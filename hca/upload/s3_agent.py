import os
import sys

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config

KB = 1024
MB = KB * KB


def sizeof_fmt(num, suffix='B'):
    """
    From https://stackoverflow.com/a/1094933
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%d %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


class S3Agent:

    CLEAR_TO_EOL = "\x1b[0K"

    def __init__(self, aws_credentials={}, transfer_acceleration=True):
        session = boto3.session.Session(**aws_credentials)
        config = Config(s3={'use_accelerate_endpoint': True}) if transfer_acceleration else Config()
        self.s3 = session.resource('s3', config=config)

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
        self.file_size = os.stat(local_path).st_size
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
        etag_stride = cls._s3_chunk_size(file_size)
        return TransferConfig(multipart_threshold=etag_stride,
                              multipart_chunksize=etag_stride)

    @staticmethod
    def _s3_chunk_size(file_size):
        if file_size <= 10000 * 64 * MB:
            return 64 * MB
        else:
            div = file_size // 10000
            if div * 10000 < file_size:
                div += 1
            return ((div + (MB - 1)) // MB) * MB
