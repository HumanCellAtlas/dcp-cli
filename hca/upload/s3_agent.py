import os
import sys

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.credentials import CredentialResolver
from botocore.session import get_session
from dcplib import s3_multipart
from tenacity import retry, wait_fixed, stop_after_attempt

WRITE_PERCENT_THRESHOLD = 0.1


def sizeof_fmt(num, suffix='B'):
    """
    Adapted from https://stackoverflow.com/a/1094933
    Re: precision - display enough decimals to show progress on a slow (<5 MB/s) Internet connection
    """
    precision = {'': 0, 'Ki': 0, 'Mi': 0, 'Gi': 3, 'Ti': 6, 'Pi': 9, 'Ei': 12, 'Zi': 15}

    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            format_string = "{number:.%df} {unit}{suffix}" % precision[unit]
            return format_string.format(number=num, unit=unit, suffix=suffix)
        num /= 1024.0
    return "%.18f %s%s" % (num, 'Yi', suffix)


class S3Agent:

    def __init__(self, credentials_provider, transfer_acceleration=True):
        config = Config(s3={'use_accelerate_endpoint': True}) if transfer_acceleration else Config()
        botocore_session = get_session()
        botocore_session.register_component('credential_provider', CredentialResolver(providers=[credentials_provider]))
        my_session = boto3.Session(botocore_session=botocore_session)
        self.target_s3 = my_session.resource('s3', config=config)
        self.source_s3_client = boto3.client('s3')

    def set_s3_agent_variables_for_batch_file_upload(self, file_count=0, file_size_sum=0):
        self.file_count = file_count
        self.file_size_sum = file_size_sum
        self.file_upload_completed_count = 0
        self.cumulative_bytes_transferred = 0
        self.bytes_transferred_at_last_sys_write = 0
        self.failed_uploads = {}

    def upload_progress_callback(self, bytes_transferred):
        self.cumulative_bytes_transferred += bytes_transferred
        files_remaining = self.file_count - self.file_upload_completed_count
        if self.should_write_to_terminal():
            self.bytes_transferred_at_last_sys_write = self.cumulative_bytes_transferred
            sys.stdout.write(
                "Completed %s/%s with %s of %s files remaining \r" % (sizeof_fmt(self.cumulative_bytes_transferred),
                                                                      sizeof_fmt(self.file_size_sum),
                                                                      files_remaining,
                                                                      self.file_count))
            sys.stdout.flush()

    def should_write_to_terminal(self):
        write_to_terminal = False
        bytes_difference = self.cumulative_bytes_transferred - self.bytes_transferred_at_last_sys_write
        # Only write to terminal if have surpassed threshold since last message
        if self.file_size_sum > 0 and float(bytes_difference) / float(
                self.file_size_sum) * 100 > WRITE_PERCENT_THRESHOLD:
            write_to_terminal = True
        return write_to_terminal

    @retry(reraise=True, wait=wait_fixed(2), stop=stop_after_attempt(3))
    def copy_s3_file(self, s3_path, target_bucket, target_key, content_type, checksums={}, report_progress=False):
        # Here we are using s3's managed copy to allow for s3 to s3 file upload
        # We override any original metadata or content types
        s3_path_split = s3_path.replace("s3://", "").split("/", 1)
        source_bucket = s3_path_split[0]
        source_key = s3_path_split[1]
        response = self.source_s3_client.head_object(Bucket=source_bucket, Key=source_key)
        file_size = response['ContentLength']
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }
        upload_args = {
            'CopySource': copy_source,
            'ExtraArgs': {
                'ContentType': content_type,
                'MetadataDirective': 'REPLACE',
                'ACL': 'bucket-owner-full-control',
                'Metadata': checksums
            },
            'Config': self.transfer_config(file_size),
            'SourceClient': self.source_s3_client,
            'Bucket': target_bucket,
            'Key': target_key
        }
        if report_progress:
            upload_args['Callback'] = self.upload_progress_callback
        self.target_s3.meta.client.copy(**upload_args)

    @retry(reraise=True, wait=wait_fixed(2), stop=stop_after_attempt(3))
    def upload_local_file(self, local_path, target_bucket, target_key, content_type, checksums, report_progress=False):
        file_size = os.path.getsize(local_path)
        bucket = self.target_s3.Bucket(target_bucket)
        obj = bucket.Object(target_key)
        upload_fileobj_args = {
            'ExtraArgs': {'ContentType': content_type, 'ACL': 'bucket-owner-full-control', 'Metadata': checksums},
            'Config': self.transfer_config(file_size)
        }
        if report_progress:
            upload_fileobj_args['Callback'] = self.upload_progress_callback
        with open(local_path, 'rb') as fh:
            obj.upload_fileobj(fh, **upload_fileobj_args)

    def list_bucket_by_page(self, bucket_name, key_prefix):
        paginator = self.target_s3.meta.client.get_paginator('list_objects')
        for page in paginator.paginate(Bucket=bucket_name, Prefix=key_prefix, PaginationConfig={'PageSize': 100}):
            if 'Contents' in page:
                yield [o['Key'] for o in page['Contents']]

    @classmethod
    def transfer_config(cls, file_size):
        return TransferConfig(multipart_threshold=s3_multipart.MULTIPART_THRESHOLD,
                              multipart_chunksize=s3_multipart.get_s3_multipart_chunk_size(file_size))
