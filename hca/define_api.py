from __future__ import absolute_import, division, print_function, unicode_literals

import json, sys, o
from io import open
import requests
from .parser import get_parser


class API:
    """Class for interacting with the REST Api."""

    def __init__(self, api_url, user):
        """Initialize the CLI API."""
        self.spec = self.get_spec()
        self.base_url = "https://" + self.spec['host'] + self.spec['basePath']
        self.parser, self.positional_args = get_parser(self.spec)

    def get_spec(self):
        """Load the API specification."""
        client = SwaggerClient.from_spec(load_file('api_spec.json'))
        print(client.swagger_spec.deref(client.swagger_spec.spec_dict['definitions']))
        print("Done")
        with open("api_spec.json") as fp:
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
        payload = {}
        for (arg_name, arg) in namespace.items():
            if arg_name not in self.positional_args[endpoint]:
                payload[arg_name] = arg
        return payload

    def make_request(self, args):
        """Function to actually make request to api."""
        namespace = vars(self.parser.parse_args(args))
        namespace = {k: namespace[k] for k in namespace if namespace[k] is not None}
        endpoint = args[0]

        url = self._build_url(endpoint, namespace)
        payload = self._build_payload(endpoint, namespace)

        param_methods = ["get", "options", "head", "delete"]
        json_methods = ["post", "put", "patch"]

        method = endpoint[:endpoint.find("-")]
        if method in param_methods:
            request = requests.request(method, url, params=payload)
        elif method in json_methods:
            request = requests.request(method, url, json=payload)
        else:
            raise ValueError("Bad request type")

        return request
        # Template for datetime transformer.
        # datetime.datetime.strptime( "2007-03-04T21:08:12", "%Y-%m-%dT%H:%M:%S" )


if __name__ == "__main__":
    api = Api("a", "b")
    print(sys.argv[1])
    print(api.make_request(sys.argv[1:]))
