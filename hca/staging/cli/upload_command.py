import os
import re
import sys

import boto3
from boto3.s3.transfer import TransferConfig

from .config_store import ConfigStore
from .staging_area_urn import StagingAreaURN

KB = 1024
MB = KB * KB


def sizeof_fmt(num, suffix='B'):
    """
    From https://stackoverflow.com/a/1094933
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%d %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


class S3Agent:

    CLEAR_TO_EOL = "\x1b[0K"

    def __init__(self, aws_credentials={}):
        session = boto3.session.Session(**aws_credentials)
        self.s3 = session.resource('s3')

    def upload_progress_callback(self, bytes_transferred):
        self.cumulative_bytes_transferred += bytes_transferred
        percent_complete = (self.cumulative_bytes_transferred * 100) / self.file_size
        sys.stdout.write("\r%s of %s transferred (%.0f%%)%s" %
                         (sizeof_fmt(self.cumulative_bytes_transferred),
                          sizeof_fmt(self.file_size),
                          percent_complete,
                          self.CLEAR_TO_EOL))
        sys.stdout.flush()

    def upload_file(self, local_path, target_bucket, target_key, content_type):
        self.file_size = os.stat(local_path).st_size
        bucket = self.s3.Bucket(target_bucket)
        obj = bucket.Object(target_key)
        with open(local_path, 'rb') as fh:
            self.cumulative_bytes_transferred = 0
            obj.upload_fileobj(fh,
                               ExtraArgs={'ContentType': content_type,
                                          'ACL': 'bucket-owner-full-control'},
                               Callback=self.upload_progress_callback,
                               Config=self.transfer_config(self.file_size)
                               )

    @classmethod
    def transfer_config(cls, file_size):
        etag_stride = cls._s3_chunk_size(file_size)
        return TransferConfig(multipart_threshold=etag_stride,
                              multipart_chunksize=etag_stride)

    @staticmethod
    def _s3_chunk_size(file_size):
        if file_size <= 10000 * 64 * MB:
            return 64 * MB
        else:
            div = file_size // 10000
            if div * 10000 < file_size:
                div += 1
            return ((div + (MB - 1)) // MB) * MB


class UploadCommand:

    STAGING_BUCKET_TEMPLATE = "org-humancellatlas-staging-%s"

    @classmethod
    def add_parser(cls, staging_subparsers):
        upload_parser = staging_subparsers.add_parser(
            'upload',
            description="Upload a file to the currently selected staging area."
        )
        upload_parser.add_argument('file_paths', nargs='+', metavar="<file_path>",
                                   help="Path to file to be uploaded.")
        upload_parser.add_argument('-t', '--target-filename', metavar="<filename>", default=None,
                                   help="Filename to use in staging bucket (if you wish to change it during upload)." +
                                   " Only valid when one file is being uploaded.")
        upload_parser.set_defaults(func=UploadCommand)

    def __init__(self, args):
        self._load_config()
        self._check_args(args)
        self.urn = StagingAreaURN(self.config.areas()[self.config.current_area()])
        self.s3agent = S3Agent(aws_credentials=self.urn.credentials())
        for file_path in args.file_paths:
            self._stage_file(file_path, args.target_filename)

    def _stage_file(self, file_path, target_filename=None):
        file_s3_key = "%s/%s" % (self.urn.uuid, target_filename or os.path.basename(file_path))
        print("Uploading %s to staging area %s..." % (os.path.basename(file_path), file_s3_key))
        bucket_name = self.STAGING_BUCKET_TEMPLATE % (self.urn.deployment_stage,)
        content_type = 'application/json' if re.search('.json$', file_path) else 'hca-data-file'
        self.s3agent.upload_file(file_path, bucket_name, file_s3_key, content_type)
        print("\n")

    def _load_config(self):
        self.config = ConfigStore()
        if not self.config.current_area():
            sys.stderr.write("\nThere is not staging area selected.\n" +
                             "Please select one with \"hca staging select <urn_or_alias>\"\n\n")

    def _check_args(self, args):
        if args.target_filename and len(args.file_paths) > 1:
            print("--target-filename option may only be used when one file is being uploaded.")
            exit(1)
