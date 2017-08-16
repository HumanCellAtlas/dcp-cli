#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import filecmp
import os
import shutil
import sys
import unittest
import uuid
import pprint
from six.moves import reload_module
from io import open

import requests
import six

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_root)

from hca import api
from hca import regenerate_api  # noqa
from hca import constants  # noqa
from test.config import override_oauth_config  # noqa


class TestHCACLI(unittest.TestCase):
    """Test the entire module."""

    def test_make_name(self):
        """Test make_name in parser.py."""
        http_method = "get"
        path_split = ["bundles"]
        self.assertEqual(
            regenerate_api._make_name(http_method, path_split),
            "get-bundles"
        )

        path_split.append("cmd")
        self.assertEqual(
            regenerate_api._make_name(http_method, path_split),
            "get-bundles-cmd"
        )

    def test_index_parameters(self):
        """Test index_parameters in parser.py."""
        self.maxDiff = None

        params = {
            "description": "Returns a list of bundles matching given criteria.\n",
            "responses": {
              "200": {
                "description": "OK",
                "schema": {
                  "properties": {
                    "bundles": {
                      "items": {
                        "$ref": "#/definitions/Bundle"
                      },
                      "type": "array"
                    }
                  },
                  "required": [
                    "bundles"
                  ],
                  "type": "object"
                }
              }
            },
            "summary": "Query bundles"
        }
        self.assertEqual(regenerate_api.index_parameters(None, params), {})

        params["parameters"] = [
            {
                "description": "Bundle unique ID.",
                "in": "path",
                "name": "uuid",
                "required": True,
                "type": "string",
            }
        ]
        self.assertEqual(
            regenerate_api.index_parameters(None, params),
            {"uuid": {
                "description": "Bundle unique ID.",
                "in": "path",
                "name": "uuid",
                "required": True,
                "type": "string",
                "array": False,
                'req': True,
                'hierarchy': ['uuid']
            }})

        params['parameters'] = [{
            "in": "body",
            "name": "extras",
            "required": True,
            "schema": {
              "properties": {
                "bundle_uuid": {
                  "description": "A RFC4122-compliant ID.",
                  "type": "string"
                },
                "timestamp": {
                  "description": "Timestamp of file creation in RFC3339.",
                  "format": "date-time",
                  "type": "string"
                }
              },
              "required": [
                "bundle_uuid",
              ],
              "type": "object"
            }
          }
        ]
        self.assertEqual(
            regenerate_api.index_parameters(None, params),
            {"timestamp": {
                "description": "Timestamp of file creation in RFC3339.",
                "in": "body",
                "name": "timestamp",
                "type": "string",
                "format": "date-time",
                "array": False,
                'req': False,
                'hierarchy': ['timestamp']
            },
            "bundle_uuid": {
                "description": "A RFC4122-compliant ID.",
                "in": "body",
                "name": "bundle_uuid",
                "type": "string",
                "array": False,
                'req': True,
                'hierarchy': ['bundle_uuid']
            },
            'top_level_body_params': {
                "timestamp": {
                    "description": "Timestamp of file creation in RFC3339.",
                    "in": "body",
                    "name": "timestamp",
                    "type": "string",
                    "format": "date-time",
                    "array": False,
                    'req': False,
                    'hierarchy': ['timestamp']
                },
                "bundle_uuid": {
                    "description": "A RFC4122-compliant ID.",
                    "in": "body",
                    "name": "bundle_uuid",
                    "type": "string",
                    "array": False,
                    'req': True,
                    'hierarchy': ['bundle_uuid']
            }}}
        )

    def test_get_files_cli(self):
        """Testing 2 things: 1. Printing bytes to stdout; 2. Iterative content download."""
        import subprocess

        dirpath = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dirpath, "bundle", "SRR2967608_1.fastq.gz")

        self.assertGreater(os.stat(file_path).st_size, constants.Constants.CHUNK_SIZE)

        args = {'file_or_dir': [file_path],
                'replica': "aws",
                'staging_bucket': "org-humancellatlas-dss-cli-test"}
        response = api.upload(**args)

        file_uuid = response['files'][0]['uuid']

        process = subprocess.Popen(["hca", "get-files", file_uuid, "--replica", "aws"], stdout=subprocess.PIPE)
        out, _ = process.communicate()
        self.assertIsInstance(out, bytes)
        with open(file_path, "rb") as bytes_fh:
            file_content = bytes_fh.read()
        self.assertEqual(file_content, out)

    def test_parsing(self):
        """Test that the parser parses arguments correctly."""
        import hca.cli
        import hca.error

        cli = hca.cli.CLI(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.json"))

        args = ["put-files", "134", "--bundle-uuid", "asdf", "--creator-uid", "1", "--source-url", "sljdf.com"]
        out = {'source_url': 'sljdf.com', 'bundle_uuid': 'asdf', 'uuid': '134', 'creator_uid': 1}
        self.assertEqual(cli.parse_args(args), out)

        args = ["put-files", "--bundle-uuid", "asdf", "--creator-uid", "1", "--source-url", "sljdf.com", "134"]
        self.assertEqual(cli.parse_args(args), out)

        args = ["put-files", "--creator-uid", "1", "--source-url", "sljdf.com", "134"]
        self.assertRaises(hca.error.PrintingException, cli.parse_args, args)

        args = ["put-files", "--bundle-uuid", "asdf", "--creator-uid", "1", "--source-url", "sljdf.com"]
        self.assertRaises(hca.error.PrintingException, cli.parse_args, args)

        args = ["put-files", "--bundle-uuid", "--creator-uid", "1", "--source-url", "sljdf.com", "134"]
        self.assertRaises(hca.error.PrintingException, cli.parse_args, args)

        args = ["get-bundles", "uuid_arg"]
        out = {"uuid": "uuid_arg"}
        self.assertEqual(cli.parse_args(args), out)

        args = ["get-bundles", "uuid_arg", "--version", "version_arg", "--replica", "rep"]
        out = {"uuid": "uuid_arg", "replica": "rep", "version": "version_arg"}
        self.assertEqual(cli.parse_args(args), out)

        # Works for now but shouldn't in the future b/c --replica required when uuid and version specified.
        args = ["get-bundles", "uuid_arg", "--version", "version_arg"]
        out = {"uuid": "uuid_arg", "version": "version_arg"}
        self.assertEqual(cli.parse_args(args), out)

        # Works for now. --replica isn't an option unless both uuid and version specified.
        args = ["get-bundles", "uuid_arg", "--replica", "rep"]
        out = {"uuid": "uuid_arg", "replica": "rep"}
        self.assertEqual(cli.parse_args(args), out)

    def test_cli_printing(self):
        import hca.cli
        cli = hca.cli.CLI()
        string = str if six.PY3 else basestring

        # No args given
        request = cli.make_request([])
        self.assertIsInstance(request, string)

        # Base parser help
        request = cli.make_request(["-h"])
        self.assertIsInstance(request, string)

        # Endpoint parser help
        request = cli.make_request(["put-bundles", "-h"])
        self.assertIsInstance(request, string)

        # Base args given incorrectly
        request = cli.make_request(["idontbelonghere"])
        self.assertIsInstance(request, string)

        # Endpoint args given incorrectly
        request = cli.make_request(["put-bundles", "idontbelonghere"])
        self.assertIsInstance(request, string)

    def _get_first_url(self, response):
        """Get the first url we sent a request to if there were redirects."""
        if response.history:
            return response.history[0].url
        return response.url

    def test_requests(self):
        """Test that the parser parses arguments in the right way."""
        import hca.cli

        cli = hca.cli.CLI(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.json"))

        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "--version", "1981-07-21T11:35:45+00:00", "--replica", "aws"]
        response = cli.make_request(args)
        self.assertFalse(response.ok)  # The key is not in there

        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "--version", "version_arg"]
        response = cli.make_request(args)
        self.assertEqual(
            self._get_first_url(response),
            "https://hca-dss.czi.technology/v1/bundles/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA?version=version_arg"
        )
        self.assertFalse(response.ok)

    @unittest.skip("We don't generate bindings from test files right now and there are no references in " +
                   "the path parameters of our swagger spec. Need to refactor this test.")
    def test_refs(self):
        """Test internal JSON reference resolution."""
        cli = hca.cli.CLI(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.json"))
        args = ["put-reftest", "--name", "name", "--uuid", "uuid", "--versions", "item1", "item2"]
        out = {"name": "name", "uuid": "uuid", "versions": ["item1", "item2"]}
        self.assertEqual(cli.parse_args(args), out)

    def test_cli_login(self):
        from tweak import Config
        import hca.cli

        cli = hca.cli.CLI()

        access_token = "test_access_token"
        out = {'completed': True}
        args = ["login", "--access-token", access_token]

        with override_oauth_config():
            response = cli.make_request(args)
            config = Config(constants.Constants.TWEAK_PROJECT_NAME)

            self.assertEqual(response, out)
            self.assertEqual(config.access_token, access_token)

    def test_array_cli(self):
        """Ensure that this framework can handle arrays."""
        import hca.cli

        cli = hca.cli.CLI(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.json"))
        args = ["put-bundles", "uuid", "--version", "version", "--files", "uuid1/v1/n1/True", "uuid2/v2/n2/False", "--creator-uid", "3", "--replica", "rep"]
        out = {"uuid": "uuid", "version": "version", "files": ["uuid1/v1/n1/True", "uuid2/v2/n2/False"], "creator_uid": 3, "replica": "rep"}
        self.assertEqual(cli.parse_args(args), out)

    def test_parsing_array_object_literals(self):
        """Make sure that parsing literals works within an array object."""
        import hca.cli
        from hca.api.autogenerated.put_bundles import PutBundles  # noqa

        cli = hca.cli.CLI(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.json"))
        args = ["put-bundles", "234sf", "--files", "True/n1/u1/v1", "False/n2/u2/v2", "--replica" ,"rep", "--creator-uid", "8"]
        parsed_args = cli.parse_args(args)
        out = {'files': [{'indexed': True, 'version': 'v1', 'uuid': 'u1', 'name': 'n1'}, {'indexed': False, 'version': 'v2', 'uuid': 'u2', 'name': 'n2'}], 'creator_uid': 8}
        body_payload = PutBundles._build_body_payload(parsed_args)
        self.assertEqual(body_payload, out)

    @unittest.skip("This doesn't work because https://github.com/HumanCellAtlas/data-store/pull/167 not merged yet.")
    def test_json_input(self):
        """Ensure that adding json input works."""
        cli = hca.cli.CLI()
        args = ["post-search", "--query", '{"hello":"world", "goodbye":"earth"}']
        parsed_args = cli.parse_args(args)
        out = {"query": {"hello": "world", "goodbye": "earth"}}
        self.assertEqual(out, parsed_args)

    @unittest.skip("The bundle referenced in this test is no longer in place. Plans to set up an upload bundle")
    def test_upload_to_cloud_from_s3(self):
        uuids, names = hca.upload_to_cloud.upload_to_cloud(
            ["s3://hca-dss-test-src/data-bundles-examples/import/10x/pbmc8k/bundles/bundle1/"],
            "pointless-staging-bucket",
            "aws",
            True
        )
        out = [
            "data-bundles-examples/import/10x/pbmc8k/bundles/bundle1/assay.json",
            "data-bundles-examples/import/10x/pbmc8k/bundles/bundle1/project.json",
            "data-bundles-examples/import/10x/pbmc8k/bundles/bundle1/sample.json"
        ]
        self.assertEqual(len(uuids), len(names))
        assert_list_items_equal = (self.assertCountEqual if six.PY3
                                   else self.assertItemsEqual)
        assert_list_items_equal(names, out)

    def test_python_upload_download(self):
        dirpath = os.path.dirname(os.path.realpath(__file__))
        bundle_path = os.path.join(dirpath, "bundle")

        namespace = {'file_or_dir': [bundle_path],
                     'replica': "aws",
                     'staging_bucket': "org-humancellatlas-dss-cli-test"}

        bundle_output = api.upload(**namespace)

        downloaded_path = os.path.join(dirpath, "TestDownload")
        api.download(bundle_output['bundle_uuid'], name=downloaded_path)

        # Check that contents are the same
        for file in os.listdir(bundle_path):
            uploaded_file = os.path.join(bundle_path, file)
            downloaded_file = os.path.join(downloaded_path, file)
            self.assertTrue(filecmp.cmp(uploaded_file, downloaded_file, False))

        if os.path.exists(downloaded_path):
            shutil.rmtree(downloaded_path)

    def test_python_bindings(self):
        dirpath = os.path.dirname(os.path.realpath(__file__))
        bundle_path = os.path.join(dirpath, "bundle")
        staging_bucket = "org-humancellatlas-dss-cli-test"
        namespace = {'file_or_dir': [bundle_path],
                     'replica': "aws",
                     'staging_bucket': "org-humancellatlas-dss-cli-test"}

        bundle_output = api.upload(**namespace)

        api.download(bundle_output['bundle_uuid'], name=os.path.join(dirpath, "TestDownload"))

        # Test get-files and head-files
        file_ = bundle_output['files'][0]
        self.assertTrue(api.get_files(file_['uuid'], replica="aws").ok)
        self.assertTrue(api.head_files(file_['uuid']).ok)

        # Test get-bundles
        bundle_uuid = bundle_output['bundle_uuid']
        self.assertTrue(api.get_bundles(bundle_uuid, replica="aws").ok)

        # Test put-files
        file_uuid = str(uuid.uuid4())
        bundle_uuid = str(uuid.uuid4())
        source_url = "s3://{}/{}/{}".format(staging_bucket, file_['uuid'], file_['name'])
        self.assertTrue(api.put_files(file_uuid, creator_uid=1, bundle_uuid=bundle_uuid, source_url=source_url).ok)

        # Test put-bundles
        files = [{'indexed': True,
                  'name': file_['name'],
                  'uuid': file_['uuid'],
                  'version': file_['version']}]
        resp = api.put_bundles(bundle_uuid, files=files, creator_uid=1, replica="aws")
        self.assertTrue(resp.ok)

    def test_python_api_url(self):
        kwargs = {'uuid': "fake_uuid",
                  'replica': "aws",
                  'api_url': "https://thisisafakeurljslfjlshsfs.com"}
        self.assertRaises(requests.exceptions.ConnectionError,
                          api.get_files,
                          **kwargs)

    def test_python_subscriptions(self):
        query = {'bool': {}}
        resp = api.put_subscriptions(query=query, callback_url="www.example.com", replica="aws")
        subscription_uuid = resp.json()['uuid']

        self.assertEqual(201, resp.status_code)
        self.assertIn('uuid', resp.json())

        resp = api.get_subscriptions("aws")
        self.assertEqual(200, resp.status_code)
        self.assertTrue(subscription_uuid in [s['uuid'] for s in resp.json()['subscriptions']])

        resp = api.get_subscriptions(replica="aws", uuid=subscription_uuid)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(subscription_uuid, resp.json()['uuid'])

        resp = api.delete_subscriptions(uuid=subscription_uuid, replica="aws")
        self.assertEqual(200, resp.status_code)
        self.assertIn('timeDeleted', resp.json())

        resp = api.get_subscriptions("aws", uuid=subscription_uuid)
        self.assertEqual(404, resp.status_code)

    def test_python_login(self):
        from tweak import Config

        access_token = "test_access_token"
        out = {'completed': True}

        with override_oauth_config():
            login = api.login(access_token=access_token)
            config = Config(constants.Constants.TWEAK_PROJECT_NAME)

            self.assertEqual(login, out)
            self.assertEqual(config.access_token, access_token)


if __name__ == '__main__':
    unittest.main()
