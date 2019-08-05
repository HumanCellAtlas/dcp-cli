from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from . import AuthClient


def add_commands(subparsers, help_menu=False):
    auth_parser = subparsers.add_parser('auth', help="Interact with the HCA authorization and authentication system.")

    def help(args):
        auth_parser.print_help()

    if sys.version_info >= (2, 7, 9):  # See https://bugs.python.org/issue9351
        auth_parser.set_defaults(entry_point=help)
    auth_subparsers = auth_parser.add_subparsers()
    auth_cli_client = AuthClient()
    auth_cli_client.build_argparse_subparsers(auth_subparsers, help_menu=help_menu)
