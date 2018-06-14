import boto3
from botocore.errorfactory import ClientError

from .api_client import ApiClient
from .upload_config import UploadConfig


class CredentialsManager:

    def __init__(self, upload_area):
        self.area = upload_area

    def get_credentials(self):
        """
        Get credentials from Config, or request them from the API, then store them in Config.

        Note that we check the credentials are good using get-caller-identity before returning them,
        instead of providing a decorator that will catch ExpiredToken and retry.
        This is because some of the Upload methods return generators, which mean the exception happens
        outside of our control.
        """
        config = UploadConfig()
        our_info = config.areas[self.area.uuid]
        if 'credentials' not in our_info or not self._credentials_are_good(our_info['credentials']):
            self._get_new_credentials()
        return our_info['credentials']

    def delete_credentials(self):
        config = UploadConfig()
        del config.areas[self.area.uuid]['credentials']
        config.save()

    def _credentials_are_good(self, credentials):
        try:
            session = boto3.session.Session(**credentials)
            sts = session.client('sts')
            sts.get_caller_identity()
            return True
        except ClientError:
            return False

    def _get_new_credentials(self):
        api = ApiClient(deployment_stage=self.area.deployment_stage)
        raw_creds = api.credentials(area_uuid=self.area.uuid)
        creds = {
            'aws_access_key_id': raw_creds['AccessKeyId'],
            'aws_secret_access_key': raw_creds['SecretAccessKey'],
            'aws_session_token': raw_creds['SessionToken']
        }
        config = UploadConfig()
        config.areas[self.area.uuid]['credentials'] = creds
        config.save()
        return creds
