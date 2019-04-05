"""
Upload Service
**************
"""

from .lib.credentials_manager import CredentialsManager
from .lib.api_client import ApiClient
from .upload_config import UploadConfig
from .upload_area import UploadArea, UploadAreaURI
from .exceptions import UploadException


def select_area(**kwargs):
    """
    Select a new destination for uploads, using the UUID of a formerly selected area, or the URN of a new upload area.

    :param uri: An Upload Area URI.
    :param uuid: A RFC4122-compliant ID of the upload area.
    """
    if 'uuid' in kwargs:
        area = UploadArea(uuid=kwargs['uuid'])
    elif 'uri' in kwargs:
        area = UploadArea(uri=kwargs['uri'])
    else:
        raise UploadException("You must supply a UUID or URI")
    area.select()


def forget_area(uuid_or_alias):
    """
    Remove an area from our cache of upload areas.
    """
    config = UploadConfig()
    area_uuid = config.area_uuid_from_partial_uuid(partial_uuid=uuid_or_alias)
    config.forget_area(area_uuid)
    return area_uuid


def list_current_area(detail=False):
    """
    A generator that returns dicts describing the files in the currently selected Upload Area.
    """
    for file_info in UploadArea(uuid=UploadConfig().current_area).list(detail=detail):
        yield file_info


def list_area(area_uuid, detail=False):
    """
    A generator that returns dicts describing the files in the Upload Area with the supplied UUID.
    """
    for file_info in UploadArea(uuid=area_uuid).list(detail=detail):
        yield file_info


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
