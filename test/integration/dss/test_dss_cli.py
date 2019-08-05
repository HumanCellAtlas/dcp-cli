#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import contextlib
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
import hca.util.exceptions
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
        with tempfile.TemporaryDirectory(prefix='cli-test-', suffix='.tmp',
                                         dir=os.getcwd()) as dest_dir, \
             self._put_test_bdl() as upload_res:
            filename = "SRR2967608_1.fastq.gz"
            file_path = os.path.join(TEST_DIR, 'res', 'bundle', filename)
            download_args = ['dss', 'download', '--bundle-uuid', upload_res['bundle_uuid'],
                             '--replica', 'aws', '--download-dir', dest_dir]
            with CapturingIO('stdout'):
                hca.cli.main(args=download_args)
            bundle_fqid = upload_res['bundle_uuid'] + '.' + upload_res['version']
            with open(os.path.join(dest_dir, bundle_fqid, filename), 'rb') as download_data:
                download_content = download_data.read()
            with open(file_path, 'rb') as bytes_fh:
                self.assertEqual(bytes_fh.read(), download_content)

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

    @staticmethod
    @contextlib.contextmanager
    def _put_test_col(args, uuid=str(uuid.uuid4()), replica='aws'):
        """
        Implements a context manager that PUTs a collection to the
        data store using `hca dss put-collection` then deletes it
        when done.

        :param list args: arguments to pass to `hca dss put-collection`
        :param str uuid: uuid of the collection
        :param str replica: replica to use
        :rtype: dict
        :returns: put-collection response object
        """
        base_args = ['dss', 'put-collection', '--replica', replica,
                     '--uuid', uuid]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args=base_args + args)
        yield json.loads(stdout.captured())
        base_args[1] = 'delete-collection'
        with CapturingIO('stdout'):
            hca.cli.main(args=base_args)

    @staticmethod
    @contextlib.contextmanager
    def _put_test_bdl(dirpath=os.path.join(TEST_DIR, 'res', 'bundle'),
                      replica='aws',
                      staging_bucket='org-humancellatlas-dss-cli-test'):
        """
        Implements a context manager that uploads a bundle to the data
        store using `hca dss upload` then deletes it when done, if the
        user has the requisite permissions.

        :param str dirpath: path of the directory to upload (`--src-dir`)
        :param str replica: replica to use (`--replica`)
        :param str staging_bucket`: passed to `--staging-bucket`
        :rtype: dict
        :returns: upload response object
        """
        put_args  = ['dss', 'upload', '--src-dir', dirpath, '--replica',
                     replica, '--staging-bucket', staging_bucket]
        with CapturingIO('stdout') as stdout:
            hca.cli.main(args=put_args)
        rv = json.loads(stdout.captured())
        yield rv
        del_args = ['dss', 'delete-bundle', '--uuid', rv['bundle_uuid'],
                    '--replica', replica, '--reason', 'tear down test bundle']
        try:
            with CapturingIO('stdout'):
                hca.cli.main(args=del_args)
        except hca.util.exceptions.SwaggerAPIException as e:
            # Deleting bundles is a privilege, not a right
            assert e.code == 403

    @unittest.skipIf(os.name is 'nt', 'Unable to test on Windows')  # TODO windows testing refactor
    def test_collection_download(self):
        """
        Upload a bundle, add it to a collection, and try downloading
        that collection.

        If we download the lone bundle in the collection that we create,
        the same data should be downloaded.
        """
        with self._put_test_bdl() as bdl:
            col_contents = {
                'type': 'bundle',
                'uuid': bdl['bundle_uuid'],
                'version': bdl['version']
            }
            put_col_args = [
                '--description', '"test collection"',
                '--details', '{}',
                '--version', bdl['version'],
                '--contents', json.dumps(col_contents),
                '--name', 'collection_test:%s' % bdl['bundle_uuid']
            ]
            with self._put_test_col(put_col_args) as col, \
                 tempfile.TemporaryDirectory() as t1, \
                 tempfile.TemporaryDirectory() as t2:
                dl_col_args = ['dss', 'download-collection', '--uuid', col['uuid'],
                               '--replica', 'aws', '--download-dir', t1]
                hca.cli.main(args=dl_col_args)
                dl_bdl_args = ['dss', 'download', '--bundle-uuid',
                               bdl['bundle_uuid'], '--replica', 'aws',
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
