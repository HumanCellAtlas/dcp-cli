from botocore.credentials import DeferredRefreshableCredentials, CredentialProvider

from .api_client import ApiClient


class CredentialsManager(CredentialProvider):

    """
    We are using an internal feature of Boto3 that allows you to provide an object that will refresh credentials
    when they are getting close to expiry.  An instance of CredentialsManager is such an object.
    Based on an original example by Andrey here: https://allspark.dev.data.humancellatlas.org/snippets/1
    """
    def __init__(self, upload_area):
        super(CredentialsManager, self).__init__()
        self.area = upload_area

    def load(self):
        return DeferredRefreshableCredentials(refresh_using=self.get_credentials_from_upload_api, method=None)

    def get_credentials_from_upload_api(self):
        api = ApiClient(deployment_stage=self.area.deployment_stage)
        credentials = api.credentials(area_uuid=self.area.uuid)
        return dict(access_key=credentials['AccessKeyId'],
                    secret_key=credentials['SecretAccessKey'],
                    token=credentials['SessionToken'],
                    expiry_time=credentials['Expiration'])
