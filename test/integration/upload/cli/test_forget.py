#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest
from argparse import Namespace

import six

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload import UploadConfig
from hca.upload.cli.forget_command import ForgetCommand
from test import CapturingIO
from test.integration.upload import UploadTestCase


class TestUploadCliForgetCommand(UploadTestCase):

    def test_when_given_an_alias_that_matches_one_area_it_forgets_that_area(self):
        area = self.mock_current_upload_area()
        self.assertIn(area.uuid, UploadConfig().areas)
        self.assertEqual(area.uuid, UploadConfig().current_area)

        with CapturingIO('stdout') as stdout:
            args = Namespace(uuid_or_alias=area.uuid)
            ForgetCommand(args)

        self.assertNotIn(area.uuid, UploadConfig().areas)
        self.assertEqual(None, UploadConfig().current_area)

    def test_when_given_an_alias_that_matches_no_areas_it_prints_a_warning(self):

        with CapturingIO('stdout') as stdout:
            with self.assertRaises(SystemExit):
                args = Namespace(uuid_or_alias='bogo-uuid')
                ForgetCommand(args)

        six.assertRegex(self, stdout.captured(), "don't recognize area")

    def test_when_given_an_alias_that_matches_more_than_one_area_it_prints_a_warning(self):
        self.mock_upload_area('deadbeef-dead-dead-dead-beeeeeeeeeef')
        self.mock_upload_area('deafbeef-deaf-deaf-deaf-beeeeeeeeeef')

        with CapturingIO('stdout') as stdout:
            with self.assertRaises(SystemExit):
                args = Namespace(uuid_or_alias='dea')
                ForgetCommand(args)

        six.assertRegex(self, stdout.captured(), "matches more than one")


if __name__ == "__main__":
    unittest.main()
