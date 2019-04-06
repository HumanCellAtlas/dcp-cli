from argparse import Namespace

from test.integration.upload import UploadTestCase

from mock import patch

from hca.upload.cli import ListFileStatusCommand
from test import CapturingIO


class TestUploadCliStatusCommand(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()

    @patch('hca.upload.lib.upload_submission_state.FileStatusCheck.get_checksum_status')
    def test_use_selected_area_and_env_if_none_given(self, mock_get_checksum_status):
        mock_return_value = 'CHECKSUMMING'
        mock_get_checksum_status.return_value = mock_return_value
        filename = 'existing_file'

        with CapturingIO('stdout') as stdout:
            args = Namespace(env=None, uuid=None, filename=filename)
            ListFileStatusCommand(args)

        assert stdout.captured() == "File: {} in UploadArea: {}/{} is currently {}\n".format(
            filename, 'test', self.area.uuid, mock_return_value)

    @patch('hca.upload.lib.upload_submission_state.FileStatusCheck.get_checksum_status')
    def test_prints_file_status(self, mock_get_checksum_status):
        mock_return_value = 'CHECKSUMMING'
        filename = 'existing_file'
        upload_area = '1234'
        env = 'test'
        mock_get_checksum_status.return_value = mock_return_value
        with CapturingIO('stdout') as stdout:
            args = Namespace(env=env, uuid=upload_area, filename=filename)
            ListFileStatusCommand(args)

        assert stdout.captured() == "File: {} in UploadArea: {}/{} is currently {}\n".format(
            filename, env, upload_area, mock_return_value)

    @patch('hca.upload.lib.upload_submission_state.FileStatusCheck.get_checksum_status')
    def test_correctly_handles_missing_file(self, mock_get_checksum_status):
        mock_return_value = 'CHECKSUM_STATUS_RETRIEVAL_ERROR: GET https://upload...website/checksum returned 404'
        mock_get_checksum_status.return_value = mock_return_value
        with CapturingIO('stdout') as stdout:
            args = Namespace(env='dev', uuid='1234', filename='missing_file')
            ListFileStatusCommand(args)

        assert stdout.captured() == mock_return_value + "\n"

