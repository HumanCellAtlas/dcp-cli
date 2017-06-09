from __future__ import absolute_import, division, print_function, unicode_literals

# import os, sys, json, time, base64
import json, sys
from io import open
# import pprint
import requests
from parser import get_parser


class Api:
    """Class for interacting with the REST Api."""

    def __init__(self, api_url, user, password):
        """Initialize the CLI API."""
        self.spec = self.get_spec()
        self.base_url = self.spec['host'] + self.spec['basePath']
        self.parser = get_parser(self.spec)

    def get_spec(self):
        """Load the API specification."""
        with open("api_spec.json") as fp:
            api_spec_dict = json.load(fp)
        return api_spec_dict

    def make_request(self, args):
        namespace = vars(self.parser.parse_args(args))
        namespace = {k:namespace[k] for k in namespace if namespace[k] is not None}

        


        # path_args = path.split("/")
        # for arg in path_args:
        #     if (len(arg) > 0 and arg[0] == "{") or len(arg) == 0:

# print(requests.get('https://hca-dss.czi.technology/v1/bundles/1/1').json())

# x = Api("a", "b", "c")
# pprint.pprint(x.spec)

# import datetime
# datetime.datetime.strptime( "2007-03-04T21:08:12", "%Y-%m-%dT%H:%M:%S" )

if __name__ == "__main__":
    api = Api("a", "b", "c")
    print(api.make_request(sys.argv[1:]))
