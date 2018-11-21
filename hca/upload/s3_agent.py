import os
import sys

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.credentials import CredentialResolver
from botocore.session import get_session
from tenacity import retry, wait_fixed, stop_after_attempt

from dcplib import s3_multipart

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
        self.s3 = my_session.resource('s3', config=config)

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
            sys.stdout.write("Completed %s/%s with %s of %s files remaining \r" % (sizeof_fmt(self.cumulative_bytes_transferred),
                                                                                   sizeof_fmt(self.file_size_sum),
                                                                                   files_remaining,
                                                                                   self.file_count))
            sys.stdout.flush()

    def should_write_to_terminal(self):
        write_to_terminal = False
        bytes_difference = self.cumulative_bytes_transferred - self.bytes_transferred_at_last_sys_write
        # Only write to terminal if have surpassed threshold since last message
        if float(bytes_difference) / float(self.file_size_sum) * 100 > WRITE_PERCENT_THRESHOLD:
            write_to_terminal = True
        return write_to_terminal

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    def upload_file(self, local_path, target_bucket, target_key, content_type, report_progress=False):
        file_size = os.path.getsize(local_path)
        bucket = self.s3.Bucket(target_bucket)
        obj = bucket.Object(target_key)
        upload_fileobj_args = {
            'ExtraArgs': {'ContentType': content_type, 'ACL': 'bucket-owner-full-control'},
            'Config': self.transfer_config(file_size)
        }
        if report_progress:
            upload_fileobj_args['Callback'] = self.upload_progress_callback
        with open(local_path, 'rb') as fh:
            obj.upload_fileobj(fh, **upload_fileobj_args)

    def list_bucket_by_page(self, bucket_name, key_prefix):
        paginator = self.s3.meta.client.get_paginator('list_objects')
        for page in paginator.paginate(Bucket=bucket_name, Prefix=key_prefix, PaginationConfig={'PageSize': 100}):
            if 'Contents' in page:
                yield [o['Key'] for o in page['Contents']]

    @classmethod
    def transfer_config(cls, file_size):
        return TransferConfig(multipart_threshold=s3_multipart.MULTIPART_THRESHOLD,
                              multipart_chunksize=s3_multipart.get_s3_multipart_chunk_size(file_size))
