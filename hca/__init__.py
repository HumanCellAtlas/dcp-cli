"""HCA DCP CLI."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import requests
import sys

from .define_api import API


def main():
    """Entrance to functionality."""
    api = API()
    response = api.make_request(sys.argv[1:])
    if isinstance(response, requests.Response):
        sys.stdout.write(response.content.decode())
    else:
        print(json.dumps(response))
