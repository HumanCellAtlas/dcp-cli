#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest
import uuid

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca.upload import UploadConfig, UploadAreaURI, UploadException
from test.integration.upload import UploadTestCase


class TestUploadConfig(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.a_uuid = str(uuid.uuid4())
        self.b_uuid = str(uuid.uuid4())
        self.areas_config = {
            self.a_uuid: {'uri': self._make_area_uri(area_uuid=self.a_uuid)},
            self.b_uuid: {'uri': self._make_area_uri(area_uuid=self.b_uuid)},
        }
        config = hca.get_config()
        config.upload = {
            'areas': self.areas_config,
            'current_area': self.a_uuid,
            'bucket_name_template': "bogo_bucket_name_template",
            'production_api_url': "https://bogo_prod_api_url",
            'preprod_api_url_template': "https://bogo_preprod_api_url_template"
        }
        config.save()

    def test_areas__when_there_are_some__returns_areas(self):
        self.assertEqual(sorted([self.a_uuid, self.b_uuid]), sorted(UploadConfig().areas))

    def test_areas__when_the_upload_tweak_config_is_not_setup__does_not_error(self):
        config = hca.get_config()
        if 'upload' in config:
            del config['upload']
        try:
            UploadConfig().areas
        except Exception as e:
            self.fail("Expected no exception, got %s" % (e,))

    def test_current_area(self):
        self.assertEqual(self.a_uuid, UploadConfig().current_area)

    def test_bucket_name_template(self):
        self.assertEqual("bogo_bucket_name_template", UploadConfig().bucket_name_template)

    def test_preprod_api_url_template(self):
        self.assertEqual("https://bogo_preprod_api_url_template", UploadConfig().preprod_api_url_template)

    def test_production_api_url(self):
        self.assertEqual("https://bogo_prod_api_url", UploadConfig().production_api_url)

    def test_area_uri(self):
        area_uuid = str(uuid.uuid4())
        uri = self._make_area_uri(area_uuid)
        config = hca.get_config()
        config.upload = {
            'areas': {area_uuid: {'uri': uri}},
        }
        config.save()

        area_uri = UploadConfig().area_uri(area_uuid)

        self.assertIsInstance(area_uri, UploadAreaURI)
        self.assertEqual(uri, area_uri.uri)

    def test_add_area(self):
        config = UploadConfig()
        new_area_uuid = str(uuid.uuid4())
        new_area_uri = self._make_area_uri(area_uuid=new_area_uuid)
        uri = UploadAreaURI(uri=new_area_uri)

        config.add_area(uri)

        config = hca.get_config()
        self.assertIn(new_area_uuid, config.upload.areas.keys())
        self.assertEqual({'uri': new_area_uri}, config.upload.areas[new_area_uuid])

    def test_select_area(self):
        upload_config = UploadConfig()
        self.assertEqual(self.a_uuid, upload_config.current_area)

        upload_config.select_area(self.b_uuid)

        config = hca.get_config()
        self.assertEqual(self.b_uuid, config.upload.current_area)

    def test_forget_area(self):
        upload_config = UploadConfig()
        self.assertEqual(sorted([self.a_uuid, self.b_uuid]), sorted(upload_config.areas))

        upload_config.forget_area(self.a_uuid)

        config = hca.get_config()
        self.assertEqual([self.b_uuid], list(config.upload.areas))
        self.assertEqual(None, config.upload.current_area)

    def test_area_uuid_from_partial_uuid__when_given_a_non_matching_partial__raises(self):
        with self.assertRaises(UploadException):
            UploadConfig().area_uuid_from_partial_uuid(partial_uuid='underscore_will_never_appear_in_uuid')

    def test_area_uuid_from_partial_uuid__when_given_a_partial_matching_several_areas__raises(self):
        uuid1 = '11111111-1111-1111-1111-111111111111'
        uuid2 = '11111111-2222-2222-2222-222222222222'
        config = hca.get_config()
        config.upload = {
            'areas': {
                uuid1: {'uri': "s3://foo/{}/".format(uuid1)},
                uuid2: {'uri': "s3://foo/{}/".format(uuid2)},
            },
        }
        config.save()

        with self.assertRaises(UploadException):
            UploadConfig().area_uuid_from_partial_uuid(partial_uuid='11111111')

    def test_area_uuid_from_partial_uuid__when_given_a_single_partial__returns_uuid(self):
        uuid1 = '11111111-1111-1111-1111-111111111111'
        uuid2 = '22222222-2222-2222-2222-222222222222'
        config = hca.get_config()
        config.upload = {
            'areas': {
                uuid1: {'uri': "s3://foo/{}/".format(uuid1)},
                uuid2: {'uri': "s3://foo/{}/".format(uuid2)},
            },
        }
        config.save()

        uuid = UploadConfig().area_uuid_from_partial_uuid(partial_uuid='11111111')

        self.assertEqual(uuid1, uuid)


if __name__ == "__main__":
    unittest.main()
