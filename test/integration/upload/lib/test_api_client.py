#!/usr/bin/env python
# coding: utf-8

import json
import os
import random
import sys
import unittest
import uuid

import responses

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.upload import UploadConfig
from hca.upload.lib.api_client import ApiClient
from test.integration.upload import UploadTestCase


class TestApiClient(UploadTestCase):

    """
    These tests test that the functions:
      - initiate the correct type of HTTP request
      - to the correct HTTP endpoint
      - authenticate when necessary
    """

    def setUp(self):
        super(self.__class__, self).setUp()
        config = UploadConfig()
        config._config.upload.preprod_api_url_template = "https://prefix.{deployment_stage}.suffix/v1"
        config._config.upload.production_api_url = "https://prefix.suffix/v1"
        config.save()

        self.api_key = "api-key-{}".format(random.randint(0,999999999))
        self.api_client = ApiClient(deployment_stage="test", authentication_token=self.api_key)

    @responses.activate
    def test_create_area(self):
        upload_area_id = uuid.uuid4()
        url = 'https://prefix.test.suffix/v1/area/{area_id}'.format(area_id=upload_area_id)
        result_data = {'uri': "s3://somebucket/somekey/"}
        responses.add(responses.POST, url, json=result_data, status=201)

        result = self.api_client.create_area(upload_area_id)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('POST', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertEqual(self.api_key, responses.calls[0].request.headers['Api-Key'])
        self.assertEqual(result_data, result)

    @responses.activate
    def test_area_exists(self):
        upload_area_id = uuid.uuid4()
        url = 'https://prefix.test.suffix/v1/area/{area_id}'.format(area_id=upload_area_id)
        responses.add(responses.HEAD, url, status=200)

        result = self.api_client.area_exists(upload_area_id)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('HEAD', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertTrue(result)

    @responses.activate
    def test_delete_area(self):
        upload_area_id = uuid.uuid4()
        url = 'https://prefix.test.suffix/v1/area/{area_id}'.format(area_id=upload_area_id)
        responses.add(responses.DELETE, url, json={'uri': "s3://somebucket/somekey/"}, status=202)

        self.api_client.delete_area(upload_area_id)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('DELETE', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertEqual(self.api_key, responses.calls[0].request.headers['Api-Key'])

    @responses.activate
    def test_credentials(self):
        upload_area_id = uuid.uuid4()
        result_data = {'some': 'keys'}
        url = 'https://prefix.test.suffix/v1/area/{area_id}/credentials'.format(area_id=upload_area_id)
        responses.add(responses.POST, url, json={'some': 'keys'}, status=200)

        result = self.api_client.credentials(upload_area_id)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('POST', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertEqual(result_data, result)

    @responses.activate
    def test_store_file(self):
        upload_area_id = uuid.uuid4()
        filename = "file-{number}".format(number=random.randint(0, 999999999))
        file_content = "lorem ipsum"
        content_type = "application/madeup"
        result_data = {'file': 'info'}
        url = 'https://prefix.test.suffix/v1/area/{area_id}/{filename}'.format(area_id=upload_area_id, filename=filename)
        responses.add(responses.PUT, url, json=result_data, status=200)

        result = self.api_client.store_file(area_uuid=upload_area_id,
                                            filename=filename,
                                            file_content=file_content,
                                            content_type=content_type)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('PUT', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertEqual(self.api_key, responses.calls[0].request.headers['Api-Key'])
        self.assertEqual(content_type, responses.calls[0].request.headers['Content-Type'])
        self.assertEqual(file_content, responses.calls[0].request.body)
        self.assertEqual(result_data, result)

    @responses.activate
    def test_file_upload_notification(self):
        upload_area_id = uuid.uuid4()
        filename = "file-{number}".format(number=random.randint(0, 999999999))
        url = 'https://prefix.test.suffix/v1/area/{uuid}/{name}'.format(uuid=upload_area_id, name=filename)
        responses.add(responses.POST, url, status=202)

        result = self.api_client.file_upload_notification(area_uuid=upload_area_id, filename=filename)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('POST', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertTrue(result)

    @responses.activate
    def test_files_info(self):
        upload_area_id = uuid.uuid4()
        filename = "file-{number}".format(number=random.randint(0, 999999999))
        file_list = [filename]
        result_data = [{'files': 'info'}]
        url = 'https://prefix.test.suffix/v1/area/{area_id}/files_info'.format(area_id=upload_area_id)
        responses.add(responses.PUT, url, json=result_data, status=200)

        result = self.api_client.files_info(area_uuid=upload_area_id,
                                            file_list=file_list)\

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('PUT', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertEqual(json.dumps(file_list), responses.calls[0].request.body.decode('utf8'))
        self.assertEqual(result_data, result)

    @responses.activate
    def test_checksum_status(self):
        upload_area_id = uuid.uuid4()
        filename = "file-{number}".format(number=random.randint(0, 999999999))
        result_data = {
            "checksum_status": "string",
            "checksums": {
                "crc32c": "string",
                "s3_etag": "string",
                "sha1": "string",
                "sha256": "string"
            }
        }
        url = 'https://prefix.test.suffix/v1/area/{area_id}/{filename}/checksum'.format(area_id=upload_area_id,
                                                                                        filename=filename)
        responses.add(responses.GET, url, json=result_data, status=200)

        result = self.api_client.checksum_status(area_uuid=upload_area_id, filename=filename)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('GET', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertEqual(result_data, result)

    @responses.activate
    def test_checksum_statuses(self):
        upload_area_id = uuid.uuid4()
        filename = "file-{number}".format(number=random.randint(0, 999999999))
        result_data = {
            "CHECKSUMMED": 0,
            "CHECKSUMMING": 0,
            "SCHEDULED": 0,
            "TOTAL_NUM_FILES": 0,
            "UNSCHEDULED": 0
        }
        url = 'https://prefix.test.suffix/v1/area/{area_id}/checksums'.format(area_id=upload_area_id, filename=filename)
        responses.add(responses.GET, url, json=result_data, status=200)

        result = self.api_client.checksum_statuses(area_uuid=upload_area_id)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('GET', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertEqual(result_data, result)

    @responses.activate
    def test_validate_files(self):
        upload_area_id = uuid.uuid4()
        file1 = "file-{number}".format(number=random.randint(0, 999999999))
        file2 = "file-{number}".format(number=random.randint(0, 999999999))
        file_list = [file1, file2]
        validator_image = "some_docker_image"
        original_validation_id = "122"
        environment = {"ENVVAR": "ENVVAL"}
        result_data = {"validation_id": "123"}
        url = 'https://prefix.test.suffix/v1/area/{area_id}/validate'.format(area_id=upload_area_id)
        responses.add(responses.PUT, url, json=result_data, status=200)

        result = self.api_client.validate_files(area_uuid=upload_area_id,
                                                file_list=file_list,
                                                validator_image=validator_image,
                                                original_validation_id=original_validation_id,
                                                environment=environment)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('PUT', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertEqual(self.api_key, responses.calls[0].request.headers['Api-Key'])
        self.assertEqual(json.dumps({
            "environment": environment,
            "files": file_list,
            "original_validation_id": original_validation_id,
            "validator_image": validator_image
        }), responses.calls[0].request.body.decode('utf8'))
        self.assertEqual(result_data, result)

    @responses.activate
    def test_validation_status(self):
        upload_area_id = uuid.uuid4()
        filename = "file-{number}".format(number=random.randint(0, 999999999))
        result_data = {
            "validation_results": "string",
            "validation_status": "string"
        }
        url = 'https://prefix.test.suffix/v1/area/{area_id}/{filename}/validate'.format(area_id=upload_area_id,
                                                                                        filename=filename)
        responses.add(responses.GET, url, json=result_data, status=200)

        result = self.api_client.validation_status(area_uuid=upload_area_id, filename=filename)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('GET', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertEqual(result_data, result)

    @responses.activate
    def test_validation_statuses(self):
        upload_area_id = uuid.uuid4()
        result_data = {
            "SCHEDULED": 0,
            "VALIDATED": 0,
            "VALIDATING": 0
        }
        url = 'https://prefix.test.suffix/v1/area/{area_id}/validations'.format(area_id=upload_area_id)
        responses.add(responses.GET, url, json=result_data, status=200)

        result = self.api_client.validation_statuses(area_uuid=upload_area_id)

        self.assertEqual(1, len(responses.calls))
        self.assertEqual('GET', responses.calls[0].request.method)
        self.assertEqual(url, responses.calls[0].request.url)
        self.assertTrue('Api-Key' not in responses.calls[0].request.headers)  # Unauthenticated endpoint
        self.assertEqual(result_data, result)




if __name__ == "__main__":
    unittest.main()
