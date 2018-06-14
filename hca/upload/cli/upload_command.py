import os
import sys

from ..upload_config import UploadConfig
from .. import upload_file
from .common import UploadCLICommand


class UploadCommand(UploadCLICommand):
    """
    Upload a file to the currently selected upload area.
    """
    COMPARISON_TOOL = "https://s3-accelerate-speedtest.s3-accelerate.amazonaws.com/en/accelerate-speed-comparsion.html"

    @classmethod
    def add_parser(cls, upload_subparsers):
        upload_parser = upload_subparsers.add_parser(
            'file',
            help=cls.__doc__,
            description=cls.__doc__
        )
        upload_parser.add_argument('file_paths', nargs='+', metavar="<file_path>",
                                   help="Path to file to be uploaded.")
        upload_parser.add_argument('-t', '--target-filename', metavar="<filename>", default=None,
                                   help="Filename to use in upload area (if you wish to change it during upload)." +
                                   " Only valid when one file is being uploaded.")
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
        self._load_config()
        self._check_args(args)
        for file_path in args.file_paths:
            self._upload_file(file_path,
                              target_filename=args.target_filename,
                              use_transfer_acceleration=(not args.no_transfer_acceleration),
                              report_progress=(not args.quiet))

    def _upload_file(self, file_path, target_filename=None, use_transfer_acceleration=True, report_progress=True):
        current_area_uuid = UploadConfig().current_area
        if report_progress:
            print("Uploading %s to upload area %s..." % (os.path.basename(file_path), current_area_uuid))
        upload_file(file_path, target_filename, use_transfer_acceleration=use_transfer_acceleration,
                    report_progress=report_progress, dcp_type="data")
        if report_progress:
            print("\n")

    def _load_config(self):
        self.config = UploadConfig()
        if not self.config.current_area:
            sys.stderr.write("\nThere is no upload area selected.\n" +
                             "Please select one with \"{cmdname} upload select <uri_or_alias>\"\n\n".format(
                                 cmdname=sys.argv[0]))
            exit(1)

    def _check_args(self, args):
        if args.target_filename and len(args.file_paths) > 1:
            print("--target-filename option may only be used when one file is being uploaded.")
            exit(1)
