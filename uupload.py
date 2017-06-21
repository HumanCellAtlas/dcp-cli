#!/usr/bin/env python3.6

"""
Run "pip install crcmod python-magic boto3" to install this script's dependencies.
"""

import os, sys, hashlib, uuid, logging, argparse, mimetypes
from io import open

import boto3
from boto3.s3.transfer import TransferConfig

from checksumming_io.checksumming_io import ChecksummingBufferedReader, S3Etag

logging.basicConfig(level=logging.INFO)


def encode_tags(tags):
    return [dict(Key=k, Value=v) for k, v in tags.items()]


def upload_to_s3(args):
    """
    Upload files to s3.

    :param args: - args.files is a list of files or directories to upload.
                 - args.staging_bucket is the
    :return: a list of each file's unique key name.
    """
    tx_cfg = TransferConfig(multipart_threshold=S3Etag.etag_stride,
                            multipart_chunksize=S3Etag.etag_stride)
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(args.staging_bucket)
    key_names = []
    for raw_fh in args.files:
        with ChecksummingBufferedReader(raw_fh) as fh:
            key_name = "{}/{}".format(uuid.uuid4(), os.path.basename(fh.raw.name))
            bucket.upload_fileobj(fh, key_name, Config=tx_cfg)
            sums = fh.get_checksums()
            metadata = {
                "hca-dss-s3_etag": sums["s3_etag"],
                "hca-dss-sha1": sums["sha1"],
                "hca-dss-sha256": sums["sha256"],
                "hca-dss-crc32c": sums["crc32c"],
                "hca-dss-content-type": mimetypes.guess_type(fh.raw.name)[0]
            }
            s3.meta.client.put_object_tagging(Bucket=bucket.name,
                                              Key=key_name,
                                              Tagging=dict(TagSet=encode_tags(metadata))
                                              )
            key_names.append(key_name)
    return key_names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=lambda f: open(f, "rb"))
    parser.add_argument("--staging-bucket", default="hca-dcp-staging-test")
    args = parser.parse_args()
    print(args)
    key_names = upload_to_s3(args)
    for name in key_names:
        print(name)
