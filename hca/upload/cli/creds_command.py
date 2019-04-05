from .. import get_credentials, UploadException, UploadConfig
from .common import UploadCLICommand


class CredsCommand(UploadCLICommand):
    """
    Get/show AWS credentials for access to Upload Area
    """
    @classmethod
    def add_parser(cls, upload_subparsers):
        forget_parser = upload_subparsers.add_parser(
            'creds',
            description=cls.__doc__,
            help=cls.__doc__
        )
        forget_parser.add_argument('uuid_or_alias',
                                   help="Full or partial (alias) UUID of an upload area.")
        forget_parser.set_defaults(entry_point=CredsCommand)

    def __init__(self, args):
        alias = args.uuid_or_alias
        try:
            area_uuid = UploadConfig().area_uuid_from_partial_uuid(partial_uuid=alias)
            creds = get_credentials(area_uuid)
            for k, v in creds.items():
                print("{key}={value}".format(key=k, value=v))

        except UploadException as e:
            print(str(e))
            exit(1)
