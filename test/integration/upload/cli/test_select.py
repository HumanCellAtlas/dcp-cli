#!/usr/bin/env python
# coding: utf-8

import os
import sys
import uuid
import unittest
from argparse import Namespace

import six

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca.upload.cli.select_command import SelectCommand
from test import CapturingIO
from test.integration.upload import UploadTestCase


class TestUploadCliSelectCommand(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self._area_uuid = str(uuid.uuid4())
        self._uri = "s3://org-humancellatlas-upload-test/{}/".format(self._area_uuid)

    def test_when_given_an_unrecognized_urn_it_stores_it_in_upload_area_list_and_sets_it_as_current_area(self):
        with CapturingIO('stdout') as stdout:
            args = Namespace(uri_or_alias=self._uri)
            SelectCommand(args)

        config = hca.get_config()
        self.assertIn(self._area_uuid, config.upload.areas)
        self.assertEqual(self._uri, config.upload.areas[self._area_uuid]['uri'])
        self.assertEqual(self._area_uuid, config.upload.current_area)

    def test_when_given_an_unrecognized_uri_without_slash_it_sets_it_as_current_area(self):
        uri_without_slash = "s3://org-humancellatlas-upload-test/{}".format(self._area_uuid)
        with CapturingIO('stdout') as stdout:
            args = Namespace(uri_or_alias=uri_without_slash)
            SelectCommand(args)

        config = hca.get_config()
        self.assertIn(self._area_uuid, config.upload.areas)
        self.assertEqual(self._uri, config.upload.areas[self._area_uuid]['uri'])
        self.assertEqual(self._area_uuid, config.upload.current_area)

    def test_when_given_a_uri_it_prints_an_alias(self):
        config = hca.get_config()
        config.upload = {
            'areas': {
                'deadbeef-dead-dead-dead-beeeeeeeeeef': {
                    'uri': 's3://bogobucket/deadbeef-dead-dead-dead-beeeeeeeeeef/'
                },
            }
        }
        config.save()
        new_area_uuid = 'deafbeef-deaf-deaf-deaf-beeeeeeeeeef'
        new_area_uri = 's3://bogobucket/{}/'.format(new_area_uuid)

        with CapturingIO('stdout') as stdout:
            args = Namespace(uri_or_alias=new_area_uri)
            SelectCommand(args)

        six.assertRegex(self, stdout.captured(), "alias \"{}\"".format('deaf'))

    def test_when_given_an_alias_that_matches_no_areas_it_prints_a_warning(self):

        config = hca.get_config()
        config.upload = {'areas': {}}
        config.save()

        with CapturingIO('stdout') as stdout:
            args = Namespace(uri_or_alias='aaa')
            SelectCommand(args)

        six.assertRegex(self, stdout.captured(), "don't recognize area")

    def test_when_given_an_alias_that_matches_more_than_one_area_it_prints_a_warning(self):
        config = hca.get_config()
        config.upload = {
            'areas': {
                'deadbeef-dead-dead-dead-beeeeeeeeeef': {'uri': 's3://bucket/deadbeef-dead-dead-dead-beeeeeeeeeef/'},
                'deafbeef-deaf-deaf-deaf-beeeeeeeeeef': {'uri': 's3://bucket/deafbeef-deaf-deaf-deaf-beeeeeeeeeef/'},
            }
        }
        config.save()

        with CapturingIO('stdout') as stdout:
            args = Namespace(uri_or_alias='dea')
            SelectCommand(args)

        six.assertRegex(self, stdout.captured(), "matches more than one")

    def test_when_given_an_alias_that_matches_one_area_it_selects_it(self):
        a_uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        b_uuid = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
        config = hca.get_config()
        config.upload = {
            'areas': {
                a_uuid: {'uri': "s3://org-humancellatlas-upload-bogo/%s/" % (a_uuid,)},
                b_uuid: {'uri': "s3://org-humancellatlas-upload-bogo/%s/" % (b_uuid,)},
            }
        }
        config.save()

        with CapturingIO('stdout') as stdout:
            args = Namespace(uri_or_alias='bbb')
            SelectCommand(args)

        config = hca.get_config()
        self.assertEqual(b_uuid, config.upload.current_area)


if __name__ == "__main__":
    unittest.main()
