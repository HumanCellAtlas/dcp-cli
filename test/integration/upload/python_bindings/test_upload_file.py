#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest

import responses

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from test import TEST_DIR
from test.integration.upload import UploadTestCase
from hca.upload.s3_agent import WRITE_PERCENT_THRESHOLD


class TestUploadFileUpload(UploadTestCase):

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
    def test_s3_agent_setup_for_single_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE"]
        self.area._setup_s3_agent_for_file_upload(file_size_sum=1078, file_count=1)
        self.assertEqual(self.area.s3agent.file_count, 1)
        self.assertEqual(self.area.s3agent.file_size_sum, 1078)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 0)
        self.assertEqual(self.area.s3agent.cumulative_bytes_transferred, 0)

    @responses.activate
    def test_s3_agent_setup_for_multiple_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        self.area._setup_s3_agent_for_file_upload(file_size_sum=2156, file_count=2)
        self.assertEqual(self.area.s3agent.file_count, 2)
        self.assertEqual(self.area.s3agent.file_size_sum, 2156)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 0)
        self.assertEqual(self.area.s3agent.cumulative_bytes_transferred, 0)

    @responses.activate
    def test_s3_agent_stats_update_for_single_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE"]
        self.area.upload_files(file_paths=file_paths, file_size_sum=1078)
        self.assertEqual(self.area.s3agent.file_count, 1)
        self.assertEqual(self.area.s3agent.file_size_sum, 1078)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 1)

    @responses.activate
    def test_s3_agent_stats_update_for_multiple_file_upload(self):
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
