#!/usr/bin/env python
# coding: utf-8

import io
import os
import sys
import tempfile
import unittest
import uuid

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.dss
from hca.util.compat import USING_PYTHON2
from hca.dss import upload_to_cloud

if USING_PYTHON2:
    import backports.tempfile
    TemporaryDirectory = backports.tempfile.TemporaryDirectory
else:
    TemporaryDirectory = tempfile.TemporaryDirectory


class TestDssApiRetry(unittest.TestCase):
    staging_bucket = "org-humancellatlas-dss-cli-test"
    source_url = None

    @classmethod
    def setUpClass(cls):
        with TemporaryDirectory() as src_dir:
            bundle_path = os.path.join(src_dir, "bundle")
            os.makedirs(bundle_path)
            hello_world_path = os.path.join(bundle_path, "hello_world")

            with io.open(hello_world_path, "wb+") as fh:
                fh.write(b"HELLO WORLD")
                fh.flush()
                fh.seek(0)
                _, uploaded_keys = upload_to_cloud(
                    [fh],
                    staging_bucket=TestDssApiRetry.staging_bucket,
                    replica="aws",
                    from_cloud=False,
                )

            TestDssApiRetry.source_url = "s3://{}/{}".format(TestDssApiRetry.staging_bucket, uploaded_keys[0])

    def test_get_retry(self):
        """
        Test that GET methods are retried.  We instruct the server to fake a 504 with some probability, and we should
        retry until successful.
        """
        client = hca.dss.DSSClient()
        file_uuid = str(uuid.uuid4())
        creator_uid = client.config.get("creator_uid", 0)

        client.put_file._request(
            dict(
                uuid=file_uuid,
                bundle_uuid=str(uuid.uuid4()),
                creator_uid=creator_uid,
                source_url=TestDssApiRetry.source_url,
            ),
        )
        client.get_file._request(
            dict(
                uuid=file_uuid,
                replica="aws",
            ),
            headers={
                'DSS_FAKE_504_PROBABILITY': "0.5",
            },
        )


if __name__ == '__main__':
    unittest.main()
