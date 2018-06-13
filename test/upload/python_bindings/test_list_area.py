import os
import sys

import boto3
import responses

from ... import reset_tweak_changes

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca import upload
from .. import UploadTestCase, mock_current_upload_area


class TestUploadListArea(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.deployment_stage = 'test'
        self.upload_bucket_name = 'org-humancellatlas-upload-{}'.format(self.deployment_stage)
        self.upload_bucket = boto3.resource('s3').Bucket(self.upload_bucket_name)
        self.upload_bucket.create()

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
