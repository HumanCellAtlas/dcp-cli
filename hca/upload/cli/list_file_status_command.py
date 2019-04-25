import re

from hca.upload import UploadConfig

from hca.upload.cli.common import UploadCLICommand
from hca.upload.lib.upload_submission_state import FileStatusCheck


class ListFileStatusCommand(UploadCLICommand):
    """
    Print status of file in an upload area
    """
    @classmethod
    def add_parser(cls, upload_subparsers):
        list_file_statuses_parser = upload_subparsers.add_parser('status', help=cls.__doc__,
                                                                 description=cls.__doc__)
        list_file_statuses_parser.set_defaults(entry_point=ListFileStatusCommand)
        list_file_statuses_parser.add_argument('filename', help='File name')
        list_file_statuses_parser.add_argument('-env',
                                               help="Environment the upload area was created in (default is based on "
                                                    "currently selected upload area)",
                                               default=None)
        list_file_statuses_parser.add_argument('-uuid',
                                               help="Full UUID of an upload area (default is based on currently "
                                                    "selected upload area)",
                                               default=None)

    def __init__(self, args):
        area_uuid = args.uuid
        env = args.env
        config = UploadConfig()
        if not area_uuid:
            area_uuid = config.current_area
        if not env:
            area_uri = config.area_uri(area_uuid)
            env = area_uri.deployment_stage
        filename = args.filename
        status = FileStatusCheck(env).check_file_status(area_uuid, filename)
        if re.search('STATUS_RETRIEVAL_ERROR', status):
            print(status)
        else:
            print("File: {} in UploadArea: {}/{} is currently {}".format(filename, env, area_uuid, status))
