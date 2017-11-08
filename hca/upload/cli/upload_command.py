import os
import sys

from ..upload_config import UploadConfig
from .. import upload_file


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
        upload_parser.add_argument('-q', '--quiet', action='store_true', help="Suppress normal output.")
        upload_parser.set_defaults(func=UploadCommand)

    def __init__(self, args):
        self._load_config()
        self._check_args(args)
        for file_path in args.file_paths:
            self._upload_file(file_path, target_filename=args.target_filename, report_progress=(not args.quiet))

    def _upload_file(self, file_path, target_filename=None, report_progress=True):
        current_area_uuid = UploadConfig().current_area
        if report_progress:
            print("Uploading %s to upload area %s..." % (os.path.basename(file_path), current_area_uuid))
        upload_file(file_path, target_filename, report_progress=report_progress, dcp_type="data")
        if report_progress:
            print("\n")

    def _load_config(self):
        self.config = UploadConfig()
        if not self.config.current_area:
            sys.stderr.write("\nThere is not upload area selected.\n" +
                             "Please select one with \"hca upload select <urn_or_alias>\"\n\n")

    def _check_args(self, args):
        if args.target_filename and len(args.file_paths) > 1:
            print("--target-filename option may only be used when one file is being uploaded.")
            exit(1)
