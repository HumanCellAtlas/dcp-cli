from .generate_status_report_command import GenerateStatusReportCommand

from .list_file_status_command import ListFileStatusCommand
from .select_command import SelectCommand
from .list_areas_command import ListAreasCommand
from .list_area_command import ListAreaCommand
from .upload_command import UploadCommand
from .forget_command import ForgetCommand
from .creds_command import CredsCommand
from .common import UploadCLICommand


def add_commands(subparsers):
    upload_parser = subparsers.add_parser('upload', help="Upload data to DCP")
    upload_subparsers = upload_parser.add_subparsers()

    help_parser = upload_subparsers.add_parser('help',
                                               description="Display list of upload commands.")

    def _help(args):
        upload_parser.print_help()

    upload_parser.set_defaults(entry_point=_help)
    help_parser.set_defaults(entry_point=_help)
    SelectCommand.add_parser(upload_subparsers)
    UploadCommand.add_parser(upload_subparsers)
    ListAreaCommand.add_parser(upload_subparsers)
    ListAreasCommand.add_parser(upload_subparsers)
    ForgetCommand.add_parser(upload_subparsers)
    CredsCommand.add_parser(upload_subparsers)
    ListFileStatusCommand.add_parser(upload_subparsers)
    GenerateStatusReportCommand.add_parser(upload_subparsers)
