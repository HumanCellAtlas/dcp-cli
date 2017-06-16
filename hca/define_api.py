from __future__ import absolute_import, division, print_function, unicode_literals

import json, sys, os
from io import open
import pprint
import requests
from .parser import get_parser


class API:
    """Class for interacting with the REST Api."""

    def __init__(self, user, password, test=False):
        """Initialize the CLI API."""
        spec = self.get_spec(test)
        self.base_url = "https://" + spec['host'] + spec['basePath']
        self.parser, self.positional_args = get_parser(spec)

    def get_spec(self, test):
        """Load the API specification."""
        url = os.path.dirname(os.path.realpath(__file__)) + "/api_spec.json"
        if test:
            url = os.path.dirname(os.path.realpath(__file__)) + "/../test/test.json"

        with open(url) as fp:
            api_spec_dict = json.load(fp)
        return api_spec_dict

    def _build_url(self, endpoint, namespace):
        split_endpoint = endpoint.split("-")[1:]

        given_positional_args = [p for p in split_endpoint]
        for positional_arg in self.positional_args[endpoint]:
            if positional_arg in namespace:
                arg = namespace[positional_arg]
                if isinstance(positional_arg, list):
                    arg = arg[0]
                given_positional_args.append(arg)
        url = self.base_url + "/" + "/".join(given_positional_args)
        return url

    def _build_payload(self, endpoint, namespace):
        query_payload = {}
        body_payload = {}
        header_payload = {}
        for (arg_name, arg) in namespace.items():
            if arg_name not in self.positional_args[endpoint]:
                query_payload[arg_name] = arg
        #     if arg_name in self.positional_args[endpoint]["header"]:
        #         header_payload[arg_name] = arg
        #     if arg_name not in self.positional_args[endpoint]:
        #         body_payload[arg_name] = arg
        return query_payload, body_payload, header_payload

    def parse_args(self, args):
        namespace = vars(self.parser.parse_args(args))
        namespace = {k: namespace[k] for k in namespace if namespace[k] is not None}
        return namespace

    def make_request(self, args):
        """Function to actually make request to api."""
        namespace = self.parse_args(args)
        endpoint = args[0]

        url = self._build_url(endpoint, namespace)
        query_payload, body_payload, header_payload = self._build_payload(endpoint, namespace)

        param_methods = ["get", "options", "head", "delete"]
        json_methods = ["post", "put", "patch"]

        method = endpoint[:endpoint.find("-")]
        if method in param_methods:
            request = requests.request(method, url, params=query_payload, headers=header_payload)
        elif method in json_methods:
            request = requests.request(method, url, json=body_payload, params=query_payload, headers=header_payload)
        else:
            raise ValueError("Bad request type")

        return request


if __name__ == "__main__":
    api = API("a", "b", True)
    print(api.make_request(sys.argv[1:]))
