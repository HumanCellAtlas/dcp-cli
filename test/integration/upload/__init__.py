import datetime
import re
import uuid
import unittest

import boto3
from moto import mock_s3, mock_sts
import responses

import hca
from hca.upload import UploadService, UploadConfig, UploadAreaURI
from test import TweakResetter


class UploadTestCase(unittest.TestCase):

    UPLOAD_BUCKET_NAME_TEMPLATE = 'org-bogo-upload-{deployment_stage}'

    def setUp(self):
        # Setup mock AWS
        self.s3_mock = mock_s3()
        self.s3_mock.start()
        self.sts_mock = mock_sts()
        self.sts_mock.start()
        # Don't crush Tweak config
        self.tweak_resetter = TweakResetter()
        self.tweak_resetter.save_config()
        # Upload bucket
        self.deployment_stage = 'test'
        self.upload_bucket_name = self.UPLOAD_BUCKET_NAME_TEMPLATE.format(deployment_stage=self.deployment_stage)
        self.upload_bucket = boto3.resource('s3').Bucket(self.upload_bucket_name)
        self.upload_bucket.create()
        # Upload Service
        self.api_token = "bogo-api-token"
        self.upload_service = UploadService(deployment_stage=self.deployment_stage, api_token=self.api_token)

    def tearDown(self):
        self.s3_mock.stop()
        self.sts_mock.stop()
        self.tweak_resetter.restore_config()

    def mock_current_upload_area(self, area_uuid=None, bucket_name=None):
        area = self.mock_upload_area(area_uuid=area_uuid, bucket_name=bucket_name)
        UploadConfig().select_area(area.uuid)
        return area

    def mock_upload_area(self, area_uuid=None, bucket_name=None):
        """
        Create a UUID and URI for a fake upload area, store it in Tweak config.
        """
        if not area_uuid:
            area_uuid = str(uuid.uuid4())
        if not bucket_name:
            bucket_name = self.UPLOAD_BUCKET_NAME_TEMPLATE.format(deployment_stage=self.deployment_stage)
        area_uri_str = "s3://{bucket}/{uuid}/".format(bucket=bucket_name, uuid=area_uuid)
        area_uri = UploadAreaURI(area_uri_str)
        config = UploadConfig()
        config.add_area(area_uri)
        area = self.upload_service.upload_area(area_uri=area_uri)
        return area

    def simulate_credentials_api(self, area_uuid,
                                 api_host="upload.{stage}.data.humancellatlas.org",
                                 stage='test'):
        if re.search('\{stage\}', api_host):
            api_host = api_host.format(stage=stage)

        creds_url = 'https://{api_host}/v1/area/{uuid}/credentials'.format(api_host=api_host, uuid=area_uuid)
        expiration = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + 'Z'
        creds = {
            'AccessKeyId': 'foo',
            'SecretAccessKey': 'bar',
            'SessionToken': 'baz',
            'Expiration': expiration
        }
        responses.add(responses.POST, creds_url, json=creds, status=201)
        return creds_url

    def _setup_tweak_config(self):
        config = hca.get_config()
        config.upload = {
            'areas': {},
            'bucket_name_template': self.UPLOAD_BUCKET_NAME_TEMPLATE
        }
        config.save()

    def _make_area_uri(self, area_uuid=None):
        return "s3://{bucket}/{uuid}/".format(bucket=self.upload_bucket_name,
                                              uuid=(area_uuid or str(uuid.uuid4())))

