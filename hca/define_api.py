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
        self.parser, self.param_data = get_parser(spec)

        self.positional_args = {endpoint: [arg['argument'] for arg in self.param_data[endpoint]['positional']] for endpoint in self.param_data}

    def get_spec(self, test):
        """Load the API specification."""
        url = os.path.dirname(os.path.realpath(__file__)) + "/api_spec.json"
        if test:
            url = os.path.dirname(os.path.realpath(__file__)) + "/../test/test.json"

        with open(url) as fp:
            api_spec_dict = json.load(fp)
        return api_spec_dict

    def _build_url(self, endpoint, namespace):
        """Add positional arguments into the url."""
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

    def _add_arg(self, arg, payload, hierarchy):
        """
        Add a given argument to its associated payload.

        Arguments:
         - arg: The value that is being assigned.
         - payload: The payload structure before adding this value.
         - hierarchy: Data structure that describes where in payload to put arg.
        """
        inner_payload = payload
        while len(hierarchy) > 1:
            curr_level = hierarchy[0]

            if curr_level not in inner_payload:
                inner_payload[curr_level] = [] if isinstance(hierarchy[1], list) else {}
            inner_payload = inner_payload[curr_level]

            hierarchy = hierarchy[1:]

        curr_level = hierarchy[0]

        if type(curr_level) == list and len(curr_level) > 0:
            for object_arg in arg:
                args = object_arg.split(":")
                if len(args) != len(curr_level):
                    raise ValueError("Each argument must have a value. Use 'None' if you don't want to define it.")

                obj = {}
                for i, arg in enumerate(args):
                    if arg == "None":
                        continue
                    argument_name = curr_level[i]
                    obj[argument_name] = arg
                inner_payload.append(obj)

        elif type(curr_level) == list:
            for object_arg in arg:
                inner_payload.append(object_arg)
        else:
            inner_payload[curr_level] = arg

    def _build_payloads(self, endpoint, namespace):
        query_payload = {}
        body_payload = {}
        header_payload = {}
        for (arg_name, arg) in namespace.items():
            if arg_name not in self.param_data[endpoint]["options"]:
                continue

            payload_format = self.param_data[endpoint]["options"][arg_name]["in"]
            hierarchy = self.param_data[endpoint]["options"][arg_name]["hierarchy"]
            if payload_format == "query":
                self._add_arg(arg, query_payload, hierarchy)
            if payload_format == "body":
                self._add_arg(arg, body_payload, hierarchy)
            if payload_format == "header":
                self._add_arg(arg, header_payload, hierarchy)
        return query_payload, body_payload, header_payload

    def parse_args(self, args):
        """Parse the input arguments into a map from parameter name -> value."""
        namespace = vars(self.parser.parse_args(args))
        namespace = {k: namespace[k] for k in namespace if namespace[k] is not None}
        return namespace

    def make_request(self, args):
        """Function to actually make request to api."""
        namespace = self.parse_args(args)
        endpoint = args[0]

        url = self._build_url(endpoint, namespace)
        query_payload, body_payload, header_payload = self._build_payloads(endpoint, namespace)

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
    response = api.make_request(sys.argv[1:])
    print(response.content)
