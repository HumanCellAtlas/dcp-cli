import base64
import json
import os
import sys
import unittest
import uuid

import boto3
import tweak
from moto import mock_s3

from ... import reset_tweak_changes

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca import upload
from hca.upload.upload_area import UploadArea
from hca.upload.upload_area_urn import UploadAreaURN
from .. import UPLOAD_BUCKET_NAME_TEMPLATE, TEST_UPLOAD_BUCKET


class TestUploadFileUpload(unittest.TestCase):

    def setUp(self):
        self.stage = 'test'
        self.area_uuid = str(uuid.uuid4())
        creds = {'AWS_ACCESS_KEY_ID': 'foo', 'AWS_SECRET_ACCESS_KEY': 'bar'}
        encoded_creds = base64.b64encode(json.dumps(creds).encode('ascii')).decode('ascii')
        self.urn = "dcp:upl:aws:{}:{}:{}".format(self.stage, self.area_uuid, encoded_creds)
        self.area = UploadArea(urn=UploadAreaURN(self.urn))
        self.area.select()

    def setup_tweak_config(self):
        config = tweak.Config(hca.TWEAK_PROJECT_NAME)
        config.upload = {
            'areas': {self.area_uuid: self.urn},
            'current_area': self.area_uuid,
            'bucket_name_template': UPLOAD_BUCKET_NAME_TEMPLATE
        }
        config.save()

    @mock_s3
    @reset_tweak_changes
    def test_file_upload(self):
        self.setup_tweak_config()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()
        area = UploadArea(uuid=self.area_uuid)

        upload.upload_file('LICENSE')

        obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/LICENSE".format(self.area_uuid))
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @mock_s3
    @reset_tweak_changes
    def test_file_upload_with_target_filename_option(self):
        self.setup_tweak_config()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()
        area = UploadArea(uuid=self.area_uuid)

        upload.upload_file('LICENSE', target_filename='POO')

        obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/POO".format(self.area_uuid))
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)
