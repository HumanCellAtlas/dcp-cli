from . import DSSClient


def add_commands(subparsers, help_menu=False):
    dss_parser = subparsers.add_parser('dss', help="Interact with the HCA Data Storage System")

    def help(args):
        dss_parser.print_help()

    dss_parser.set_defaults(entry_point=help)
    dss_subparsers = dss_parser.add_subparsers()
    dss_cli_client = DSSClient()
    dss_cli_client.build_argparse_subparsers(dss_subparsers, help_menu=help_menu)
