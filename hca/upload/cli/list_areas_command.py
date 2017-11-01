import sys

from ..upload_area import UploadArea


class ListAreasCommand:

    @classmethod
    def add_parser(cls, upload_subparsers):
        list_areas_parser = upload_subparsers.add_parser('areas',
                                                         description="List upload areas I know about.")
        list_areas_parser.set_defaults(func=ListAreasCommand)

    def __init__(self, args):
        for area in UploadArea.all():
            sys.stdout.write(area.uuid)
            if area.is_selected:
                sys.stdout.write(" <- selected")
            sys.stdout.write("\n")
