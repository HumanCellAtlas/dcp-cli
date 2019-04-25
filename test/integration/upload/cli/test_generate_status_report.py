from argparse import Namespace
from mock import patch
from test.integration.upload import UploadTestCase

from test import CapturingIO

from hca.upload.cli import GenerateStatusReportCommand


class TestUploadCliStatusCommand(UploadTestCase):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()

    @patch('hca.upload.lib.upload_submission_state.UploadAreaFilesStatusCheck.check_file_statuses')
    def test_use_selected_area_and_env_if_none_given(self, mock_check_file_statuses):
        with CapturingIO('stdout') as stdout:
            args = Namespace(env=None, uuid=None, output_file_name=None)
            GenerateStatusReportCommand(args)
            mock_check_file_statuses.assert_called_once_with(self.area.uuid, self.area.uuid)

        assert stdout.captured() == 'File status report for {}/{} generated, located {}.txt\n'.format(
            'test', self.area.uuid, self.area.uuid)

    @patch('hca.upload.lib.upload_submission_state.UploadAreaFilesStatusCheck.check_file_statuses')
    def test_upload_area_is_default_output_file_name(self, mock_check_file_statuses):
        with CapturingIO('stdout') as stdout:
            upload_area ='1234'
            env = 'test'
            args = Namespace(env=env, uuid=upload_area, output_file_name=None)
            GenerateStatusReportCommand(args)
            # upload area id used as file name if not passed in
            mock_check_file_statuses.assert_called_once_with(upload_area, upload_area)

        assert stdout.captured() == 'File status report for {}/{} generated, located {}.txt\n'.format(
        env, upload_area, upload_area)


