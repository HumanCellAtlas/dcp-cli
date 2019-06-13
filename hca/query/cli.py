from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from . import DCPQueryClient

def add_commands(subparsers, help_menu=False):
    query_parser = subparsers.add_parser('query', help="Interact with the HCA DCP Query Service")

    def help(args):
        query_parser.print_help()

    if sys.version_info >= (2, 7, 9):  # See https://bugs.python.org/issue9351
        query_parser.set_defaults(entry_point=help)
    query_subparsers = query_parser.add_subparsers()
    query_cli_client = DCPQueryClient()
    query_cli_client.build_argparse_subparsers(query_subparsers, help_menu=help_menu)
