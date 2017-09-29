from .select_command import SelectCommand
from .list_areas_command import ListAreasCommand


def add_commands(subparsers):
    staging_parser = subparsers.add_parser('staging')
    staging_subparsers = staging_parser.add_subparsers()

    SelectCommand.add_parser(staging_subparsers)
    ListAreasCommand.add_parser(staging_subparsers)
