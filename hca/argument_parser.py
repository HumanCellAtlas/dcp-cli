import argparse

from .error import PrintingException


class NonPrintingParser(argparse.ArgumentParser):
    """ArgumentParser that will return help and error strings instead of printing."""

    def __init__(self, *args, **kwargs):
        super(NonPrintingParser, self).__init__(*args, **kwargs)

    def print_usage(self, file=None):
        raise PrintingException(self.format_usage())

    def print_help(self, file=None):
        raise PrintingException(self.format_help())
