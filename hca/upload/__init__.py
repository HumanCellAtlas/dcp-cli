"""
Upload Service
**************
"""

from .credentials_manager import CredentialsManager
from .upload_config import UploadConfig
from .upload_area import UploadArea, UploadAreaURI
from .exceptions import UploadException
from .api_client import ApiClient


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
    area = UploadArea.from_alias(uuid_or_alias)
    area.forget()
    return area


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


def list_areas():
    return [{'uuid': area.uuid, 'is_selected': area.is_selected} for area in UploadArea.all()]


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
