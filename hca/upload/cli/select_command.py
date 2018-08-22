from ..upload_area import UploadArea, UploadException
from .common import UploadCLICommand


class SelectCommand(UploadCLICommand):
    """
    Select upload area to which you wish to upload files.
    """
    @classmethod
    def add_parser(cls, upload_subparsers):
        select_parser = upload_subparsers.add_parser(
            'select',
            help=cls.__doc__,
            description=cls.__doc__
        )
        select_parser.add_argument('uri_or_alias',
                                   help="S3 URI of an upload area, or short alias.")
        select_parser.set_defaults(entry_point=SelectCommand)

    def __init__(self, args):
        if args.uri_or_alias.startswith('s3://'):  # URI
            self._save_and_select_area_by_uri(args.uri_or_alias)
        else:  # alias
            self._select_area_by_alias(args.uri_or_alias)

    def _save_and_select_area_by_uri(self, uri_string):
        area = UploadArea(uri=uri_string)
        area.select()
        print("Upload area %s selected." % area.uuid)
        print("In future you may refer to this upload area using the alias \"%s\"" % area.unique_prefix)

    def _select_area_by_alias(self, alias):
        try:
            area = UploadArea.from_alias(alias)
            area.select()
        except UploadException as e:
            print(str(e))
