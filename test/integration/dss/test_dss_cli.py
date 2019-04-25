#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import sys
import unittest
import tempfile
import shutil

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca
import hca.cli
import hca.dss
from test import CapturingIO, reset_tweak_changes, TEST_DIR


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

                with open(os.path.join(dest_dir, upload_res['bundle_uuid'], filename), 'rb') as download_data:
                    download_content = download_data.read()
                with open(file_path, "rb") as bytes_fh:
                    file_content = bytes_fh.read()
                    self.assertEqual(file_content, download_content)
            finally:
                shutil.rmtree(dest_dir)

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


if __name__ == "__main__":
    unittest.main()
