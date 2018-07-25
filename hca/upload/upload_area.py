import os
import re

from six.moves.urllib.parse import urlparse

from dcplib.media_types import DcpMediaType

from .api_client import ApiClient
from .credentials_manager import CredentialsManager
from .exceptions import UploadException
from .s3_agent import S3Agent
from .upload_config import UploadConfig


class UploadAreaURI:

    """
    Upload area URIs take the form s3://<upload-bucket-prefix>-<deployment_stage>/<area_uuid>/

    e.g. s3://org-humancellatlas-upload-prod/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/
    """

    def __init__(self, uri):
        self.uri = uri
        self.parsed = urlparse(self.uri)

    def __str__(self):
        return self.uri

    @property
    def bucket_name(self):
        return self.parsed.netloc

    @property
    def deployment_stage(self):
        return self.bucket_name.split('-')[-1]

    @property
    def area_uuid(self):
        return self.parsed.path.split('/')[-2]


class UploadArea:

    @classmethod
    def all(cls):
        return [cls(uuid=uuid) for uuid in UploadConfig().areas.keys()]

    @classmethod
    def from_alias(cls, uuid_or_alias):
        matching_areas = UploadArea.areas_matching_alias(alias=uuid_or_alias)
        if len(matching_areas) == 0:
            raise UploadException("Sorry I don't recognize area \"%s\"" % (uuid_or_alias,))
        elif len(matching_areas) == 1:
            return matching_areas[0]
        else:
            raise UploadException(
                "\"%s\" matches more than one area, please provide more characters." % (uuid_or_alias,))

    @classmethod
    def areas_matching_alias(cls, alias):
        return [cls(uuid=uuid) for uuid in UploadConfig().areas if re.match(alias, uuid)]

    def __init__(self, **kwargs):
        """
        You must supply either a uuid or uri keyword argument.

        :param uuid: The UUID of an existing Upload Area that we know about.
        :param uri: A URI for a new area.
        """
        if 'uuid' in kwargs:
            uuid = kwargs['uuid']
            areas = UploadConfig().areas
            if uuid not in areas:
                raise UploadException("I'm not aware of upload area \"%s\"" % uuid)
            self.uri = UploadAreaURI(areas[uuid]['uri'])
        elif 'uri' in kwargs:
            self.uri = UploadAreaURI(kwargs['uri'])
            UploadConfig().add_area(self.uri)
        else:
            raise UploadException("You must provide a uuid or URI")
        self.uuid = self.uri.area_uuid

    def __str__(self):
        return "UploadArea {uri}".format(uri=self.uri)

    @property
    def deployment_stage(self):
        return self.uri.deployment_stage

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
        upload_api_client = ApiClient(self.uri.deployment_stage)
        creds_provider = CredentialsManager(upload_area=self)
        s3agent = S3Agent(credentials_provider=creds_provider)
        key_prefix = self.uuid + "/"
        key_prefix_length = len(key_prefix)
        for page in s3agent.list_bucket_by_page(bucket_name=self.uri.bucket_name, key_prefix=key_prefix):
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
        creds_provider = CredentialsManager(upload_area=self)
        s3agent = S3Agent(credentials_provider=creds_provider, transfer_acceleration=use_transfer_acceleration)
        s3agent.upload_file(file_path, self.uri.bucket_name, file_s3_key, content_type, report_progress=report_progress)
