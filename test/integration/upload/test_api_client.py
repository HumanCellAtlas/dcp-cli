#!/usr/bin/env python
# coding: utf-8

import os
import sys
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload import ApiClient, UploadConfig
from test.integration.upload import UploadTestCase


class TestApiClient(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        config = UploadConfig()
        config._config.upload.preprod_api_url_template = "https://prefix.{deployment_stage}.suffix"
        config._config.upload.production_api_url = "https://prefix.suffix"
        config.save()

    def test_api_base_is_set_correctly_for_preprod(self):

        client = ApiClient(deployment_stage="somestage")
        self.assertEqual("https://prefix.somestage.suffix", client.api_url_base)

    def test_api_base_is_set_correctly_for_prod(self):
        client = ApiClient(deployment_stage="prod")
        self.assertEqual("https://prefix.suffix", client.api_url_base)


if __name__ == "__main__":
    unittest.main()
