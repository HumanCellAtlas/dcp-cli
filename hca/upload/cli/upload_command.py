import os
import re
import sys

from ..config_store import ConfigStore
from ..upload_area_urn import UploadAreaURN
from ..s3_agent import S3Agent


class UploadCommand:

    UPLOAD_BUCKET_TEMPLATE = "org-humancellatlas-upload-%s"

    @classmethod
    def add_parser(cls, upload_subparsers):
        upload_parser = upload_subparsers.add_parser(
            'file',
            description="Upload a file to the currently selected upload area."
        )
        upload_parser.add_argument('file_paths', nargs='+', metavar="<file_path>",
                                   help="Path to file to be uploaded.")
        upload_parser.add_argument('-t', '--target-filename', metavar="<filename>", default=None,
                                   help="Filename to use in upload area (if you wish to change it during upload)." +
                                   " Only valid when one file is being uploaded.")
        upload_parser.set_defaults(func=UploadCommand)

    def __init__(self, args):
        self._load_config()
        self._check_args(args)
        self.urn = UploadAreaURN(self.config.areas()[self.config.current_area()])
        self.s3agent = S3Agent(aws_credentials=self.urn.credentials())
        for file_path in args.file_paths:
            self._upload_file(file_path, args.target_filename)

    def _upload_file(self, file_path, target_filename=None):
        file_s3_key = "%s/%s" % (self.urn.uuid, target_filename or os.path.basename(file_path))
        print("Uploading %s to upload area %s..." % (os.path.basename(file_path), file_s3_key))
        bucket_name = self.UPLOAD_BUCKET_TEMPLATE % (self.urn.deployment_stage,)
        content_type = 'application/json' if re.search('.json$', file_path) else 'hca-data-file'
        self.s3agent.upload_file(file_path, bucket_name, file_s3_key, content_type)
        print("\n")

    def _load_config(self):
        self.config = ConfigStore()
        if not self.config.current_area():
            sys.stderr.write("\nThere is not upload area selected.\n" +
                             "Please select one with \"hca upload select <urn_or_alias>\"\n\n")

    def _check_args(self, args):
        if args.target_filename and len(args.file_paths) > 1:
            print("--target-filename option may only be used when one file is being uploaded.")
            exit(1)
