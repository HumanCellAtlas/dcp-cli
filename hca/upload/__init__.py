from .upload_area import UploadArea
from .upload_area_urn import UploadAreaURN
from .exceptions import UploadException


def select_area(**kwargs):
    """
    Select a new destination for uploads, using the UUID of a formerly selected area, or the URN of a new upload area.

    :param urn: An Upload Area URN.
    :param uuid: A RFC4122-compliant ID of the upload area.
    """
    if 'uuid' in kwargs:
        area = UploadArea(uuid=kwargs['uuid'])
    elif 'urn' in kwargs:
        area = UploadArea(urn=UploadAreaURN(kwargs['urn']))
    else:
        raise UploadException("You must supply a UUID or URN")
    area.select()


def list_areas():
    """
    Return a list of all the Upload Areas that we have previously used.
    Indicating which one is currently selected for the next upload.
    Returns a list of dicts with elements {uuid: <string> , is_selected: <bool>}
    """
    return [{'uuid': area.uuid, 'is_selected': area.is_selected} for area in UploadArea.all()]
