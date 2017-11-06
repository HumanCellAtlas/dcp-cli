from ..upload_area_urn import UploadAreaURN
from ..upload_area import UploadArea


class SelectCommand:

    @classmethod
    def add_parser(cls, upload_subparsers):
        select_parser = upload_subparsers.add_parser(
            'select',
            description="Select upload area to which you wish to upload files."
        )
        select_parser.add_argument('urn_or_alias',
                                   help="Full URN of an upload area, or short alias.")
        select_parser.set_defaults(func=SelectCommand)

    def __init__(self, args):
        if args.urn_or_alias.find(':') == -1:  # alias
            self._select_area_by_alias(args.urn_or_alias)
        else:  # URN
            self._save_and_select_area_by_urn(args.urn_or_alias)

    def _save_and_select_area_by_urn(self, urn_string):
        area = UploadArea(urn=UploadAreaURN(urn_string))
        area.select()
        print("Upload area %s selected." % area.uuid)
        print("In future you may refer to this upload area using the alias \"%s\"" % area.unique_prefix)

    def _select_area_by_alias(self, alias):
        matching_areas = UploadArea.areas_matching_alias(alias)
        if len(matching_areas) == 0:
            print("Sorry I don't recognize area \"%s\"" % (alias,))
        elif len(matching_areas) == 1:
            matching_areas[0].select()
            print("Upload area %s selected." % matching_areas[0].uuid)
        else:
            print("\"%s\" matches more than one area, please provide more characters." % (alias,))
