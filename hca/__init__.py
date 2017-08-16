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
    elif six.PY2 and type(response) == unicode:
        print(response.decode())
    elif type(response) == str:
        print(response)
    else:
        print(json.dumps(response))
