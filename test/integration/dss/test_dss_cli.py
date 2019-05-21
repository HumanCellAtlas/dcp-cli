#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import filecmp
import json
import os
import sys
import unittest
import uuid
import tempfile
import shutil

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
import hca.cli
import hca.dss
from hca.util.compat import USING_PYTHON2
from test import CapturingIO, reset_tweak_changes, TEST_DIR

if USING_PYTHON2:
    import backports.tempfile
    tempfile = backports.tempfile


class TestDssCLI(unittest.TestCase):
    def test_post_search_cli(self):
        query = json.dumps({})
        replica = "aws"
        args = ["dss", "post-search", "--es-query", query, "--replica", replica, "--output-format", "raw"]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args)
        result = json.loads(stdout.captured())
        self.assertIn("results", result)

    def test_get_files_cli(self):
            try:
                filename = "SRR2967608_1.fastq.gz"
                dirpath = os.path.join(TEST_DIR, "res", "bundle")
                file_path = os.path.join(dirpath, filename)
                dest_dir = tempfile.mkdtemp(dir=os.getcwd(), prefix="cli-test-", suffix=".tmp")
                replica = "aws"
                staging_bucket = "org-humancellatlas-dss-cli-test"

                upload_args = ['dss', 'upload', '--src-dir', dirpath, '--replica', replica,
                               '--staging-bucket', staging_bucket]
                with CapturingIO('stdout') as stdout_upload:
                    hca.cli.main(args=upload_args)
                upload_res = json.loads(stdout_upload.captured())
                download_args = ['dss', 'download', '--bundle-uuid', upload_res['bundle_uuid'],
                                 '--replica', replica, '--download-dir', dest_dir]
                with CapturingIO('stdout'):
                    hca.cli.main(args=download_args)
                bundle_fqid = upload_res['bundle_uuid'] + '.' + upload_res['version']
                with open(os.path.join(dest_dir, bundle_fqid, filename), 'rb') as download_data:
                    download_content = download_data.read()
                with open(file_path, "rb") as bytes_fh:
                    file_content = bytes_fh.read()
                    self.assertEqual(file_content, download_content)
            finally:
                shutil.rmtree(dest_dir)

    @unittest.skipIf(True, "Manual Test")
    @reset_tweak_changes
    def test_remote_login(self):
        """Test that remote logins work for non-interactive systems
            0. Change the skipIf from True to False to allow invocation of test
            1. Follow the link provided by the test
            2. Paste the code value into the test env
            3. Confirm Results
        """
        args = ["dss", "login", "--remote"]
        hca.cli.main(args)
        self.assertTrue(hca.get_config().oauth2_token.access_token)
        args = ['dss', 'get-subscriptions', '--replica', 'aws']
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args)
        results = json.loads(stdout.captured())
        self.assertIn("subscriptions", results)

    @reset_tweak_changes
    def test_cli_login(self):
        """Test that the login command works with a dummy token"""
        access_token = "test_access_token"
        expected = "Storing access credentials\n"
        args = ["dss", "login", "--access-token", access_token]

        with CapturingIO('stdout') as stdout:
            hca.cli.main(args)

        self.assertEqual(stdout.captured(), expected)
        self.assertEqual(hca.get_config().oauth2_token.access_token, access_token)

    def test_json_input(self):
        """Ensure that adding JSON input works"""
        args = ["dss", "post-search", "--es-query", '{}', "--replica", "aws"]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args)

        self.assertEqual(json.loads(stdout.captured())["es_query"], {})

    def test_version_output(self):
        args = ["dss", "create-version"]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args=args)
        print(stdout.captured())
        self.assertTrue(stdout.captured())

    def test_collection_download(self):
        """
        Upload a bundle, add it to a collection, and try downloading
        that collection.

        If we download the lone bundle in the collection that we create,
        the same data should be downloaded.
        """
        dirpath = os.path.join(TEST_DIR, "res", "bundle")
        upload_args = ['dss', 'upload', '--src-dir', dirpath, '--replica', 'aws',
                       '--staging-bucket', 'org-humancellatlas-dss-cli-test']
        with CapturingIO('stdout') as stdout_upload:
            hca.cli.main(args=upload_args)
        bdl_res =  json.loads(stdout_upload.captured())
        col_contents = {
            'type': 'bundle',
            'uuid': bdl_res['bundle_uuid'],
            'version': bdl_res['version']
        }
        put_col_args = ['dss', 'put-collection', '--replica', 'aws', '--uuid',
                        str(uuid.uuid4()), '--description', '"test collection"',
                        '--details', '{}', '--version', bdl_res['version'],
                        '--contents', json.dumps(col_contents), '--name',
                        'collection_test:%s' % bdl_res['bundle_uuid']]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args=put_col_args)
        col_res = json.loads(stdout.captured())
        with tempfile.TemporaryDirectory() as t1:
            dl_col_args = ['dss', 'download-collection', '--uuid', col_res['uuid'],
                           '--replica', 'aws', '--download-dir', t1]
            hca.cli.main(args=dl_col_args)
            with tempfile.TemporaryDirectory() as t2:
                dl_bdl_args = ['dss', 'download', '--bundle-uuid',
                               bdl_res['bundle_uuid'], '--replica', 'aws',
                               '--download-dir', t2]
                hca.cli.main(args=dl_bdl_args)
                # Bundle download and collection download share the same backend,
                # so shallow check is sufficient.
                diff = filecmp.dircmp(t1, t2)
                # It would be more concise to say `self.assertFalse(diff.right_only
                # or diff.left_only or ...)` but writing it out the long way will
                # make troubleshooting a failure easier.
                self.assertFalse(diff.right_only)
                self.assertFalse(diff.left_only)
                self.assertFalse(diff.funny_files)
                self.assertFalse(diff.diff_files)


if __name__ == "__main__":
    unittest.main()
