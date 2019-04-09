#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest
import uuid
from mock import Mock, patch

import responses

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from test import TEST_DIR
from test.integration.upload import UploadTestCase
from hca.upload.lib.s3_agent import WRITE_PERCENT_THRESHOLD
from hca.upload import UploadAreaURI, UploadService


class TestUploadArea(UploadTestCase):

    def _create_upload_area(self):
        upload = UploadService(deployment_stage=self.deployment_stage)
        area_uuid = str(uuid.uuid4())
        area_uri = UploadAreaURI(self._make_area_uri(area_uuid=area_uuid))
        return upload.upload_area(area_uri=area_uri)

    def test_get_credentials(self):

        area = self.mock_current_upload_area()
        creds_url = self.simulate_credentials_api(area_uuid=area.uuid)

        creds = area.get_credentials()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, creds_url)
        self.assertIn('aws_access_key_id', creds)
        self.assertIn('aws_secret_access_key', creds)
        self.assertIn('aws_session_token', creds)
        self.assertIn('expiry_time', creds)

    def test_delete(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            mock_delete_area = Mock(return_value=True)
            mock_api_client = Mock(delete_area=mock_delete_area)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()
            area.delete()

            mock_delete_area.assert_called_once_with(area_uuid=area.uuid)

    def test_exists(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            mock_area_exists = Mock(return_value=False)
            mock_api_client = Mock(area_exists=mock_area_exists)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()
            result = area.exists()

            mock_area_exists.assert_called_once_with(area_uuid=area.uuid)
            self.assertFalse(result)

    def test_validate_files(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            validation_id = "validation234"
            mock_validate_files_method = Mock(return_value=validation_id)
            mock_api_client = Mock(validate_files=mock_validate_files_method)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()
            docker_img = "bogo_image"
            orig_val_id = "validation123"
            files = ['file1', 'file2']
            env = {'KEY': 'someval'}

            result = area.validate_files(file_list=files, validator_image=docker_img,
                                         original_validation_id=orig_val_id, environment=env)

            mock_validate_files_method.assert_called_once_with(area_uuid=area.uuid,
                                                               file_list=files,
                                                               validator_image=docker_img,
                                                               original_validation_id=orig_val_id,
                                                               environment=env)
            self.assertEqual(validation_id, result)

    def test_store_file(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            file_info = {'files': 'info'}
            mock_store_file_method = Mock(return_value=file_info)
            mock_api_client = Mock(store_file=mock_store_file_method)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()
            filename = "bogofile"
            content = "bogobogobogo"
            content_type = "application/bogo"

            result = area.store_file(filename=filename, file_content=content, content_type=content_type)

            mock_store_file_method.assert_called_once_with(area_uuid=area.uuid,
                                                           filename=filename,
                                                           file_content=content,
                                                           content_type=content_type)
            self.assertEqual(file_info, result)

    def test_checksum_status(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            checksum_status = {'checksum': 'status'}
            mock_checksum_status_method = Mock(return_value=checksum_status)
            mock_api_client = Mock(checksum_status=mock_checksum_status_method)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()
            filename = "bogofile"

            result = area.checksum_status(filename=filename)

            mock_checksum_status_method.assert_called_once_with(area_uuid=area.uuid,
                                                                filename=filename)
            self.assertEqual(checksum_status, result)

    def test_validation_status(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            validation_status = {'validation': 'status'}
            mock_validation_status_method = Mock(return_value=validation_status)
            mock_api_client = Mock(validation_status=mock_validation_status_method)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()
            filename = "bogofile"

            result = area.validation_status(filename=filename)

            mock_validation_status_method.assert_called_once_with(area_uuid=area.uuid,
                                                                  filename=filename)
            self.assertEqual(validation_status, result)

    def test_checksum_statuses(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            checksum_statuses = {'checksum': 'statuses'}
            mock_checksum_statuses_method = Mock(return_value=checksum_statuses)
            mock_api_client = Mock(checksum_statuses=mock_checksum_statuses_method)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()

            result = area.checksum_statuses()

            mock_checksum_statuses_method.assert_called_once_with(area_uuid=area.uuid)
            self.assertEqual(checksum_statuses, result)

    def test_validation_statuses(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            validation_statuses = {'validation': 'statuses'}
            mock_validation_statuses_method = Mock(return_value=validation_statuses)
            mock_api_client = Mock(validation_statuses=mock_validation_statuses_method)
            mock_api_client_class.return_value = mock_api_client

            area = self._create_upload_area()

            result = area.validation_statuses()

            mock_validation_statuses_method.assert_called_once_with(area_uuid=area.uuid)
            self.assertEqual(validation_statuses, result)


class TestUploadAreaFileUpload(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()

    @responses.activate
    def test_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)

        file_path = os.path.join(TEST_DIR, "res", "bundle", "assay.json")
        self.area.upload_files(file_paths=[file_path])

        obj = self.upload_bucket.Object("{}/assay.json".format(self.area.uuid))
        self.assertEqual(obj.content_type, 'application/json; dcp-type=data')
        with open(file_path, 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @responses.activate
    def test_file_upload_with_target_filename_option(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)

        self.area.upload_files(file_paths=["LICENSE"], target_filename='POO')

        obj = self.upload_bucket.Object("{}/POO".format(self.area.uuid))
        self.assertEqual(obj.content_type, 'application/octet-stream; dcp-type=data')
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @responses.activate
    def test_s3_agent_setup_for_file_upload__for_a_single_file(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)

        self.area._setup_s3_agent_for_file_upload(file_size_sum=1078, file_count=1)

        self.assertEqual(self.area.s3agent.file_count, 1)
        self.assertEqual(self.area.s3agent.file_size_sum, 1078)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 0)
        self.assertEqual(self.area.s3agent.cumulative_bytes_transferred, 0)

    @responses.activate
    def test_s3_agent_setup_for_file_upload__for_multiple_files(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)

        self.area._setup_s3_agent_for_file_upload(file_size_sum=2156, file_count=2)

        self.assertEqual(self.area.s3agent.file_count, 2)
        self.assertEqual(self.area.s3agent.file_size_sum, 2156)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 0)
        self.assertEqual(self.area.s3agent.cumulative_bytes_transferred, 0)

    @responses.activate
    def test_test_s3_agent_setup_for_file_upload__for_single_file__computes_stats_correctly(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE"]

        self.area.upload_files(file_paths=file_paths, file_size_sum=1078)

        self.assertEqual(self.area.s3agent.file_count, 1)
        self.assertEqual(self.area.s3agent.file_size_sum, 1078)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 1)

    @responses.activate
    def test_test_s3_agent_setup_for_file_upload__for_multiple_files__computes_stats_correctly(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE", "LICENSE"]

        self.area.upload_files(file_paths=file_paths, file_size_sum=2156)

        self.assertEqual(self.area.s3agent.file_count, 2)
        self.assertEqual(self.area.s3agent.file_size_sum, 2156)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 2)

    @responses.activate
    def test_s3_agent_should_write_to_terminal(self):
        self.area._setup_s3_agent_for_file_upload(file_size_sum=2156, file_count=2)
        below_threshold_bytes = WRITE_PERCENT_THRESHOLD / 100.0 * self.area.s3agent.file_size_sum / 2
        above_threshold_bytes = WRITE_PERCENT_THRESHOLD / 100.0 * self.area.s3agent.file_size_sum * 2
        self.assertEqual(self.area.s3agent.file_size_sum, 2156)

        self.area.s3agent.cumulative_bytes_transferred = below_threshold_bytes
        write_to_terminal = self.area.s3agent.should_write_to_terminal()
        self.assertEqual(write_to_terminal, False)

        self.area.s3agent.cumulative_bytes_transferred = above_threshold_bytes
        write_to_terminal = self.area.s3agent.should_write_to_terminal()
        self.assertEqual(write_to_terminal, True)

    @responses.activate
    def test_determine_s3_file_content_type(self):
        content_type_one = self.area._determine_s3_file_content_type("s3://bucket/file.json")
        content_type_two = self.area._determine_s3_file_content_type("s3://bucket/file.fastq.gz")
        content_type_three = self.area._determine_s3_file_content_type("s3://bucket/file.pdf")

        self.assertEqual(content_type_one, "application/json; dcp-type=data")
        self.assertEqual(content_type_two, "application/gzip; dcp-type=data")
        self.assertEqual(content_type_three, "application/pdf; dcp-type=data")


if __name__ == "__main__":
    unittest.main()
