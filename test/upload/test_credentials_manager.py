import datetime

import responses

from . import UploadTestCase

from hca.upload import UploadConfig
from hca.upload.credentials_manager import CredentialsManager

call_count = 0


class TestCredentialsManager(UploadTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.area = self.mock_current_upload_area()
        self.cm = CredentialsManager(upload_area=self.area)

    def _store_credentials(self):
        stored_creds = {'aws_access_key_id': 'skey', 'aws_secret_access_key': 'ssecret', 'aws_session_token': 'stoken'}
        config = UploadConfig()
        config.areas[self.area.uuid]['credentials'] = stored_creds
        config.save()
        return stored_creds

    def _simulate_credentials_api(self):
        api_host = "upload.{stage}.data.humancellatlas.org".format(stage=self.area.deployment_stage)
        creds_url = 'https://{api_host}/v1/area/{uuid}/credentials'.format(api_host=api_host, uuid=self.area.uuid)
        expiration = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + 'Z'
        api_creds = {
            'AccessKeyId': 'apikey',
            'SecretAccessKey': 'apisecret',
            'SessionToken': 'apitoken',
            'Expiration': expiration
        }
        responses.add(responses.POST, creds_url, json=api_creds, status=201)
        expected_creds = {
            'access_key': api_creds['AccessKeyId'],
            'secret_key': api_creds['SecretAccessKey'],
            'token': api_creds['SessionToken'],
            'expiry_time': expiration
        }
        return creds_url, expected_creds

    @responses.activate
    def test_get_credentials_from_upload_api(self):
        creds_url, expected_creds = self._simulate_credentials_api()

        creds = self.cm.get_credentials_from_upload_api()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, creds_url)
        self.assertEqual(expected_creds, creds)
