import os
import sys

import boto3

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca import upload
from .. import UploadTestCase, TEST_UPLOAD_BUCKET, mock_current_upload_area


class TestUploadFileUpload(UploadTestCase):

    def test_file_upload(self):
        area = mock_current_upload_area()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()

        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'bundle', 'assay.json')
        upload.upload_file(file_path)

        obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/assay.json".format(area.uuid))
        self.assertEqual(obj.content_type, 'application/json; dcp-type=data')
        with open(file_path, 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    def test_file_upload_with_target_filename_option(self):
        area = mock_current_upload_area()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()

        upload.upload_file('LICENSE', target_filename='POO')

        obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/POO".format(area.uuid))
        self.assertEqual(obj.content_type, 'application/octet-stream; dcp-type=data')
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)
