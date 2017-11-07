import os
import sys
import unittest
from argparse import Namespace

import requests_mock

from ... import CapturingIO, reset_tweak_changes
from .. import mock_current_upload_area

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload.cli.list_area_command import ListAreaCommand


class TestUploadListAreaCommand(unittest.TestCase):

    @reset_tweak_changes
    def test_list_area_command(self):

        area = mock_current_upload_area()

        with requests_mock.mock() as m:
            mock_url = 'https://upload.test.data.humancellatlas.org/v1/area/{uuid}'.format(uuid=area.uuid)
            m.get(mock_url, text='{"files":[{"name":"file1.fastq.gz"},{"name":"sample.json"}]}')

            with CapturingIO('stdout') as stdout:
                ListAreaCommand(Namespace(long=False))

        self.assertEqual(stdout.captured(), "file1.fastq.gz\nsample.json\n")

    @reset_tweak_changes
    def test_list_area_command_with_long_option(self):

        area = mock_current_upload_area()

        with requests_mock.mock() as m:
            mock_url = 'https://upload.test.data.humancellatlas.org/v1/area/{uuid}'.format(uuid=area.uuid)
            m.get(mock_url, text='{"files":['
                                 '{"name":"file1.fastq.gz",'
                                 '"content_type":"foo/bar",'
                                 '"size":123,'
                                 '"url":"http://example.com",'
                                 '"checksums":{"sha1":"shaaa"}}'
                                 ']}')

            with CapturingIO('stdout') as stdout:
                ListAreaCommand(Namespace(long=True))

        self.assertRegexpMatches(stdout.captured(), "size\s+123")
        self.assertRegexpMatches(stdout.captured(), "Content-Type\s+foo/bar")
        self.assertRegexpMatches(stdout.captured(), "SHA1\s+shaaa")
