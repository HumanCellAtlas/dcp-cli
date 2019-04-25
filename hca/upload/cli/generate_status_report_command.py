from hca.upload import UploadConfig

from hca.upload.lib.upload_submission_state import UploadAreaFilesStatusCheck

from hca.upload.cli.common import UploadCLICommand


class GenerateStatusReportCommand(UploadCLICommand):
    """
    Generate file status report for upload area
    """
    @classmethod
    def add_parser(cls, upload_subparsers):
        gen_file_status_report_parser = upload_subparsers.add_parser('report', help=cls.__doc__,
                                                                     description=cls.__doc__)
        gen_file_status_report_parser.set_defaults(entry_point=GenerateStatusReportCommand)
        gen_file_status_report_parser.add_argument('-env',
                                                   help="Environment the upload area was created in (default is based "
                                                        "on currently selected upload area)",
                                                   default=None)
        gen_file_status_report_parser.add_argument('-uuid',
                                                   help="Full UUID of an upload area (default is based on currently "
                                                        "selected upload area)",
                                                   default=None)
        gen_file_status_report_parser.add_argument('-output_file_name',
                                                   help='Name of output file (default is upload area name)',
                                                   default=None)

    def __init__(self, args):
        area_uuid = args.uuid
        env = args.env
        out_put = args.output_file_name
        config = UploadConfig()
        if not area_uuid:
            area_uuid = config.current_area
        if not env:
            area_uri = config.area_uri(area_uuid)
            env = area_uri.deployment_stage
        if not out_put:
            out_put = area_uuid
        UploadAreaFilesStatusCheck(env).check_file_statuses(area_uuid, out_put)
        print('File status report for {}/{} generated, located {}.txt'.format(env, area_uuid, out_put))
