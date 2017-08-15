import argparse

from .error import PrintingException


class NonPrintingParser(argparse.ArgumentParser):
    """ArgumentParser that will return help and error strings instead of printing."""

    def print_usage(self, file=None):
        raise PrintingException(self.format_usage())

    def print_help(self, file=None):
        raise PrintingException(self.format_help())
