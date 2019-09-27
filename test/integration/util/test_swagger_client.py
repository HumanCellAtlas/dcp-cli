#!/usr/bin/env python
# coding: utf-8
import argparse
import json
import os
import sys
import unittest
import requests
from unittest import mock
from unittest.mock import mock_open

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.util
from hca import HCAConfig
from test import TEST_DIR


class TestSwaggerClient(unittest.TestCase):
    """
    Tests the correctness of SwaggerClient's code generation methods based
    on a general Swagger definition (dcp-cli/test/res/test_swagger.json).

    Specifically, these tests verify that the API client method signatures
    are generated correctly, are callable and are executed when the
    corresponding, generated argparse command is invoked.

    """
    swagger_url = "test_swagger_url"
    swagger_filename = "test_swagger.json"
    test_swagger_json = None

    parser = argparse.ArgumentParser(description="Test ArgumentParser")
    subparsers = parser.add_subparsers()

    dummy_response = requests.models.Response()
    dummy_response.status_code = 200
    dummy_response._content = "content"

    generated_method_names = [
        # method names corresponding to all `paths`
        # defined in `dcp-cli/test/res/test_swagger.json`
        "get_with_path_query_params",
        "post_with_path_query_body_param",
        "post_with_list_in_body_param",
        "delete_with_missing_required_param",
        "head_with_optional_param",
        "put_with_invalid_enum_param",
        "get_with_allOf_in_body_param",
        "get_with_allOf_multiple_in_body_param",
        "get_with_something_in_path",
        "get_with_header_parameter",
        "get_with_request_body_application_json"
    ]

    @classmethod
    def setUpClass(cls):
        """
        Initialize SwaggerClient using a test HCAConfig.
        """
        swagger_response = requests.models.Response()
        swagger_response.status_code = 200
        with open(os.path.join(TEST_DIR, "res", cls.swagger_filename), 'rb') as fh:
            # load test swagger JSON file
            content = fh.read()
            swagger_response._content = content
            cls.test_swagger_json = json.loads(content.decode("utf-8"))

        cls.url_base = (cls.test_swagger_json['schemes'][0] + "://" +
                        cls.test_swagger_json['host'] +
                        cls.test_swagger_json['basePath'])

        with mock.patch('requests.Session.get') as mock_get, \
                mock.patch("builtins.open", mock_open()), \
                mock.patch('hca.util.fs.atomic_write'), \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json') as mock_load_swagger_json:
            # init SwaggerClient with test swagger JSON file
            mock_get.return_value = swagger_response
            mock_load_swagger_json.return_value = json.loads(swagger_response._content.decode("utf-8"))

            config = HCAConfig(save_on_exit=False)
            config['SwaggerClient'] = {}
            config['SwaggerClient'].swagger_url = cls.swagger_url
            cls.client = hca.util.SwaggerClient(config)
            cls.client.build_argparse_subparsers(cls.subparsers)

    @classmethod
    def tearDownClass(cls):
        cls.client._swagger_spec = None

    def setUp(self):
        self.client._session = requests.Session()

    def test_client_methods_exist(self):
        for method_name in self.generated_method_names:
            with self.subTest(method_name):
                self.assertTrue(hasattr(self.client.__class__, method_name) and
                                callable(getattr(self.client.__class__, method_name)))

    def test_get_with_path_query_params(self):
        http_method = "get"
        path = "/with/path/query/params"
        path_param = "param"
        query_param = "enum1"
        url = self.url_base + path + "/" + path_param

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test API client method
            mock_request.return_value = self.dummy_response

            self.client.get_with_path_query_params(path_param=path_param, query_param=query_param)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={'query_param': query_param},
                                            json=None,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test argparse command
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args(args=["get-with-path-query-params",
                                                "--path-param", path_param,
                                                "--query-param", query_param])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={'query_param': query_param},
                                            json=None,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

    def test_post_with_path_query_body_params(self):
        http_method = "post"
        path = "/with/path/query/body/params"
        path_param = "param"
        query_param = "query"
        body_param = {
            'prop1': "val1",
            'prop2': "val2"
        }
        url = self.url_base + path + "/" + path_param

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test API client method
            mock_request.return_value = self.dummy_response

            self.client.post_with_path_query_body_param(path_param=path_param,
                                                        query_param=query_param,
                                                        prop1=body_param['prop1'],
                                                        prop2=body_param['prop2'])
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={'query_param': query_param},
                                            json=body_param,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test argparse command
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args(args=["post-with-path-query-body-param",
                                                "--path-param", path_param,
                                                "--query-param", query_param,
                                                "--prop1", body_param['prop1'],
                                                "--prop2", body_param['prop2']])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={'query_param': query_param},
                                            json=body_param,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

    def test_post_with_list_in_body_param(self):
        path = "/with/list/in/body/param"
        http_method = "post"
        body_param = {
            'prop1': "param",
            'prop2': [{'prop3': "val3", 'prop4': True}, {'prop3': "val5", 'prop4': False}]
        }
        url = self.url_base + path

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            mock_request.return_value = self.dummy_response

            self.client.post_with_list_in_body_param(prop1=body_param['prop1'],
                                                     prop2=body_param['prop2'])
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={},
                                            json=body_param,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args(["post-with-list-in-body-param",
                                           "--prop1", body_param['prop1'],
                                           "--prop2",
                                           json.dumps(body_param['prop2'][0]), json.dumps(body_param['prop2'][1])])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={},
                                            json=body_param,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

    def test_get_with_allOf_in_body_param(self):
        path = "/with/allOf/in/body/param"
        http_method = "get"
        func_name = http_method + path
        body_param = {
            'prop1': "param1",
            'prop2': "param2"
        }
        url = self.url_base + path

        with self.subTest('API'):
            with mock.patch('requests.Session.request') as mock_request, \
                    mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
                mock_request.return_value = self.dummy_response

                resp = getattr(self.client, func_name.replace('/', '_'))(**body_param)
                mock_consume_response.assert_called_once_with(mock.ANY)
                mock_request.assert_called_once_with(http_method,
                                                     url,
                                                     params={},
                                                     json=body_param,
                                                     stream=False,
                                                     headers={},
                                                     timeout=mock.ANY)

        with self.subTest('CLI'):
            with mock.patch('requests.Session.request') as mock_request, \
                    mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
                mock_request.return_value = self.dummy_response

                args = self.parser.parse_args([func_name.replace('/', '-'),
                                               "--prop1", body_param['prop1'],
                                               "--prop2", body_param['prop2']])
                args.entry_point(args)
                mock_consume_response.assert_called_once_with(mock.ANY)
                mock_request.assert_called_once_with(http_method,
                                                     url,
                                                     params={},
                                                     json=body_param,
                                                     stream=False,
                                                     headers={},
                                                     timeout=mock.ANY)

    def test_get_with_allOf_multiple_in_body_param(self):
        path = "/with/allOf/multiple/in/body/param"
        http_method = "get"
        func_name = http_method + path
        url = self.url_base + path

        with self.subTest('API'):
            with mock.patch('requests.Session.request') as mock_request, \
                    mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
                mock_request.return_value = self.dummy_response

                getattr(self.client, func_name.replace('/', '_'))(prop1='a')
                mock_consume_response.assert_called_once_with(mock.ANY)
                mock_request.assert_called_once_with(http_method,
                                                     url,
                                                     params={},
                                                     json={'prop1': 'a'},
                                                     stream=False,
                                                     headers={},
                                                     timeout=mock.ANY)

        # In the CLI test, we try passing a value to `--prop1` that isn't in
        # its enum. If the schema is parsed correctly, we'll get an error.
        with self.subTest('CLI'):
            try:
                args = self.parser.parse_args([func_name.replace('/', '-'),
                                               '--prop1', 'not-in-enum'])
                args.entry_point(args)
            except SystemExit:  # an argparse.ArgumentError is raised, leading to SystemExit
                pass
            else:
                raise AssertionError("Expected SystemExit")

    def test_delete_with_missing_required_param(self):
        path = "/with/missing/required/param"
        command = "delete-with-missing-required-param"
        http_method = "delete"
        path_param = "param"
        url = self.url_base + path + "/" + path_param

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test success
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args([command,
                                           "--path-param", path_param])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={},
                                            json=None,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

            with self.assertRaises(SystemExit) as e:
                # test failure
                self.parser.parse_args(args=[command])
            self.assertEqual(e.exception.code, 2)

    def test_head_with_optional_param(self):
        path = "/with/optional/param"
        command = "head-with-optional-param"
        http_method = "head"
        query_param = "query"
        url = self.url_base + path

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test with optional param
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args([command,
                                           "--query-param", query_param])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={'query_param': query_param},
                                            json=None,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test without optional param
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args([command])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={},
                                            json=None,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

    def test_put_with_invalid_enum_param(self):
        path = "/with/invalid/enum/param"
        command = "put-with-invalid-enum-param"
        http_method = "put"
        query_param_valid = "enum1"
        query_param_invalid = "query"
        url = self.url_base + path

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            # test with valid enum
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args([command,
                                           "--query-param", query_param_valid])
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                            url,
                                            params={'query_param': query_param_valid},
                                            json=None,
                                            stream=False,
                                            headers={},
                                            timeout=mock.ANY)

            with self.assertRaises(SystemExit) as e:
                # test with invalid enum
                self.parser.parse_args(args=[command,
                                             '--query-param', query_param_invalid])
            self.assertEqual(e.exception.code, 2)

    def test_get_with_something_in_path(self):
        self._test("/with/something/.well-known/in/path", "get")

    def test_get_with_header_parameter(self):
        self._test("/with/header/parameter",
                   "get",
                   headers={"some_header": "foo"},
                   command_args=["--some-header", "foo"])

    def test_get_with_request_body_application_json(self):
        self._test("/with/request_body/not_application/json",
                   "get",
                   json={"foo": "bar"},
                   command_args=["--foo", "bar"])

    def _test(self,
              path: str,
              http_method: str,
              json: dict = None,
              stream: bool = False,
              params: dict = None,
              headers: dict = None,
              timeout=mock.ANY,
              command_args: list = None):

        params = params or {}
        headers = headers or {}
        command_args = command_args or []

        command = self.get_command(http_method, path)
        url = self.url_base + path

        with mock.patch('requests.Session.request') as mock_request, \
                mock.patch('hca.util._ClientMethodFactory._consume_response') as mock_consume_response:
            mock_request.return_value = self.dummy_response

            args = self.parser.parse_args([command] + command_args)
            args.entry_point(args)
            mock_consume_response.assert_called_once_with(mock.ANY)
            mock_request.assert_called_once_with(http_method,
                                                 url,
                                                 json=json,
                                                 stream=stream,
                                                 params=params,
                                                 headers=headers,
                                                 timeout=timeout)

    def get_command(self, http_method, path):
        return self.client._build_method_name(http_method, path).replace('_', '-')


if __name__ == "__main__":
    unittest.main()
