#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, unittest, tempfile, json, subprocess, pprint

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
                'req': True
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
        pprint.pprint(hca.parser.index_parameters(None, params))
        self.assertEqual(
            hca.parser.index_parameters(None, params),
            {"extras-timestamp": {
                "description": "Timestamp of file creation in RFC3339.",
                "in": "body",
                "name": "extras-timestamp",
                "type": "string",
                "format": "date-time", 
                "array": False,
                'req': False
            },
            "extras-bundle_uuid": {
                "description": "A RFC4122-compliant ID.",
                "in": "body",
                "name": "extras-bundle_uuid",
                "type": "string",
                "array": False,
                'req': True
            }}
        )

    def test_parsing(self):
        """Test that the parser parses arguments correctly."""
        api = hca.define_api.API("url", "user")

        args = ["put-files", "134", "--extras-bundle_uuid", "asdf", "--extras-creator_uid", "sdf", "--extras-source_url", "sljdf.com"]
        out = {'extras_source_url': 'sljdf.com', 'extras_bundle_uuid': 'asdf', 'uuid': '134', 'extras_creator_uid': 'sdf'}
        self.assertEqual(api.parse_args(args), out)

        args = ["put-files", "--extras-bundle_uuid", "asdf", "--extras-creator_uid", "sdf", "--extras-source_url", "sljdf.com", "134"]
        self.assertEqual(api.parse_args(args), out)

        args = ["put-files", "--extras-creator_uid", "sdf", "--extras-source_url", "sljdf.com", "134"]
        self.assertRaises(SystemExit, api.parse_args, args)

        args = ["put-files", "--extras-bundle_uuid", "asdf", "--extras-creator_uid", "sdf", "--extras-source_url", "sljdf.com"]
        self.assertRaises(SystemExit, api.parse_args, args)

        args = ["put-files", "--extras-bundle_uuid", "--extras-creator_uid", "sdf", "--extras-source_url", "sljdf.com", "134"]
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
        api = hca.define_api.API("user", "password")

        args = ["get-bundles"]
        response = api.make_request(args)
        self.assertEqual(self._get_first_url(response), "https://hca-dss.czi.technology/v1/bundles")
        self.assertTrue(response.ok)

        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"]
        response = api.make_request(args)
        self.assertEqual(self._get_first_url(response), "https://hca-dss.czi.technology/v1/bundles/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA")
        self.assertTrue(response.ok)

        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "version_arg", "--replica", "rep"]
        response = api.make_request(args)
        self.assertEqual(self._get_first_url(response), "https://hca-dss.czi.technology/v1/bundles/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA/version_arg?replica=rep")
        self.assertTrue(response.ok)

        # Works for now but shouldn't in the future b/c --replica required when uuid and version specified.
        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "version_arg"]
        response = api.make_request(args)
        self.assertEqual(self._get_first_url(response), "https://hca-dss.czi.technology/v1/bundles/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA/version_arg")
        self.assertFalse(response.ok)

        # Works for now. --replica isn't an option unless both uuid and version specified.
        args = ["get-bundles", "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA", "--replica", "rep"]
        response = api.make_request(args)
        self.assertEqual(self._get_first_url(response), "https://hca-dss.czi.technology/v1/bundles/AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA?replica=rep")
        self.assertTrue(response.ok)

    def test_refs(self):
        """Test internal JSON reference resolution."""
        api = hca.define_api.API("a", "b", True)
        args = ["put-ref_test", "--obj-name", "name", "--obj-uuid", "uuid", "--obj-versions", "item1", "item2"]
        out = {"obj_name": "name", "obj_uuid": "uuid", "obj_versions": ["item1", "item2"]}
        self.assertEqual(api.parse_args(args), out)

    def test_array_cli(self):
        """Ensure that this framework can handle arrays."""
        api = hca.define_api.API("a", "b", True)
        args = ["put-bundles", "uuid", "version", "--extras-timestamp", "name", "name1", "--extras-file_uuid", "uuid1", "uuid2"]
        print(api.parse_args(args))
        out = {"uuid": "uuid", "bundle_version": "version", "extras_timestamp": ["name", "name1"], "extras_file_uuid": ["uuid1", "uuid2"]}
        self.assertEqual(api.parse_args(args), out)


if __name__ == '__main__':
    unittest.main()
