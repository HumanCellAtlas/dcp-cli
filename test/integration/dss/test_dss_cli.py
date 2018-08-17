#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import sys
import unittest

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
        filename = "SRR2967608_1.fastq.gz"
        dirpath = os.path.join(TEST_DIR, "res", "bundle")
        file_path = os.path.join(dirpath, filename)

        replica = "aws"
        staging_bucket = "org-humancellatlas-dss-cli-test"
        client = hca.dss.DSSClient()
        response = client.upload(src_dir=dirpath, replica=replica, staging_bucket=staging_bucket)

        for f in response["files"]:
            print(f)
            if f["name"] == filename:
                file_uuid = f['uuid']
                break

        res = client.get_file(uuid=file_uuid, replica=replica)

        self.assertIsInstance(res, bytes)
        with open(file_path, "rb") as bytes_fh:
            file_content = bytes_fh.read()
            self.assertEqual(file_content, res)

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

    def test_cli_get_bundle(self):
        """Test that get_bundle() returns the same files that were uploaded"""
        client = hca.dss.DSSClient()
        bundle_path = os.path.join(TEST_DIR, "res", "bundle")
        replica = "aws"
        staging_bucket = "org-humancellatlas-dss-cli-test"

        response = client.upload(src_dir=bundle_path, replica=replica, staging_bucket=staging_bucket)
        bundle_uuid = response['bundle_uuid']
        args = ["dss", "get-bundle", "--uuid", bundle_uuid, "--replica", replica]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args)
        # Assert that each file uuid in the bundle is the same as before we uploaded it
        for i, f in enumerate(json.loads(stdout.captured())['bundle']['files']):
            self.assertEqual(f['uuid'], response['files'][i]['uuid'])

if __name__ == "__main__":
    unittest.main()
