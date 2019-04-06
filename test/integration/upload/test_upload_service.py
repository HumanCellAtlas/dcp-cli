#!/usr/bin/env python
# coding: utf-8

import os
import sys
import uuid
from mock import Mock, patch

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload import UploadService, UploadAreaURI, UploadArea
from test.integration.upload import UploadTestCase


class TestUploadService(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.api_key = "bogo_api_key"
        self.upload_service = UploadService(deployment_stage=self.deployment_stage, api_token=self.api_key)

    def test_create_area(self):
        with patch('hca.upload.upload_service.ApiClient') as mock_api_client_class:
            area_uuid = str(uuid.uuid4())
            area_uri_str = 's3://bogobucket/{uuid}/'.format(uuid=area_uuid)
            mock_create_area = Mock(return_value={'uri': area_uri_str})
            mock_api_client = Mock(create_area=mock_create_area)
            mock_api_client_class.return_value = mock_api_client

            upload = UploadService(deployment_stage=self.deployment_stage, api_token=self.api_key)
            area = upload.create_area(area_uuid=area_uuid)

            mock_api_client_class.assert_called_once_with(deployment_stage='test',
                                                          authentication_token=self.api_key)
            mock_create_area.assert_called_once_with(area_uuid=area_uuid)
            self.assertIsInstance(area, UploadArea)
            self.assertEqual(area_uuid, area.uuid)

    def test_upload_area(self):
        area_uuid = str(uuid.uuid4())
        area_uri = UploadAreaURI(self._make_area_uri(area_uuid=area_uuid))

        upload = UploadService(deployment_stage=self.deployment_stage, api_token=self.api_key)
        area = upload.upload_area(area_uri)

        self.assertIsInstance(area, UploadArea)
        self.assertEqual(area_uuid, area.uuid)
