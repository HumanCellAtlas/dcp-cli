import os
import sys
import unittest

import boto3
from moto import mock_s3
import responses

from ... import reset_tweak_changes

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca import upload
from .. import mock_current_upload_area


class TestUploadListArea(unittest.TestCase):

    def setUp(self):
        self.s3_mock = mock_s3()
        self.s3_mock.start()

        self.deployment_stage = 'test'
        self.upload_bucket_name = 'org-humancellatlas-upload-{}'.format(self.deployment_stage)
        self.upload_bucket = boto3.resource('s3').Bucket(self.upload_bucket_name)
        self.upload_bucket.create()

    def tearDown(self):
        self.s3_mock.stop()

    @reset_tweak_changes
    def test_list_current_area(self):
        area = mock_current_upload_area()
        self.upload_bucket.Object('/'.join([area.uuid, 'bogofile'])).put(Body="foo")

        file_list = list(upload.list_current_area())

        self.assertEqual(file_list, [{'name': 'bogofile'}])

    @reset_tweak_changes
    @responses.activate
    def test_list_current_area_with_detail(self):
        area = mock_current_upload_area()
        self.upload_bucket.Object('/'.join([area.uuid, 'bogofile'])).put(Body="foo")

        list_url = 'https://upload.{stage}.data.humancellatlas.org/v1/area/{uuid}/files_info'.format(
            stage=self.deployment_stage,
            uuid=area.uuid)
        responses.add(responses.PUT, list_url, json=[{"name": "bogofile", "size": 1234}], status=200)

        file_list = list(upload.list_current_area(detail=True))

        self.assertEqual(file_list, [{'name': 'bogofile', 'size': 1234}])
