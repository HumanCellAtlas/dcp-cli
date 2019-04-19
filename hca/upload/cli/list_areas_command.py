import sys

from ..upload_config import UploadConfig
from .common import UploadCLICommand


class ListAreasCommand(UploadCLICommand):
    """
    List upload areas I know about.
    """
    @classmethod
    def add_parser(cls, upload_subparsers):
        list_areas_parser = upload_subparsers.add_parser('areas',
                                                         help=cls.__doc__,
                                                         description=cls.__doc__)
        list_areas_parser.set_defaults(entry_point=ListAreasCommand)

    def __init__(self, args):
        for uuid in UploadConfig().areas:
            sys.stdout.write(uuid)
            if uuid == UploadConfig().current_area:
                sys.stdout.write(" <- selected")
            sys.stdout.write("\n")
