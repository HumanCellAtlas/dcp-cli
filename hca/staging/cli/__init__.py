from .select_command import SelectCommand
from .list_areas_command import ListAreasCommand
from .upload_command import UploadCommand


def add_commands(subparsers):
    staging_parser = subparsers.add_parser('staging')
    staging_subparsers = staging_parser.add_subparsers()

    help_parser = staging_subparsers.add_parser('help',
                                                description="Display list of staging commands.")
    help_parser.set_defaults(func=_help)

    SelectCommand.add_parser(staging_subparsers)
    ListAreasCommand.add_parser(staging_subparsers)
    UploadCommand.add_parser(staging_subparsers)


def _help(args):
    print("""
hca staging commands:

    help     print this message
    select   select a staging area to use
    areas    list staging areas we know about
    upload   upload a file to the currently selected staging area

Use "hca staging <command> -h" to get detailed command help.
""")
