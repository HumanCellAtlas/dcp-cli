from .select_command import SelectCommand
from .list_areas_command import ListAreasCommand
from .list_area_command import ListAreaCommand
from .upload_command import UploadCommand
from .forget_command import ForgetCommand


def add_commands(subparsers):
    upload_parser = subparsers.add_parser('upload')
    upload_subparsers = upload_parser.add_subparsers()

    help_parser = upload_subparsers.add_parser('help',
                                               description="Display list of upload commands.")
    help_parser.set_defaults(func=_help)

    SelectCommand.add_parser(upload_subparsers)
    UploadCommand.add_parser(upload_subparsers)
    ListAreaCommand.add_parser(upload_subparsers)
    ListAreasCommand.add_parser(upload_subparsers)
    ForgetCommand.add_parser(upload_subparsers)


def _help(args):
    print("""
hca upload commands:

    help     print this message
    select   select an upload area to use
    forget   forget about an upload area
    file     upload a file to the currently selected upload area
    list     list contents of currently selected upload area
    areas    list upload areas we know about

Use "hca upload <command> -h" to get detailed command help.
""")
