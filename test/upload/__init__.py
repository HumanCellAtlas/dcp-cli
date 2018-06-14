import base64
import json
import uuid
import unittest

import boto3
from moto import mock_s3

from .. import TweakResetter

import hca
from hca.upload import UploadArea, UploadAreaURN


class UploadTestCase(unittest.TestCase):

    UPLOAD_BUCKET_NAME_TEMPLATE = 'bogo-bucket-{deployment_stage}'

    def setUp(self):
        # Setup mock AWS
        self.s3_mock = mock_s3()
        self.s3_mock.start()
        # Don't crush Tweak config
        self.tweak_resetter = TweakResetter()
        self.tweak_resetter.save_config()
        # Clean config
        self._setup_tweak_config()
        # Upload bucket
        self.deployment_stage = 'test'
        self.upload_bucket_name = self.UPLOAD_BUCKET_NAME_TEMPLATE.format(deployment_stage=self.deployment_stage)
        self.upload_bucket = boto3.resource('s3').Bucket(self.upload_bucket_name)
        self.upload_bucket.create()

    def tearDown(self):
        self.s3_mock.stop()
        self.tweak_resetter.restore_config()

    def mock_current_upload_area(self):
        area = self.mock_upload_area()
        area.select()
        return area

    def mock_upload_area(self, area_uuid=None):
        """
        Create a UUID and URN for a fake upload area, store it in Tweak config.
        """
        if not area_uuid:
            area_uuid = str(uuid.uuid4())
        creds = {'AWS_ACCESS_KEY_ID': 'foo', 'AWS_SECRET_ACCESS_KEY': 'bar'}
        encoded_creds = base64.b64encode(json.dumps(creds).encode('ascii')).decode('ascii')
        urn = "dcp:upl:aws:{}:{}:{}".format(self.deployment_stage, area_uuid, encoded_creds)
        area = UploadArea(urn=UploadAreaURN(urn))
        return area

    def _setup_tweak_config(self):
        config = hca.get_config()
        config.upload = {
            'areas': {},
            'bucket_name_template': self.UPLOAD_BUCKET_NAME_TEMPLATE
        }
        config.save()

