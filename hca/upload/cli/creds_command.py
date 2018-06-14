from .. import get_credentials, UploadArea, UploadException
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

            area = UploadArea.from_alias(alias)
            creds = get_credentials(area.uuid)
            print("SAM: ", creds)
            print("AWS_ACCESS_KEY_ID=%s\nAWS_SECRET_ACCESS_KEY=%s\nAWS_SESSION_TOKEN=%s" % (
                creds['aws_access_key_id'], creds['aws_secret_access_key'], creds['aws_session_token']
            ))
        except UploadException as e:
            print(str(e))
            exit(1)
