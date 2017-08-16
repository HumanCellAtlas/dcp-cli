"""HCA DCP CLI."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import requests
import sys

import six

from .constants import Constants


def main():
    """Entrance to functionality."""
    from .cli import CLI
    cli = CLI()

    # Windows includes carriage returns
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    response = cli.make_request(sys.argv[1:])
    if isinstance(response, requests.Response):
        for chunk in response.iter_content(chunk_size=Constants.CHUNK_SIZE, decode_unicode=True):
            if chunk:  # filter out keep-alive new chunks
                if six.PY3:
                    sys.stdout.buffer.write(chunk)
                else:
                    sys.stdout.write(chunk)
    elif isinstance(response, dict):
        print(json.dumps(response))
    elif isinstance(response, str):
        print(response)
    else:  # Unicode
        print(response.decode())
