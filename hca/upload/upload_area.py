import os
import re

from dcplib.media_types import DcpMediaType

from .api_client import ApiClient
from .credentials_manager import CredentialsManager
from .exceptions import UploadException
from .s3_agent import S3Agent
from .upload_config import UploadConfig
from .upload_area_uri import UploadAreaURI
from hca.util.pool import ThreadPool


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
        self.s3_agent = None

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

    def upload_files(self, file_paths, dcp_type="data", target_filename=None, use_transfer_acceleration=True,
                     report_progress=False):
        """
        A function that takes in a list of file paths and other optional args for parallel file upload
        """
        self._setup_s3_agent_for_file_upload(file_paths=file_paths, use_transfer_acceleration=use_transfer_acceleration)
        pool = ThreadPool()
        if report_progress:
            print("\nStarting upload of %s files to upload area %s" % (len(file_paths), self.uuid))
        for file_path in file_paths:
            pool.add_task(self._upload_file, file_path,
                          target_filename=target_filename,
                          use_transfer_acceleration=use_transfer_acceleration,
                          report_progress=report_progress)
        pool.wait_for_completion()
        if report_progress:
            number_of_errors = len(self.s3agent.failed_uploads)
            if number_of_errors == 0:
                print("Completed upload of %s files to upload area %s\n" % (self.s3agent.file_upload_completed_count, self.uuid))
            else:
                error = "\nThe following files failed:"
                for k, v in self.s3agent.failed_uploads.items():
                    error += "\n%s: [Exception] %s" % (k, v)
                error += "\nPlease retry or contact an hca administrator at data-help@humancellatlas.org for help.\n"
                raise UploadException(error)

    def _setup_s3_agent_for_file_upload(self, file_paths=[], use_transfer_acceleration=True):
        creds_provider = CredentialsManager(upload_area=self)
        self.s3agent = S3Agent(credentials_provider=creds_provider, transfer_acceleration=use_transfer_acceleration)
        file_size_sum = sum(os.path.getsize(path) for path in file_paths)
        file_count = len(file_paths)
        self.s3agent.set_s3_agent_variables_for_batch_file_upload(file_count=file_count, file_size_sum=file_size_sum)

    def _upload_file(self, file_path=None, dcp_type="data", target_filename=None, use_transfer_acceleration=True,
                     report_progress=False):
        try:
            file_s3_key = "%s/%s" % (self.uuid, target_filename or os.path.basename(file_path))
            content_type = str(DcpMediaType.from_file(file_path, dcp_type))
            self.s3agent.upload_file(file_path, self.uri.bucket_name, file_s3_key, content_type, report_progress=report_progress)
            self.s3agent.file_upload_completed_count += 1
            print("Download complete of %s to upload area %s" % (file_path, file_s3_key))
        except Exception as e:
            self.s3agent.failed_uploads[file_path] = e
