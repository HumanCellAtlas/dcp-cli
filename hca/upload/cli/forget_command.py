from .. import forget_area, UploadException
from .common import UploadCLICommand


class ForgetCommand(UploadCLICommand):
    """
    Forget about upload area.
    """
    @classmethod
    def add_parser(cls, upload_subparsers):
        forget_parser = upload_subparsers.add_parser(
            'forget',
            description=cls.__doc__,
            help=cls.__doc__
        )
        forget_parser.add_argument('uuid_or_alias',
                                   help="Full or partial (alias) UUID of an upload area.")
        forget_parser.set_defaults(entry_point=ForgetCommand)

    def __init__(self, args):
        alias = args.uuid_or_alias
        try:
            area = forget_area(alias)
            print("Forgetting about area {uuid}".format(uuid=area.uuid))
        except UploadException as e:
            print(str(e))
            exit(1)
