from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from . import DSSClient

def add_commands(subparsers):
    dss_parser = subparsers.add_parser('dss', help="Interact with the HCA Data Storage System")

    def help(args):
        dss_parser.print_help()

    if sys.version_info >= (2, 7, 9):  # See https://bugs.python.org/issue9351
        dss_parser.set_defaults(entry_point=help)
    dss_subparsers = dss_parser.add_subparsers()
    dss_cli_client = DSSClient()
    dss_cli_client.build_argparse_subparsers(dss_subparsers)
