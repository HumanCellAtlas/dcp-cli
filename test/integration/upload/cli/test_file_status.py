import unittest
from argparse import Namespace

from mock import patch

from hca.upload.cli import ListFileStatusCommand
from test import CapturingIO


class TestUploadCliStatusCommand(unittest.TestCase):
    @patch('hca.upload.upload_submission_state.FileStatusCheck.get_checksum_status')
    def test_prints_file_status(self, mock_get_checksum_status):
        mock_return_value = 'CHECKSUMMING'
        filename = 'existing_file'
        upload_area = '1234'
        mock_get_checksum_status.return_value = mock_return_value
        with CapturingIO('stdout') as stdout:
            args = Namespace(env='dev', uuid=upload_area, filename=filename)
            ListFileStatusCommand(args)

        assert stdout.captured() == "File: {} in UploadArea: {} is currently {}\n".format(filename, upload_area, mock_return_value)

    @patch('hca.upload.upload_submission_state.FileStatusCheck.get_checksum_status')
    def test_correctly_handles_missing_file(self, mock_get_checksum_status):
        mock_return_value = 'CHECKSUM_STATUS_RETRIEVAL_ERROR: GET https://upload...website/checksum returned 404'
        mock_get_checksum_status.return_value = mock_return_value
        with CapturingIO('stdout') as stdout:
            args = Namespace(env='dev', uuid='1234', filename='missing_file')
            ListFileStatusCommand(args)

        assert stdout.captured() == mock_return_value + "\n"

