"""HCA DCP CLI."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import requests
import sys


def main():
    """Entrance to functionality."""
    from .cli import CLI
    cli = CLI()
    response = cli.make_request(sys.argv[1:])
    if isinstance(response, requests.Response):
        print(response.content.decode())
    else:
        print(json.dumps(response))
