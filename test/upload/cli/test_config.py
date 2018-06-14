from argparse import Namespace

import responses

from ... import CapturingIO
from .. import UploadTestCase

import hca
from hca.upload.cli.list_area_command import ListAreaCommand


class TestConfig(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()
        self.upload_bucket.Object('/'.join([self.area.uuid, 'file1.fastq.gz'])).put(Body="foo")

    @responses.activate
    def test_upload_service_api_url_template_is_obeyed(self):
        config = hca.get_config()
        config.upload.upload_service_api_url_template = "https://upload.example.com/v1"
        config.save()

        creds_url = self.simulate_credentials_api(self.area.uuid, api_host="upload.example.com")

        list_url = 'https://upload.example.com/v1/area/{uuid}/files_info'.format(uuid=self.area.uuid)
        responses.add(responses.PUT, list_url, json={}, status=200)

        with CapturingIO('stdout') as stdout:
            ListAreaCommand(Namespace(long=True))

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, creds_url)
        self.assertEqual(responses.calls[1].request.url, list_url)
