#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest
from argparse import Namespace

import responses
import six

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload.cli.creds_command import CredsCommand
from test import CapturingIO
from test.integration.upload import UploadTestCase


class TestUploadCliCredsCommand(UploadTestCase):

    @responses.activate
    def test_creds(self):
        area = self.mock_current_upload_area()
        self.simulate_credentials_api(area_uuid=area.uuid)

        with CapturingIO('stdout') as stdout:
            args = Namespace(uuid_or_alias=area.uuid)
            CredsCommand(args)

        non_blank_lines = [s for s in stdout.captured().split("\n") if s]
        self.assertEqual(3, len(non_blank_lines))
        six.assertRegex(self, stdout.captured(), "AWS_ACCESS_KEY_ID=")
        six.assertRegex(self, stdout.captured(), "AWS_SECRET_ACCESS_KEY=")
        six.assertRegex(self, stdout.captured(), "AWS_SESSION_TOKEN=")


if __name__ == "__main__":
    unittest.main()
