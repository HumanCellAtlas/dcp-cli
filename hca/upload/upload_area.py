import mimetypes
import os
import re

from dcplib.media_types import DcpMediaType

from hca.util.pool import ThreadPool
from .lib.api_client import ApiClient
from .lib.client_side_checksum_handler import ClientSideChecksumHandler
from .lib.credentials_manager import CredentialsManager
from .exceptions import UploadException
from .lib.s3_agent import S3Agent
from .upload_area_uri import UploadAreaURI
from .upload_config import UploadConfig


class UploadArea:

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
        self.upload_api_client = ApiClient(self.uri.deployment_stage)

    def __str__(self):
        return "UploadArea {uri}".format(uri=self.uri)

    @property
    def deployment_stage(self):
        return self.uri.deployment_stage

    def get_credentials(self):
        """
        Return a set of credentials that may be used to access the Upload Area folder in the S3 bucket
        :return: a dict containing AWS credentials in a format suitable for passing to Boto3
            or if capitalized, used as environment variables
        """
        creds_mgr = CredentialsManager(self)
        creds = creds_mgr.get_credentials_from_upload_api()
        return {
            'aws_access_key_id': creds['access_key'],
            'aws_secret_access_key': creds['secret_key'],
            'aws_session_token': creds['token'],
            'expiry_time': creds['expiry_time']
        }

    def list(self, detail=False):
        """
        A generator that yields information about each file in the upload area
        :param detail: return detailed file information (slower)
        :return: a list of dicts containing at least 'name', or more of detail was requested
        """
        creds_provider = CredentialsManager(upload_area=self)
        s3agent = S3Agent(credentials_provider=creds_provider)
        key_prefix = self.uuid + "/"
        key_prefix_length = len(key_prefix)
        for page in s3agent.list_bucket_by_page(bucket_name=self.uri.bucket_name, key_prefix=key_prefix):
            file_list = [key[key_prefix_length:] for key in page]  # cut off upload-area-id/
            if detail:
                files_info = self.upload_api_client.files_info(self.uuid, file_list)
            else:
                files_info = [{'name': filename} for filename in file_list]
            for file_info in files_info:
                yield file_info

    def upload_files(self, file_paths, file_size_sum=0, dcp_type="data", target_filename=None,
                     use_transfer_acceleration=True, report_progress=False):
        """
        A function that takes in a list of file paths and other optional args for parallel file upload
        """
        self._setup_s3_agent_for_file_upload(file_count=len(file_paths),
                                             file_size_sum=file_size_sum,
                                             use_transfer_acceleration=use_transfer_acceleration)
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
                print(
                    "Completed upload of %d files to upload area %s\n" %
                    (self.s3agent.file_upload_completed_count, self.uuid))
            else:
                error = "\nThe following files failed:"
                for k, v in self.s3agent.failed_uploads.items():
                    error += "\n%s: [Exception] %s" % (k, v)
                error += "\nPlease retry or contact an hca administrator at data-help@humancellatlas.org for help.\n"
                raise UploadException(error)

    def _setup_s3_agent_for_file_upload(self, file_count=0, file_size_sum=0, use_transfer_acceleration=True):
        creds_provider = CredentialsManager(upload_area=self)
        self.s3agent = S3Agent(credentials_provider=creds_provider, transfer_acceleration=use_transfer_acceleration)
        self.s3agent.set_s3_agent_variables_for_batch_file_upload(file_count=file_count, file_size_sum=file_size_sum)

    def _determine_s3_file_content_type(self, file_path, dcp_type="data"):
        mime_type_tuple = mimetypes.guess_type(file_path)
        mime_type = "application/data"
        if mime_type_tuple[0]:
            mime_type = mime_type_tuple[0]
        elif mime_type_tuple[1] == "gzip":
            # If there is an encoding guess of gzip without a mimetype guess, set as application/gzip.
            mime_type = "application/gzip"
        content_type = "{0}; dcp-type={1}".format(mime_type, dcp_type)
        return content_type

    def _upload_file(self, file_path=None, dcp_type="data", target_filename=None, use_transfer_acceleration=True,
                     report_progress=False):
        try:
            target_bucket = self.uri.bucket_name
            if file_path.startswith("s3://"):
                file_name = file_path.split('/')[-1]
                target_key = "%s/%s" % (self.uuid, target_filename or file_name)
                content_type = self._determine_s3_file_content_type(file_path, dcp_type)
                self.s3agent.copy_s3_file(file_path, target_bucket, target_key, content_type,
                                          report_progress=report_progress)
            else:
                target_key = "%s/%s" % (self.uuid, target_filename or os.path.basename(file_path))
                content_type = str(DcpMediaType.from_file(file_path, dcp_type))
                checksum_handler = ClientSideChecksumHandler(file_path)
                checksum_handler.compute_checksum()
                checksums = checksum_handler.get_checksum_metadata_tag()
                self.s3agent.upload_local_file(file_path, target_bucket, target_key, content_type, checksums,
                                               report_progress=report_progress)
            self.s3agent.file_upload_completed_count += 1
            self.upload_api_client.file_upload_notification(self.uuid, target_filename or os.path.basename(file_path))
            print("Upload complete of %s to upload area %s" % (file_path, self.uri))
        except Exception as e:
            self.s3agent.failed_uploads[file_path] = e
