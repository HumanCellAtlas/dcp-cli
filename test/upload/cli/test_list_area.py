import os
import sys
import unittest
from argparse import Namespace

import responses
import boto3
from moto import mock_s3

from ... import CapturingIO, reset_tweak_changes
from .. import mock_current_upload_area

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload.cli.list_area_command import ListAreaCommand


class TestUploadListAreaCommand(unittest.TestCase):

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
    def test_list_area_command(self):
        area = mock_current_upload_area()
        self.upload_bucket.Object('/'.join([area.uuid, 'file1.fastq.gz'])).put(Body="foo")
        self.upload_bucket.Object('/'.join([area.uuid, 'sample.json'])).put(Body="foo")

        with CapturingIO('stdout') as stdout:
            ListAreaCommand(Namespace(long=False))

        self.assertEqual(stdout.captured(), "file1.fastq.gz\nsample.json\n")

    @reset_tweak_changes
    @responses.activate
    def test_list_area_command_with_long_option(self):
        area = mock_current_upload_area()
        self.upload_bucket.Object('/'.join([area.uuid, 'file1.fastq.gz'])).put(Body="foo")

        list_url = 'https://upload.{stage}.data.humancellatlas.org/v1/area/{uuid}/files_info'.format(
            stage=self.deployment_stage,
            uuid=area.uuid)
        responses.add(responses.PUT, list_url, status=200, json=[
            {
                "name": "file1.fastq.gz",
                "content_type": "binary/octet-stream; dcp-type=data",
                "size": 123,
                "url": "http://example.com",
                "checksums": {"sha1": "shaaa"}
            }
        ])

        with CapturingIO('stdout') as stdout:
            ListAreaCommand(Namespace(long=True))

        self.assertRegexpMatches(stdout.captured(), "size\s+123")
        self.assertRegexpMatches(stdout.captured(), "Content-Type\s+binary/octet-stream; dcp-type=data")
        self.assertRegexpMatches(stdout.captured(), "SHA1\s+shaaa")
