import argparse
import json

import Constants


class AddObject(argparse.Action):
    """Object to parse json objects when they're inputted in the cli."""

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddObject, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, json.loads(values))


class AddedCommand:
    """Class containing information to reach this endpoint."""

    @classmethod
    def _get_endpoint_name(cls):
        raise NotImplementedError("This function has not been implemented yet.")

    @classmethod
    def _get_endpoint_info(cls):
        raise NotImplementedError("This function has not been implemented yet.")

    @classmethod
    def _get_arg_type(cls, arg_type_string):
        argtype = None
        if arg_type_string == "integer":
            argtype = int
        elif arg_type_string == "boolean":
            argtype = bool
        elif arg_type_string == "number":
            argtype = float
        return argtype

    @classmethod
    def _get_action(cls, arg_type_string):
        if arg_type_string == "object":
            return AddObject
        return "store"

    @classmethod
    def _add_positional_args(cls, subparser):
        endpoint_info = cls._get_endpoint_info()
        for positional_arg in endpoint_info['positional']:
            h = endpoint_info['description']

            argtype = cls._get_arg_type(positional_arg['type'])

            subparser.add_argument(
                positional_arg['argument'],
                nargs=None if positional_arg['required'] else "?",
                help=h,
                type=argtype
            )

    @classmethod
    def _add_optional_args(cls, subparser):
        endpoint_info = cls._get_endpoint_info()
        for (optional_name, optional_data) in endpoint_info['options'].items():
            h = endpoint_info['description']

            argtype = cls._get_arg_type(optional_data['type'])
            actiontype = cls._get_action(optional_data['type'])

            optional_name_with_dashes = optional_name.replace("_", "-")
            subparser.add_argument(
                "--" + optional_name_with_dashes,
                dest=optional_name,  # So we can send correctly formatted objects to api.
                metavar=optional_data['metavar'],
                required=optional_data['required'],
                nargs="+" if optional_data['array'] else None,
                help=h,
                type=argtype,
                action=actiontype
            )

    @classmethod
    def add_parser(cls, subparsers):
        """Add a parser."""
        endpoint_name = cls._get_endpoint_name()
        endpoint_info = cls._get_endpoint_info()

        subparser = subparsers.add_parser(endpoint_name, help=endpoint_info['description'])
        cls._add_positional_args(subparser, endpoint_info)
        cls._add_optional_args(subparser, endpoint_info)

    @classmethod
    def run_cli(cls):
        """Run this command using args from the cli."""
        pass

    @classmethod
    def run(cls, uuid, version=None, replica=None):
        """Function that will be exposed to the api users."""
        pass
