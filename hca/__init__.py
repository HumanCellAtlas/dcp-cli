"""HCA DCP CLI."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import requests
import sys

from .cli import CLI


def main():
    """Entrance to functionality."""
    print("before init")
    cli = CLI()
    print("in init")
    response = cli.make_request(sys.argv[1:])
    if isinstance(response, requests.Response):
        print(response.content.decode())
    else:
        print(json.dumps(response))
