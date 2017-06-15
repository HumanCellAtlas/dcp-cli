from __future__ import absolute_import, division, print_function, unicode_literals

import json, sys, os
from io import open
import requests
from .parser import get_parser


class API:
    """Class for interacting with the REST Api."""

    def __init__(self, api_url, user):
        """Initialize the CLI API."""
        self.spec = self.get_spec()
        self.base_url = self.spec['host'] + self.spec['basePath']
        self.parser = get_parser(self.spec)

    def get_spec(self):
        """Load the API specification."""
        with open(os.path.dirname(os.path.realpath(__file__)) + "/api_spec.json") as fp:
            api_spec_dict = json.load(fp)
        return api_spec_dict

    def parse_args(self, args):
        """Parse cmd line arguments."""
        namespace = vars(self.parser.parse_args(args))
        namespace = {k: namespace[k] for k in namespace if namespace[k] is not None}
        return namespace

    def make_request(self, args):
        """Function to actually make request to api. Ignore for now."""
        return self.parse_args(args)


if __name__ == "__main__":
    api = API("a", "b")
    print(api.make_request(sys.argv[1:]))
