"""HCA DCP CLI."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import requests
import sys

from .define_api import API
from .regenerate_api import generate_python_bindings


def main():
    """Entrance to functionality."""
    cli = API()
    response = cli.make_request(sys.argv[1:])
    if isinstance(response, requests.Response):
        print(response.content.decode())
    else:
        print(json.dumps(response))
