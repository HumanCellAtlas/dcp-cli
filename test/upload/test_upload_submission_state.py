import filecmp
import os
import unittest
from mock import patch
from hca.upload.upload_submission_state import FileStatusCheck, UploadAreaFilesStatusCheck


class TestFileStatusCheck(unittest.TestCase):
    def setUp(self):
        self.checksummed_response_body = {
            "checksum_status": "CHECKSUMMED",
            "checksums": {
                "crc32c": "string",
                "s3_etag": "string",
                "sha1": "string",
                "sha256": "string"
              }
        }
        self.checksum_scheduled_response_body = {
            "checksum_status": "SCHEDULED",
            "checksums": {
                "crc32c": "string",
                "s3_etag": "string",
                "sha1": "string",
                "sha256": "string"
              }
        }
        self.validated_response_body = {
            'validation_results':
                '{"validation_state": "VALID",'
                '"validation_errors": []'
                '}\n',
            'validation_status': 'VALIDATED'
        }
        self.validation_scheduled_response_body = {
            'validation_results':
                '{"validation_state": "VALID",'
                '"validation_errors": []'
                '}\n',
            'validation_status': 'SCHEDULED'
        }
        self.file_status = FileStatusCheck('dev')


    @patch('hca.upload.api_client.ApiClient.checksum_status')
    @patch('hca.upload.api_client.ApiClient.validation_status')
    def test_validated_file_status(self, mock_validation_status, mock_checksum_status):
        mock_validation_status.return_value = self.validated_response_body
        mock_checksum_status.return_value = self.checksummed_response_body
        valid_file = self.file_status.check_file_status('uuid', 'filename')
        assert valid_file == 'VALIDATED'

    @patch('hca.upload.api_client.ApiClient.checksum_status')
    def test_checksumming_scheduled_file_status(self, mock_checksum_status):
        mock_checksum_status.return_value = self.checksum_scheduled_response_body
        checksum_scheduled = self.file_status.check_file_status('uuid', 'filename')
        assert checksum_scheduled == 'CHECKSUMMING_SCHEDULED'

    @patch('hca.upload.api_client.ApiClient.checksum_status')
    @patch('hca.upload.api_client.ApiClient.validation_status')
    def test_validation_scheduled_file_status(self, mock_validation_status, mock_checksum_status):
        mock_validation_status.return_value = self.validation_scheduled_response_body
        mock_checksum_status.return_value = self.checksummed_response_body
        valid_file = self.file_status.check_file_status('uuid', 'filename')
        assert valid_file == 'VALIDATION_SCHEDULED'




class TestUploadAreaStatusCheck(unittest.TestCase):
    def setUp(self):
        self.checksums_response_body = {
            "CHECKSUMMED": 98,
            "CHECKSUMMING": 1,
            "CHECKSUMMING_UNSCHEDULED": 1,
            "TOTAL_NUM_FILES": 100
        }
        self.validations_response_body = {
            "SCHEDULED": 2,
            "VALIDATED": 90,
            "VALIDATING": 5
        }
        self.upload_area_status_checker = UploadAreaFilesStatusCheck('dev')

    @classmethod
    def tearDownClass(clsr):
        os.remove('test_status_report.txt')

    @patch('hca.upload.api_client.ApiClient.checksum_statuses')
    @patch('hca.upload.api_client.ApiClient.validation_statuses')
    def test_get_file_statuses_correctly_sets_number_unscheduled_for_validation(self, mock_validation_statuses,
                                                                                mock_checksum_statuses):
        mock_validation_statuses.return_value = self.validations_response_body
        mock_checksum_statuses.return_value = self.checksums_response_body

        checksum_statuses, validations_statuses = self.upload_area_status_checker.get_file_statuses('upload_area_uuid')
        assert checksum_statuses == self.checksums_response_body
        assert validations_statuses['VALIDATION_UNSCHEDULED'] == 1

    @patch('hca.upload.api_client.ApiClient.checksum_statuses')
    @patch('hca.upload.api_client.ApiClient.validation_statuses')
    def test_report_generated_correctly(self, mock_validation_statuses, mock_checksum_statuses):
        mock_validation_statuses.return_value = self.validations_response_body
        mock_checksum_statuses.return_value = self.checksums_response_body

        self.upload_area_status_checker.check_file_statuses('upload_area_id', 'test_status_report')
        assert filecmp.cmp('test_status_report.txt', 'data/mock_upload_area_status_report.txt')

if __name__ == "__main__":
    unittest.main()
