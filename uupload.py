#!/usr/bin/env python3.6

"""
Run "pip install crcmod python-magic" to install this script's dependencies.
"""

import os, sys, hashlib, uuid, logging, argparse
from io import BufferedRandom, BufferedReader

import crcmod
import magic
import boto3
from boto3.s3.transfer import TransferConfig

logging.basicConfig(level=logging.INFO)

class MetadataReader(BufferedReader):
    etag_stride = 64 * 1024 * 1024

    def __init__(self, *args, **kwargs):
        self._hashers = dict(crc32c=crcmod.predefined.Crc("crc-32c"),
                             sha1=hashlib.sha1(),
                             sha256=hashlib.sha256())
        self._etag_bytes = 0
        self._etag_parts = []
        self._etag_hasher = hashlib.md5()
        self._mime_type = None
        BufferedReader.__init__(self, *args, **kwargs)

    def read(self, size=None):
        chunk = BufferedReader.read(self, size)
        if not self._mime_type:
            self._mime_type = magic.from_buffer(chunk, mime=True)
        if self._etag_bytes + len(chunk) > self.etag_stride:
            chunk_head = chunk[:self.etag_stride - self._etag_bytes]
            chunk_tail = chunk[self.etag_stride - self._etag_bytes:]
            self._etag_hasher.update(chunk_head)
            self._etag_parts.append(self._etag_hasher.digest())
            self._etag_hasher = hashlib.md5()
            self._etag_hasher.update(chunk_tail)
            self._etag_bytes = len(chunk_tail)
        else:
            self._etag_hasher.update(chunk)
            self._etag_bytes += len(chunk)

        for hasher in self._hashers.values():
            hasher.update(chunk)
        return chunk

    def get_metadata(self):
        if self._etag_bytes:
            self._etag_parts.append(self._etag_hasher.digest())
            self._etag_bytes = 0
        metadata = {"hca-dss-content-type": self._mime_type}
        if len(self._etag_parts) > 1:
            etag_csum = hashlib.md5(b"".join(self._etag_parts)).hexdigest()
            metadata["hca-dss-etag"] = '"{}-{}"'.format(etag_csum, len(self._etag_parts))
        else:
            metadata["hca-dss-etag"] = self._etag_hasher.hexdigest()

        metadata.update({"hca-dss-{}".format(name): hasher.hexdigest() for name, hasher in self._hashers.items()})
        return metadata

def encode_tags(tags):
    return [dict(Key=k, Value=v) for k, v in tags.items()]

parser = argparse.ArgumentParser()
parser.add_argument("files", type=argparse.FileType("rb"), nargs="+")
parser.add_argument("--staging-bucket", default="hca-dcp-staging-test")
args = parser.parse_args()

tx_cfg = TransferConfig(multipart_threshold=MetadataReader.etag_stride,
                        multipart_chunksize=MetadataReader.etag_stride)
s3 = boto3.resource("s3")
bucket = s3.Bucket(args.staging_bucket)
for raw_fh in args.files:
    with MetadataReader(raw_fh) as fh:
        key_name = "{}/{}".format(uuid.uuid4(), os.path.basename(fh.raw.name))
        bucket.upload_fileobj(fh, key_name, Config=tx_cfg)
        metadata = fh.get_metadata()
        s3.meta.client.put_object_tagging(Bucket=bucket.name, Key=key_name, Tagging=dict(TagSet=encode_tags(metadata)))
        print(key_name)
