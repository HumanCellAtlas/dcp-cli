import sys

from .config_store import ConfigStore


class ListAreasCommand:

    @classmethod
    def add_parser(cls, staging_subparsers):
        list_areas_parser = staging_subparsers.add_parser('areas',
                                                          description="List staging areas I know about.")
        list_areas_parser.set_defaults(func=ListAreasCommand)

    def __init__(self, args):
        config = ConfigStore()
        for uuid in config.areas():
            sys.stdout.write(uuid)
            if config.current_area() == uuid:
                sys.stdout.write(" <- selected")
            sys.stdout.write("\n")
