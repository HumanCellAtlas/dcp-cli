"""
Upload Service
**************
"""

from .lib.credentials_manager import CredentialsManager
from .lib.api_client import ApiClient
from .upload_config import UploadConfig
from .upload_area import UploadArea, UploadAreaURI
from .exceptions import UploadException


def get_credentials(area_uuid):
    """
    Return a set of credentials that may be used to access the Upload Area.
    """
    area = UploadArea(uuid=area_uuid)
    creds_mgr = CredentialsManager(area)
    creds = creds_mgr.get_credentials_from_upload_api()
    return {
        'AWS_ACCESS_KEY_ID': creds['access_key'],
        'AWS_SECRET_ACCESS_KEY': creds['secret_key'],
        'AWS_SESSION_TOKEN': creds['token']
    }
