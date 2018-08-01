import os
import sys

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.credentials import CredentialResolver
from botocore.session import get_session

from dcplib import s3_multipart


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

    CLEAR_TO_EOL = "\x1b[0K"

    def __init__(self, credentials_provider, transfer_acceleration=True):
        config = Config(s3={'use_accelerate_endpoint': True}) if transfer_acceleration else Config()
        botocore_session = get_session()
        botocore_session.register_component('credential_provider', CredentialResolver(providers=[credentials_provider]))
        my_session = boto3.Session(botocore_session=botocore_session)
        self.s3 = my_session.resource('s3', config=config)

    def upload_progress_callback(self, bytes_transferred):
        self.cumulative_bytes_transferred += bytes_transferred
        percent_complete = (self.cumulative_bytes_transferred * 100) / self.file_size
        sys.stdout.write("\r%s of %s transferred (%.0f%%)%s" %
                         (sizeof_fmt(self.cumulative_bytes_transferred),
                          sizeof_fmt(self.file_size),
                          percent_complete,
                          self.CLEAR_TO_EOL))
        sys.stdout.flush()

    def upload_file(self, local_path, target_bucket, target_key, content_type, report_progress=False):
        self.file_size = os.path.getsize(local_path)
        bucket = self.s3.Bucket(target_bucket)
        obj = bucket.Object(target_key)
        upload_fileobj_args = {
            'ExtraArgs': {'ContentType': content_type, 'ACL': 'bucket-owner-full-control'},
            'Config': self.transfer_config(self.file_size)
        }
        if report_progress:
            upload_fileobj_args['Callback'] = self.upload_progress_callback
        with open(local_path, 'rb') as fh:
            self.cumulative_bytes_transferred = 0
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
