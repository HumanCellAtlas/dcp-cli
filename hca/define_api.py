from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import sys
import requests

from io import open

from .parser import get_parser, ADDED_COMMANDS
from .constants import Constants


class API:
    """Class for interacting with the REST Api."""

    def __init__(self, test_api_path=None):
        """Initialize the CLI API."""
        self.test_api_path = test_api_path
        spec = self.get_spec()
        scheme = spec['schemes'][0] if 'schemes' in spec else "https"
        self.base_url = "{}://{}{}".format(scheme, spec['host'], spec['basePath'])
        self.parser, self.param_data = get_parser(spec)

    def get_spec(self):
        """
        Load the API specification.

        self.test_api_path is a path to the test api path if the functionality is being tested.
            api_spec is the spec downloaded from the api on build.
            ../test/test is the mocked up spec I've been toying with.
        :return:     The dictionary containing all swagger specification definitions.
        """
        url = self.test_api_path
        if not url:
            url = os.path.join(os.path.dirname(os.path.realpath(__file__)), "api_spec.json")

        with open(url) as fp:
            api_spec_dict = json.load(fp)
        return api_spec_dict

    def _build_url(self, endpoint, namespace):
        """
        Add positional arguments into the url.

        :param endpoint: The first argument to the cli. Dictates what positional args are available.
                         The part preceding "-" declares what http method to use.
                         The part after "-" declares what path is being used,
                         which dictates what positional args are available.
        :param namespace: The parsed arguments from argparse.
        :return: The url to send requests to (minus query string).
        """
        split_endpoint = endpoint.split("-")[1]

        all_positional_args_for_endpoint = [arg['argument'] for arg in self.param_data[endpoint]['positional']]

        given_positional_args = [split_endpoint]
        for positional_arg in all_positional_args_for_endpoint:
            if positional_arg in namespace:
                arg = namespace[positional_arg]
                given_positional_args.append(arg)
            else:
                # No positional args can be skipped.
                # If arg2 is present but arg1 isn't, arg2 can't take arg1's positional place.
                break
        url = self.base_url + "/" + "/".join(given_positional_args)
        return url

    def _add_arg(self, arg, payload, hierarchy):
        """
        Add a given argument to its associated payload.

        Arguments:
         - arg: The value that is being assigned.
         - payload: The payload structure before adding this value.
         - hierarchy: List that describes where in payload to put arg (needed because of nested objects
                      within a payload). Each element of hierarchy describes the data format of that layer.
                      * If a level is an empty list, that means it's a list of the type taken from argpargs,
                        so we just add each element as is to the payload.
                      * If a level is a populated list, that means it's a list of objects with each element
                        of that list corresponding to the name of the variable that the corresponding element
                        in the inputs will be assigned to.
                      * A level being a string (call it str) means str is a key to either the next level of the
                        hierarchy (if there is one) or to the final argument that's being passed in here.
        """
        inner_payload = payload

        # Iterating through payload structure to find the right value to set.
        # Loop through hierarchy to define data structures that may not exist in payload yet.
        for i in range(len(hierarchy) - 1):
            curr_level = hierarchy[i]

            if curr_level not in inner_payload:
                inner_payload[curr_level] = [] if isinstance(hierarchy[i + 1], list) else {}
            inner_payload = inner_payload[curr_level]

        curr_level = hierarchy[-1]

        # Command line argument represents a list of objects.
        if isinstance(curr_level, list) and len(curr_level) > 0:
            for string_object_values in arg:
                object_values = string_object_values.split(Constants.OBJECT_SPLITTER)
                if len(object_values) != len(curr_level):
                    raise ValueError("Each argument must have a value. Use 'None' if you don't want to define it.")

                obj = {}
                for i, value in enumerate(object_values):
                    if value == "None":
                        continue
                    argument_name = curr_level[i][0]
                    argument_type = curr_level[i][1]
                    if argument_type == "object":
                        value = json.loads(value)
                    elif argument_type == "integer":
                        value = int(value)
                    elif argument_type == "number":
                        value = float(value)
                    elif argument_type == "boolean" and value == "True":
                        value = True
                    elif argument_type == "boolean" and value == "False":
                        value = False
                    elif argument_type != "string":
                        raise ValueError("Unknown type")
                    obj[argument_name] = value
                inner_payload.append(obj)

        # Command line argument represents a list of standard types.
        elif isinstance(curr_level, list):
            for object_arg in arg:
                inner_payload.append(object_arg)

        # Command line argument represents a standard type.
        else:
            inner_payload[curr_level] = arg

    def _build_payloads(self, endpoint, namespace):
        """
        Build query params, header params, and body for http requests.

        Loop through all arguments provided from argparse and assign them to their appropriate payload.
        :param endpoint: <httpmethod>-<endpoint> (e.g. put-files). Data in param_data is indexed by this.
        :param namespace: The parsed arguments from argparse.
        :return: Properly formatted query params, header params, and body payload for http request.
        """
        query_payload = {}
        body_payload = {}
        header_payload = {}
        for (arg_name, arg) in namespace.items():
            # If the argument is positional, belongs in path, not a payload
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

    def make_request(self, args, stream=False):
        """Function to actually make request to api."""
        if not args:
            self.parser.print_help()
            self.parser.exit(1)
        namespace = self.parse_args(args)
        endpoint = args[0]

        for command in ADDED_COMMANDS:
            if endpoint == command.CONSOLE_ARGUMENT:
                return command.run(namespace, self)

        url = self._build_url(endpoint, namespace)
        query_payload, body_payload, header_payload = self._build_payloads(endpoint, namespace)

        param_methods = ["get", "options", "head", "delete"]
        json_methods = ["post", "put", "patch"]

        method = endpoint[:endpoint.find("-")]
        if method in param_methods:
            request = requests.request(method, url, params=query_payload, headers=header_payload, stream=stream)
        elif method in json_methods:
            request = requests.request(
                method,
                url,
                json=body_payload,
                params=query_payload,
                headers=header_payload,
                stream=stream
            )
        else:
            raise ValueError("Bad request type")
        return request


if __name__ == "__main__":
    api = API()
    response = api.make_request(sys.argv[1:])
    if response:
        print(response.headers)
        print(response.content)
