import os
import sys

import boto3

from hca.upload import UploadService
from .common import UploadCLICommand


class UploadCommand(UploadCLICommand):
    """
    Upload a file to the currently selected upload area.
    """
    COMPARISON_TOOL = "https://s3-accelerate-speedtest.s3-accelerate.amazonaws.com/en/accelerate-speed-comparsion.html"

    @classmethod
    def add_parser(cls, upload_subparsers):
        upload_parser = upload_subparsers.add_parser(
            'files',
            help=cls.__doc__,
            description=cls.__doc__
        )
        upload_parser.add_argument('upload_paths', nargs='+', metavar="<upload_path>",
                                   help="Path to files or directories to be uploaded.")
        upload_parser.add_argument('-t', '--target-filename', metavar="<filename>", default=None,
                                   help="Filename to use in upload area (if you wish to change it during upload)." +
                                   " Only valid when one file is being uploaded.")
        upload_parser.add_argument('--file-extension', metavar="<fileextension>", default=None,
                                   help="File extension to limit which files should be uploaded" +
                                   " Only valid when directories are targeted for upload.")
        upload_parser.add_argument('--no-transfer-acceleration', action='store_true',
                                   help="""Don't use Amazon S3 Transfer Acceleration.
                                           By default we using the aforementioned service to upload via an endpoint
                                           geographically close to you, instead of directly to Virginia, USA.
                                           However, in some situations this can be slower.  Use the S3 Transfer
                                           Acceleration Speed Comparison Tool to determine whether you should use
                                           this option: {url}.""".format(url=cls.COMPARISON_TOOL))
        upload_parser.add_argument('-q', '--quiet', action='store_true', help="Suppress normal output.")
        upload_parser.set_defaults(entry_point=UploadCommand)

    def __init__(self, args):
        self.source_s3_client = boto3.client('s3')
        self.file_paths = []
        self.file_size_sum = 0
        self._load_config()
        self._check_args(args)
        for upload_path in args.upload_paths:
            self._load_file_paths_from_upload_path(args, upload_path)
        config = UploadService.config()
        area_uuid = config.current_area
        area_uri = config.area_uri(area_uuid)
        upload_service = UploadService(deployment_stage=area_uri.deployment_stage)
        area = upload_service.upload_area(area_uri=area_uri)
        area.upload_files(self.file_paths,
                          self.file_size_sum,
                          target_filename=args.target_filename,
                          use_transfer_acceleration=(not args.no_transfer_acceleration),
                          report_progress=(not args.quiet),
                          dcp_type="data")

    def _load_config(self):
        self.config = UploadService.config()
        if not self.config.current_area:
            sys.stderr.write("\nThere is no upload area selected.\n" +
                             "Please select one with \"{cmdname} upload select <uri_or_alias>\"\n\n".format(
                                 cmdname=sys.argv[0]))
            exit(1)

    def _check_args(self, args):
        if args.target_filename and (len(args.upload_paths) > 1 or os.path.isdir(args.upload_paths[0])):
            print("--target-filename option may only be used when one file is being uploaded.")
            exit(1)
        if args.file_extension:
            for upload_path in args.upload_paths:
                if not os.path.isdir(upload_path):
                    print("--file-extension can only be used when paths targeted for upload are directories")
                    exit(1)

    def _load_file_paths_from_upload_path(self, args, upload_path):
        if upload_path.startswith("s3://"):
            s3_file_paths, s3_file_size_sum = self._retrieve_files_list_and_size_sum_tuple_from_s3_path(upload_path)
            self.file_paths += s3_file_paths
            self.file_size_sum += s3_file_size_sum
        elif os.path.isfile(upload_path):
            self.file_paths.append(upload_path)
            self.file_size_sum += os.path.getsize(upload_path)
        elif os.path.isdir(upload_path):
            for dir_path, sub_dir_list, file_list in os.walk(upload_path):
                for file_name in file_list:
                    if not args.file_extension or file_name.endswith(args.file_extension):
                        file_path = os.path.join(dir_path, file_name)
                        self.file_paths.append(file_path)
                        self.file_size_sum += os.path.getsize(file_path)

    def _retrieve_files_list_and_size_sum_tuple_from_s3_path(self, s3_path):
        s3_file_obj_paths = []
        s3_file_size_bytes_sum = 0
        bucket, prefix = self._parse_s3_path(s3_path)

        paginator = self.source_s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
        for page in page_iterator:
            if "Contents" in page:
                for key in page["Contents"]:
                    s3_file_size_bytes_sum += key['Size']
                    s3_obj_path = "s3://{0}/{1}".format(bucket, key['Key'])
                    s3_file_obj_paths.append(s3_obj_path)
        return s3_file_obj_paths, s3_file_size_bytes_sum

    def _parse_s3_path(self, s3_path):
        s3_path = s3_path.replace("s3://", "")
        s3_path_split = s3_path.split("/", 1)

        bucket = s3_path_split[0]
        prefix = ''
        if len(s3_path_split) > 1:
            prefix = s3_path_split[1]
        return bucket, prefix
