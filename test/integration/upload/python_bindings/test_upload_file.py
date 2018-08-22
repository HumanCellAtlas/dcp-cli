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
        self.area._setup_s3_agent_for_file_upload(file_paths=file_paths)
        self.assertEqual(self.area.s3agent.file_count, 1)
        self.assertEqual(self.area.s3agent.file_size_sum, 1078)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 0)
        self.assertEqual(self.area.s3agent.cumulative_bytes_transferred, 0)

    @responses.activate
    def test_s3_agent_setup_for_multiple_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE", "LICENSE"]
        self.area._setup_s3_agent_for_file_upload(file_paths=file_paths)
        self.assertEqual(self.area.s3agent.file_count, 2)
        self.assertEqual(self.area.s3agent.file_size_sum, 2156)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 0)
        self.assertEqual(self.area.s3agent.cumulative_bytes_transferred, 0)

    @responses.activate
    def test_s3_agent_stats_update_for_single_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE"]
        self.area.upload_files(file_paths=file_paths)
        self.assertEqual(self.area.s3agent.file_count, 1)
        self.assertEqual(self.area.s3agent.file_size_sum, 1078)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 1)

    @responses.activate
    def test_s3_agent_stats_update_for_multiple_file_upload(self):
        self.simulate_credentials_api(area_uuid=self.area.uuid)
        file_paths = ["LICENSE", "LICENSE"]
        self.area.upload_files(file_paths=file_paths)
        self.assertEqual(self.area.s3agent.file_count, 2)
        self.assertEqual(self.area.s3agent.file_size_sum, 2156)
        self.assertEqual(self.area.s3agent.file_upload_completed_count, 2)

if __name__ == "__main__":
    unittest.main()
