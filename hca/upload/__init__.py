import os
import re

from .upload_config import UploadConfig
from .upload_area import UploadArea
from .upload_area_urn import UploadAreaURN
from .exceptions import UploadException
from .s3_agent import S3Agent
from .api_client import ApiClient


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


def forget_area(uuid_or_alias):
    """
    Remove an area from our cache of upload areas.
    """
    matching_areas = UploadArea.areas_matching_alias(alias=uuid_or_alias)
    if len(matching_areas) == 0:
        raise UploadException("Sorry I don't recognize area \"%s\"" % (uuid_or_alias,))
    elif len(matching_areas) == 1:
        matching_areas[0].forget()
    else:
        raise UploadException("\"%s\" matches more than one area, please provide more characters." % (uuid_or_alias,))


def list_current_area():
    """
    Returns array of dicts describing the files in the currently selected Upload Area.
    """
    return list_area(UploadConfig().current_area)


def list_area(area_uuid):
    """
    Returns array of dicts describing the files in the Upload Area with the supplied UUID.
    """
    return UploadArea(uuid=area_uuid).list()


def list_areas():
    return [{'uuid': area.uuid, 'is_selected': area.is_selected} for area in UploadArea.all()]


def upload_file(file_path, target_filename=None, report_progress=False):
    """
    Upload a file to the currently selected Upload Area

    :param file_path: <string> Path to file on local filesystem.
    :param target_filename: <string> Rename file during upload (optional).
    :param report_progress: <bool> Display progress % during upload (optional).
    """
    upload_area = UploadArea(uuid=UploadConfig().current_area)
    file_s3_key = "%s/%s" % (upload_area.uuid, target_filename or os.path.basename(file_path))
    bucket_name = UploadConfig().bucket_name_template.format(deployment_stage=upload_area.urn.deployment_stage)
    content_type = 'application/json' if re.search('.json$', file_path) else 'hca-data-file'
    s3agent = S3Agent(aws_credentials=upload_area.urn.credentials)
    s3agent.upload_file(file_path, bucket_name, file_s3_key, content_type, report_progress=report_progress)
