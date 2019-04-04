#!/usr/bin/env python
# coding: utf-8

import json
import os
import random
import sys
import unittest
import uuid

import responses

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
from hca.upload import UploadConfig, UploadAreaURI
from test.integration.upload import UploadTestCase


class TestUploadConfig(UploadTestCase):

    @staticmethod
    def _make_area_uri(area_uuid=None):
        return "s3://foo/{}/".format(area_uuid or str(uuid.uuid4()))

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
        self.assertEqual(self.areas_config, UploadConfig().areas)

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
        self.assertEqual(sorted([self.a_uuid, self.b_uuid]), sorted((upload_config.areas.keys())))

        upload_config.forget_area(self.a_uuid)

        config = hca.get_config()
        self.assertEqual([self.b_uuid], list(config.upload.areas.keys()))
        self.assertEqual(None, config.upload.current_area)


if __name__ == "__main__":
    unittest.main()
