import base64
import json
import os
import sys
import unittest
import uuid
from argparse import Namespace

import boto3
import tweak
from moto import mock_s3

from ... import reset_tweak_changes

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca.upload.cli.upload_command import UploadCommand
from .. import UPLOAD_BUCKET_NAME_TEMPLATE, TEST_UPLOAD_BUCKET


class TestUploadCliUploadCommand(unittest.TestCase):

    def setUp(self):
        self.stage = os.environ['DEPLOYMENT_STAGE']
        self.area_uuid = str(uuid.uuid4())
        creds = {'AWS_ACCESS_KEY_ID': 'foo', 'AWS_SECRET_ACCESS_KEY': 'bar'}
        encoded_creds = base64.b64encode(json.dumps(creds).encode('ascii')).decode('ascii')
        self.urn = "dcp:upl:aws:{}:{}:{}".format(self.stage, self.area_uuid, encoded_creds)

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
    def test_upload_with_target_filename_option(self):
        self.setup_tweak_config()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()

        UploadCommand(Namespace(file_paths=['test/bundle/sample.json'], target_filename='FOO', quiet=True))

        obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/FOO".format(self.area_uuid))
        self.assertEqual(obj.content_type, 'application/json; dcp-type=data')
        with open('test/bundle/sample.json', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @mock_s3
    @reset_tweak_changes
    def test_upload_with_dcp_type_option(self):
        self.setup_tweak_config()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()

        UploadCommand(Namespace(file_paths=['LICENSE'], target_filename=None, quiet=True))

        obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/LICENSE".format(self.area_uuid))
        self.assertEqual(obj.content_type, 'application/octet-stream; dcp-type=data')
        with open('LICENSE', 'rb') as fh:
            expected_contents = fh.read()
            self.assertEqual(obj.get()['Body'].read(), expected_contents)

    @mock_s3
    @reset_tweak_changes
    def test_multiple_uploads(self):
        self.setup_tweak_config()
        s3 = boto3.resource('s3')
        s3.Bucket(TEST_UPLOAD_BUCKET).create()

        files = ['LICENSE', 'README.rst']
        UploadCommand(Namespace(file_paths=files, target_filename=None, dcp_type=None, quiet=True))

        for filename in files:
            obj = s3.Bucket(TEST_UPLOAD_BUCKET).Object("{}/{}".format(self.area_uuid, filename))
            with open(filename, 'rb') as fh:
                expected_contents = fh.read()
                self.assertEqual(obj.get()['Body'].read(), expected_contents)
