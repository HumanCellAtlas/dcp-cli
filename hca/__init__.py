"""HCA DCP CLI."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import requests
import sys

import six


def main():
    """Entrance to functionality."""
    from .cli import CLI
    cli = CLI()
    response = cli.make_request(sys.argv[1:])

    if isinstance(response, requests.Response):
        print(response.content.decode())
    elif isinstance(response, dict):
        print(json.dumps(response))
    elif isinstance(response, str):
        print(response)
    else:  # Unicode
        print(response.decode())
