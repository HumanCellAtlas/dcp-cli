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
