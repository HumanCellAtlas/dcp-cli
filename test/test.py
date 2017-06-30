#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import unittest
import pprint

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_root)

import hca


class TestHCACLI(unittest.TestCase):
    """Test the entire module."""

    def test_make_name(self):
        """Test make_name in parser.py."""
        http_method = "get"
        path_split = ["bundles"]
        self.assertEqual(
            hca.parser.make_name(http_method, path_split),
            "get-bundles"
        )

        path_split.append("cmd")
        self.assertEqual(
            hca.parser.make_name(http_method, path_split),
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
        self.assertEqual(hca.parser.index_parameters(None, params), {})

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
            hca.parser.index_parameters(None, params),
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
            hca.parser.index_parameters(None, params),
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
            }}
        )

    def test_parsing(self):
        """Test that the parser parses arguments correctly."""
        api = hca.define_api.API(True)

        args = ["put-files", "134", "--bundle-uuid", "asdf", "--creator-uid", "1", "--source-url", "sljdf.com"]
        out = {'source_url': 'sljdf.com', 'bundle_uuid': 'asdf', 'uuid': '134', 'creator_uid': 1}
        self.assertEqual(api.parse_args(args), out)

        args = ["put-files", "--bundle-uuid", "asdf", "--creator-uid", "1", "--source-url", "sljdf.com", "134"]
        self.assertEqual(api.parse_args(args), out)

        args = ["put-files", "--creator-uid", "1", "--source-url", "sljdf.com", "134"]
        self.assertRaises(SystemExit, api.parse_args, args)

        args = ["put-files", "--bundle-uuid", "asdf", "--creator-uid", "1", "--source-url", "sljdf.com"]
        self.assertRaises(SystemExit, api.parse_args, args)

        args = ["put-files", "--bundle-uuid", "--creator-uid", "1", "--source-url", "sljdf.com", "134"]
        self.assertRaises(SystemExit, api.parse_args, args)

        args = ["get-bundles"]
        out = {}
        self.assertEqual(api.parse_args(args), out)

        args = ["get-bundles", "uuid_arg"]
        out = {"uuid": "uuid_arg"}
        self.assertEqual(api.parse_args(args), out)

        args = ["get-bundles", "uuid_arg", "version_arg", "--replica", "rep"]
        out = {"uuid": "uuid_arg", "replica": "rep", "bundle_version": "version_arg"}
        self.assertEqual(api.parse_args(args), out)

        # Works for now but shouldn't in the future b/c --replica required when uuid and version specified.
        args = ["get-bundles", "uuid_arg", "version_arg"]
        out = {"uuid": "uuid_arg", "bundle_version": "version_arg"}
        self.assertEqual(api.parse_args(args), out)

        # Works for now. --replica isn't an option unless both uuid and version specified.
        args = ["get-bundles", "uuid_arg", "--replica", "rep"]
        out = {"uuid": "uuid_arg", "replica": "rep"}
        self.assertEqual(api.parse_args(args), out)

    def _get_first_url(self, response):
        """Get the first url we sent a request to if there were redirects."""
        if response.history:
            return response.history[0].url
        return response.url

    def test_requests(self):
        """Test that the parser parses arguments in the right way."""
        api = hca.define_api.API(True)

        args = ["get-bundles"]
        response = api.make_request(args)
        self.assertEqual(self._get_first_url(response), "https://hca-dss.czi.technology/v1/bundles")
        self.assertTrue(response.ok)

        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "--version", "1981-07-21T11:35:45+00:00", "--replica", "aws"]
        response = api.make_request(args)
        self.assertFalse(response.ok)  # The key is not in there

        # Works for now but shouldn't in the future b/c --replica required when uuid and version specified.
        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "version_arg"]
        response = api.make_request(args)
        self.assertEqual(
            self._get_first_url(response),
            "https://hca-dss.czi.technology/v1/bundles/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA/version_arg"
        )
        self.assertFalse(response.ok)

    def test_refs(self):
        """Test internal JSON reference resolution."""
        api = hca.define_api.API(True)
        args = ["put-reftest", "--name", "name", "--uuid", "uuid", "--versions", "item1", "item2"]
        out = {"name": "name", "uuid": "uuid", "versions": ["item1", "item2"]}
        self.assertEqual(api.parse_args(args), out)

    def test_array_cli(self):
        """Ensure that this framework can handle arrays."""
        api = hca.define_api.API(True)
        args = ["put-bundles", "uuid", "--version", "version", "--files", "uuid1/v1/n1/True", "uuid2/v2/n2/False", "--creator-uid", "3", "--replica", "rep"]
        out = {"uuid": "uuid", "version": "version", "files": ["uuid1/v1/n1/True", "uuid2/v2/n2/False"], "creator_uid": 3, "replica": "rep"}
        self.assertEqual(api.parse_args(args), out)

    def test_parsing_array_object_literals(self):
        api = hca.define_api.API(True)
        args = ["put-bundles", "234sf", "--files", "True/n1/u1/v1", "False/n2/u2/v2", "--replica" ,"rep", "--creator-uid", "8"]
        parsed_args = api.parse_args(args)
        out = {'files': [{'indexed': True, 'version': 'v1', 'uuid': 'u1', 'name': 'n1'}, {'indexed': False, 'version': 'v2', 'uuid': 'u2', 'name': 'n2'}], 'creator_uid': 8}
        query_payload, body_payload, header_payload = api._build_payloads("put-bundles", parsed_args)
        self.assertEqual(body_payload, out)

    def test_json_input(self):
        api = hca.define_api.API()
        args = ["post-search", "--query", '{"hello":"world", "goodbye":"earth"}']
        parsed_args = api.parse_args(args)
        out = {"query": {"hello": "world", "goodbye": "earth"}}
        self.assertEqual(out, parsed_args)

    def test_upload_files(self):

        pass
        # [(<_io.BufferedReader name='test/bundle/a.txt'>, '034a9842-1670-4e84-9991-b022eb2ebe66/a.txt'), (<_io.BufferedReader name='test/bundle/b.txt'>, '44b48f40-b94c-4fcc-8cd1-85449de7086e/b.txt'), (<_io.BufferedReader name='test/bundle/c.txt'>, '71129b9a-9320-4b47-8263-e1796702c2bb/c.txt')]






if __name__ == '__main__':
    unittest.main()
