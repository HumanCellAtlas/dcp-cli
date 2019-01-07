#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest
import uuid
import responses

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload import ApiClient, UploadConfig
from test.integration.upload import UploadTestCase


class TestApiClient(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        config = UploadConfig()
        config._config.upload.preprod_api_url_template = "https://prefix.{deployment_stage}.suffix/v1"
        config._config.upload.production_api_url = "https://prefix.suffix/v1"
        config.save()

    def test_api_base_is_set_correctly_for_preprod(self):

        client = ApiClient(deployment_stage="somestage")
        self.assertEqual("https://prefix.somestage.suffix/v1", client.api_url_base)

    def test_api_base_is_set_correctly_for_prod(self):
        client = ApiClient(deployment_stage="prod")
        self.assertEqual("https://prefix.suffix/v1", client.api_url_base)

    @responses.activate
    def test_file_upload_notification(self):
        area_id = str(uuid.uuid4())
        client = ApiClient(deployment_stage="test")
        self.simulate_file_upload_notification_api(area_uuid=area_id,
                                                   filename="filename123",
                                                   api_host="prefix.test.suffix")

        response = client.file_upload_notification(area_uuid=area_id, filename="filename123")

        self.assertEqual(response.status_code, 202)


if __name__ == "__main__":
    unittest.main()
