import os
import sys
from argparse import Namespace

import responses
import boto3

from ... import CapturingIO
from .. import UploadTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload.cli.list_area_command import ListAreaCommand


class TestUploadListAreaCommand(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()

    def test_list_area_command(self):
        self.upload_bucket.Object('/'.join([self.area.uuid, 'file1.fastq.gz'])).put(Body="foo")
        self.upload_bucket.Object('/'.join([self.area.uuid, 'sample.json'])).put(Body="foo")

        with CapturingIO('stdout') as stdout:
            ListAreaCommand(Namespace(long=False))

        self.assertEqual(stdout.captured(), "file1.fastq.gz\nsample.json\n")

    @responses.activate
    def test_list_area_command_with_long_option(self):
        self.upload_bucket.Object('/'.join([self.area.uuid, 'file1.fastq.gz'])).put(Body="foo")

        list_url = 'https://upload.{stage}.data.humancellatlas.org/v1/area/{uuid}/files_info'.format(
            stage=self.deployment_stage,
            uuid=self.area.uuid)
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
