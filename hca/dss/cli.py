from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
import pkgutil

from ..dss import autogenerated, composite_commands


def add_commands(subparsers):
    dss_parser = subparsers.add_parser('dss')
    dss_subparsers = dss_parser.add_subparsers()
    _add_commands_from_package(autogenerated, dss_subparsers)
    _add_commands_from_package(composite_commands, dss_subparsers)


def _add_commands_from_package(package, subparsers):
    prefix = package.__name__ + "."
    for importer, modname, _ in pkgutil.iter_modules(package.__path__, prefix):
        module = importer.find_module(modname).load_module(modname)
        module_classes = inspect.getmembers(module, inspect.isclass)
        for klassname, klass in module_classes:
            if klass.__module__ == modname:
                klass.add_parser(subparsers)


def parse_args(argparser_args):
    """Parse the input arguments into a map from parameter name -> value."""
    return {k: v for k, v in vars(argparser_args).items() if v is not None}
