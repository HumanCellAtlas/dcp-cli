import unittest

from argparse import Namespace
from mock import patch
from test import CapturingIO

from hca.upload.cli import GenerateStatusReportCommand


class TestUploadCliStatusCommand(unittest.TestCase):
    @patch('hca.upload.upload_submission_state.UploadAreaFilesStatusCheck.check_file_statuses')
    def test_upload_area_is_default_output_file_name(self, mock_check_file_statuses):
        with CapturingIO('stdout') as stdout:
            upload_area ='1234'
            args = Namespace(env='dev', uuid=upload_area, output_file_name=None)
            GenerateStatusReportCommand(args)
            # upload area id used as file name if not passed in
            mock_check_file_statuses.assert_called_once_with(upload_area, upload_area)

        assert stdout.captured() == 'File status report generated, located {}.txt\n'.format(upload_area)

