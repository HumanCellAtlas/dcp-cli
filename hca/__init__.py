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
        CHUNK_SIZE = (2 ** 20) * 16  # 16 MB
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE, decode_unicode=True):
            if chunk:  # filter out keep-alive new chunks
                print(chunk)
    elif isinstance(response, dict):
        print(json.dumps(response))
    elif isinstance(response, str):
        print(response)
    else:  # Unicode
        print(response.decode())
