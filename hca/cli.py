# coding: utf-8

"""
Human Cell Atlas Command Line Interface
"""

import argparse
import sys
import os

from .dss import cli as dss_cli
from .upload import cli as staging_cli


class CLI:

    def __init__(self):
        # Windows includes carriage returns
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

        self._setup_arg_parser()

    def run(self, command_line_args=None):
        argparser_args = self.top_parser.parse_args(command_line_args or sys.argv[1:])
        if not argparser_args.__contains__('func'):
            self.top_parser.print_help()
            sys.exit(1)
        command_function = argparser_args.func
        del argparser_args.func
        command_function(argparser_args)

    def _setup_arg_parser(self):
        self.top_parser = argparse.ArgumentParser(description=__doc__,
                                                  formatter_class=argparse.RawDescriptionHelpFormatter)
        top_subparsers = self.top_parser.add_subparsers(title="Commands",
                                                        help="Use \"hca <command> -h\" to get detailed command help.\"")

        help_parser = top_subparsers.add_parser('help', add_help=False)
        help_parser.set_defaults(func=self._help)

        dss_cli.add_commands(top_subparsers)
        staging_cli.add_commands(top_subparsers)

    def _help(self, args):
        self.top_parser.print_usage()
        print("""
Commands:

    help     print this message
    dss      manipulate HCA Data Store
    upload   upload files and manage upload areas

Use "hca <command> -h" to get detailed command help.
        """)
