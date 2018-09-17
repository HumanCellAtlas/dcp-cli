from hca.upload.upload_submission_state import UploadAreaFilesStatusCheck

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
        gen_file_status_report_parser.add_argument('env', help="Environment the upload area was created in")
        gen_file_status_report_parser.add_argument('uuid', help="Full UUID of an upload area.")
        gen_file_status_report_parser.add_argument('-output_file_name',
                                                   help='Name of output file (default is upload area name)',
                                                   default=None)

    def __init__(self, args):
        upload_area = args.uuid
        env = args.env
        out_put = args.output_file_name

        if not out_put:
            out_put = upload_area
        UploadAreaFilesStatusCheck(env).check_file_statuses(upload_area, out_put)
        print('File status report generated, located {}.txt'.format(out_put))
