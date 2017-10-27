import os
import re

from .upload_config import UploadConfig
from .upload_area import UploadArea
from .upload_area_urn import UploadAreaURN
from .exceptions import UploadException
from .s3_agent import S3Agent


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


def upload_file(file_path, target_filename=None, report_progress=False):
    """
    Upload a file to the currently selected Upload Area

    :param file_path: <string> Path to file on local filesystem.
    :param target_filename: <string> Rename file during upload (optional).
    :param report_progress: <bool> Display progress % during upload (optional).
    """
    upload_area = UploadArea(uuid=UploadConfig().current_area())
    file_s3_key = "%s/%s" % (upload_area.uuid, target_filename or os.path.basename(file_path))
    bucket_name = UploadConfig().bucket_name_template.format(deployment_stage=upload_area.urn.deployment_stage)
    content_type = 'application/json' if re.search('.json$', file_path) else 'hca-data-file'
    s3agent = S3Agent(aws_credentials=upload_area.urn.credentials)
    s3agent.upload_file(file_path, bucket_name, file_s3_key, content_type, report_progress=report_progress)
