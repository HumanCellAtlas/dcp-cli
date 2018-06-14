import responses
from mock import patch

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
        api_creds = {'AccessKeyId': 'apikey', 'SecretAccessKey': 'apisecret', 'SessionToken': 'apitoken'}
        responses.add(responses.POST, creds_url, json=api_creds, status=201)
        expected_creds = {
            'aws_access_key_id': api_creds['AccessKeyId'],
            'aws_secret_access_key': api_creds['SecretAccessKey'],
            'aws_session_token': api_creds['SessionToken']
        }
        return (creds_url, expected_creds)

    @responses.activate
    def test_get_credentials_with_no_creds_in_config_should_get_them_from_the_api_and_save_then_in_config(self):
        creds_url, expected_creds = self._simulate_credentials_api()

        creds = self.cm.get_credentials()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, creds_url)
        self.assertEqual(expected_creds, creds)
        self.assertEqual(expected_creds, UploadConfig().areas[self.area.uuid]['credentials'])

    @responses.activate
    def test_get_credentials_with_good_creds_in_config_it_should_return_them_and_not_call_the_api(self):
        self._simulate_credentials_api()
        stored_creds = self._store_credentials()

        creds = self.cm.get_credentials()

        self.assertEqual(len(responses.calls), 0)
        self.assertEqual(stored_creds, creds)

    @responses.activate
    @patch('hca.upload.credentials_manager.CredentialsManager._credentials_are_good')
    def test_get_credentials_with_bad_creds_in_config_it_should_get_new_ones_from_the_api(self, mock_creds_good):
        mock_creds_good.return_value = False
        creds_url, expected_creds = self._simulate_credentials_api()
        self._store_credentials()

        creds = self.cm.get_credentials()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, creds_url)
        self.assertEqual(expected_creds, creds)
        self.assertEqual(expected_creds, UploadConfig().areas[self.area.uuid]['credentials'])

    def test_delete_credentials_for_area(self):
        self._store_credentials()

        self.cm.delete_credentials()

        config = UploadConfig()
        self.assertNotIn('credentials', config.areas[self.area.uuid])
