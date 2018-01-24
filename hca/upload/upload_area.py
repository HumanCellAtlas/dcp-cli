import os
import re

from dcplib.media_types import DcpMediaType

from .api_client import ApiClient
from .exceptions import UploadException
from .s3_agent import S3Agent
from .upload_config import UploadConfig
from .upload_area_urn import UploadAreaURN


class UploadArea:

    @classmethod
    def all(cls):
        return [cls(uuid=uuid) for uuid in UploadConfig().areas()]

    @classmethod
    def areas_matching_alias(cls, alias):
        return [cls(uuid=uuid) for uuid in UploadConfig().areas() if re.match(alias, uuid)]

    def __init__(self, **kwargs):
        """
        You must supply either a uuid or urn keyword argument.

        :param uuid: The UUID of an existing Upload Area that we know about.
        :param urn: An UploadAreaURN for a new area.
        """
        if 'uuid' in kwargs:
            self.uuid = kwargs['uuid']
            areas = UploadConfig().areas()
            if self.uuid not in areas:
                raise UploadException("I'm not aware of upload area \"%s\"" % self.uuid)
            self.urn = UploadAreaURN(areas[self.uuid])
        elif 'urn' in kwargs:
            self.urn = kwargs['urn']
            self.uuid = self.urn.uuid
            UploadConfig().add_area(self.urn)
        else:
            raise UploadException("You must provide a uuid or URN")

    @property
    def is_selected(self):
        return UploadConfig().current_area == self.uuid

    @property
    def unique_prefix(self):
        for prefix_len in range(1, len(self.uuid)):
            prefix = self.uuid[0:prefix_len]
            matches = UploadArea.areas_matching_alias(prefix)
            if len(matches) == 1:
                return prefix

    def select(self):
        config = UploadConfig()
        config.select_area(self.uuid)

    def forget(self):
        UploadConfig().forget_area(self.uuid)

    def list(self, detail=False):
        """
        A generator that yields information about each file in the upload area
        :param detail: return detailed file information (slower)
        :return: a list of dicts containing at least 'name', or more of detail was requested
        """
        upload_api_client = ApiClient(self.urn.deployment_stage)
        s3agent = S3Agent(aws_credentials=self.urn.credentials)
        key_prefix = self.uuid + "/"
        key_prefix_length = len(key_prefix)
        for page in s3agent.list_bucket_by_page(bucket_name=self._bucket_name(), key_prefix=key_prefix):
            file_list = [key[key_prefix_length:] for key in page]  # cut off upload-area-id/
            if detail:
                files_info = upload_api_client.files_info(self.uuid, file_list)
            else:
                files_info = [{'name': filename} for filename in file_list]
            for file_info in files_info:
                yield file_info

    def upload_file(self, file_path, dcp_type=None, target_filename=None, use_transfer_acceleration=True,
                    report_progress=False):
        file_s3_key = "%s/%s" % (self.uuid, target_filename or os.path.basename(file_path))
        content_type = str(DcpMediaType.from_file(file_path, dcp_type))
        s3agent = S3Agent(aws_credentials=self.urn.credentials, transfer_acceleration=use_transfer_acceleration)
        s3agent.upload_file(file_path, self._bucket_name(), file_s3_key, content_type, report_progress=report_progress)

    def _bucket_name(self):
        return UploadConfig().bucket_name_template.format(deployment_stage=self.urn.deployment_stage)
