import argparse
import json
import os
import re
import uuid

import jsonschema
import requests

from .constants import Constants
from .oauth_flow import get_access_token


class AddObject(argparse.Action):
    """Object to parse json objects when they're inputted in the cli."""

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddObject, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, json.loads(values))


class AddedCommand(object):
    """Class containing information to reach this endpoint."""

    @classmethod
    def _get_base_url(cls):
        raise NotImplementedError("This function has not been implemented yet.")

    @classmethod
    def get_command_name(cls):
        """Return the name that this command should be called to run this functionality."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

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
        for positional_arg in endpoint_info.get('positional', []):
            argtype = cls._get_arg_type(positional_arg['type'])

            subparser.add_argument(
                positional_arg['argument'],
                nargs=None if positional_arg['required'] else "?",
                help=endpoint_info['description'],
                type=argtype
            )

    @classmethod
    def _add_optional_args(cls, subparser):
        endpoint_info = cls._get_endpoint_info()
        for (optional_name, optional_data) in endpoint_info.get('options', {}).items():
            argtype = cls._get_arg_type(optional_data['type'])
            actiontype = cls._get_action(optional_data['type'])

            optional_name_with_dashes = optional_name.replace("_", "-")
            subparser.add_argument(
                "--" + optional_name_with_dashes,
                dest=optional_name,  # So we can send correctly formatted objects to api.
                metavar=optional_data['metavar'],
                required=optional_data['required'],
                nargs="+" if optional_data['array'] else None,
                help=endpoint_info['description'],
                type=argtype,
                action=actiontype
            )

    @classmethod
    def add_parser(cls, subparsers):
        """Add a command line subparser to handle this endpoint. Override this to add higher-level commands.

        :param subparsers: The parent parser that this subparser will be added to.
        """
        endpoint_name = cls.get_command_name()
        endpoint_info = cls._get_endpoint_info()

        subparser = subparsers.add_parser(endpoint_name, help=endpoint_info['description'])
        cls._add_positional_args(subparser)
        cls._add_optional_args(subparser)

    @classmethod
    def _get_ordered_path_args(cls, namespace):
        """
        Add positional arguments into the url.

        :param namespace: The parsed arguments from argparse.
        :return: The url to send requests to (minus query string).
        """
        endpoint_info = cls._get_endpoint_info()
        all_positional_args_for_endpoint = [arg['argument'] for arg in endpoint_info.get('positional', [])]

        given_positional_args = []
        for positional_arg in all_positional_args_for_endpoint:
            if namespace.get(positional_arg, None):
                arg = namespace[positional_arg]
                given_positional_args.append(arg)
            else:
                # No positional args can be skipped.
                # If arg2 is present but arg1 isn't, arg2 can't take arg1's positional place.
                break
        return given_positional_args

    @classmethod
    def _add_arg(cls, arg, payload, hierarchy):
        """
        Add a given argument to its associated payload.

        Arguments:
         - arg: The value that is being assigned.
         - payload: The payload structure before adding this value.
         - hierarchy: List that describes where in payload to put arg (needed because of nested objects
                      within a payload). Each element of hierarchy describes the data format of that layer.
                      * If a level is an empty list, that means it's a list of the type taken from argpargs,
                        so we just add each element as is to the payload.
                      * If a level is a populated list, that means it's a list of objects with each element
                        of that list corresponding to the name of the variable that the corresponding element
                        in the inputs will be assigned to.
                      * A level being a string (call it str) means str is a key to either the next level of the
                        hierarchy (if there is one) or to the final argument that's being passed in here.
        """
        inner_payload = payload

        # Iterating through payload structure to find the right value to set.
        # Loop through hierarchy to define data structures that may not exist in payload yet.
        for i in range(len(hierarchy) - 1):
            curr_level = hierarchy[i]

            if curr_level not in inner_payload:
                inner_payload[curr_level] = [] if isinstance(hierarchy[i + 1], list) else {}
            inner_payload = inner_payload[curr_level]

        curr_level = hierarchy[-1]

        # Command line argument represents a list of objects.
        if isinstance(curr_level, list) and len(curr_level) > 0:
            for string_object_values in arg:
                object_values = string_object_values.split(Constants.OBJECT_SPLITTER)
                if len(object_values) != len(curr_level):
                    raise ValueError("Each argument must have a value. Use 'None' if you don't want to define it.")

                obj = {}
                for i, value in enumerate(object_values):
                    if value == "None":
                        continue
                    argument_name = curr_level[i][0]
                    argument_type = curr_level[i][1]
                    if argument_type == "object":
                        value = json.loads(value)
                    elif argument_type == "integer":
                        value = int(value)
                    elif argument_type == "number":
                        value = float(value)
                    elif argument_type == "boolean" and value == "True":
                        value = True
                    elif argument_type == "boolean" and value == "False":
                        value = False
                    elif argument_type != "string":
                        raise ValueError("Unknown type")
                    obj[argument_name] = value
                inner_payload.append(obj)

        # Command line argument represents a list of standard types.
        elif isinstance(curr_level, list):
            for object_arg in arg:
                inner_payload.append(object_arg)

        # Command line argument represents a standard type.
        else:
            inner_payload[curr_level] = arg

    @classmethod
    def _build_body_payload(cls, namespace):
        """
        Build body for http requests.

        Loop through all arguments provided from argparse and assign them to the body payload when appropriate.
        :param namespace: The parsed arguments from argparse.
        :return: Properly formatted body payload for http request.
        """
        endpoint_info = cls._get_endpoint_info()
        body_payload = {}
        for (arg_name, arg) in namespace.items():
            # If the argument is positional, belongs in path, not a payload
            if arg_name not in endpoint_info["options"]:
                continue

            payload_format = endpoint_info["options"][arg_name]["in"]
            if payload_format == "body":
                hierarchy = endpoint_info["options"][arg_name]["hierarchy"]
                cls._add_arg(arg, body_payload, hierarchy)
        return body_payload

    @classmethod
    def _get_auth_header(cls, real_header=True):
        credentials_path = os.path.join(os.path.expanduser("~"), ".config", "hca")
        if not os.path.isdir(credentials_path):
            os.makedirs(credentials_path)

        access_token_wrapper = get_access_token(
            os.path.join(credentials_path, "oauth2.json"),
            __file__,
            scope="https://www.googleapis.com/auth/userinfo.email")

        token = access_token_wrapper.access_token if real_header else str(uuid.uuid4())
        return "Bearer {}".format(token)

    @classmethod
    def _build_non_body_payloads(cls, namespace):
        """
        Build query params and header params for http requests.

        Loop through all arguments provided from argparse and assign them to their appropriate payload.
        :param namespace: The parsed arguments from argparse.
        :return: Properly formatted query params and header params for http request.
        """
        endpoint_info = cls._get_endpoint_info()
        query_payload = {}
        body_payload = {}
        header_payload = {}
        for (arg_name, arg) in namespace.items():
            # If the argument is positional, belongs in path, not a payload
            if arg_name not in endpoint_info["options"]:
                continue

            if endpoint_info['body_params'].get(arg_name, None):
                # Check that it conforms to the right schema
                try:
                    jsonschema.validate(arg, endpoint_info['body_params'][arg_name])
                except jsonschema.ValidationError as e:
                    print(e)
                    raise ValueError("Argument {} has an invalid input type.".format(arg_name))

                # If it does, set the payload to the given input.
                body_payload[arg_name] = arg
                continue

            payload_format = endpoint_info["options"][arg_name]["in"]
            hierarchy = endpoint_info["options"][arg_name]["hierarchy"]
            if payload_format == "query":
                cls._add_arg(arg, query_payload, hierarchy)
            if payload_format == "header":
                cls._add_arg(arg, header_payload, hierarchy)

        header_payload['Authorization'] = cls._get_auth_header()
        return query_payload, body_payload, header_payload

    @classmethod
    def run_cli(cls, args):
        """Run this command using args from the cli. Override this to add higher-level commands."""
        body_payload = cls._build_body_payload(args)
        args.update(body_payload)
        return cls.run(args)

    @classmethod
    def run(cls, args):
        """Function that will be exposed to the api users."""
        endpoint_name = cls.get_command_name()

        split_endpoint = endpoint_name.split("-")[1]
        query_route = [split_endpoint]
        query_route.extend(cls._get_ordered_path_args(args))

        base_url = args.get('api_url', cls._get_base_url())
        url = base_url + "/" + "/".join(query_route)

        query_payload, body_payload, header_payload = cls._build_non_body_payloads(args)

        param_methods = ["get", "options", "head", "delete"]
        json_methods = ["post", "put", "patch"]
        method = endpoint_name[:endpoint_name.find("-")]

        if method in param_methods:
            request = requests.request(
                method,
                url,
                params=query_payload,
                headers=header_payload,
                stream=args.get('stream', False)
            )
        elif method in json_methods:
            request = requests.request(
                method,
                url,
                json=body_payload,
                params=query_payload,
                headers=header_payload,
                stream=args.get('stream', False)
            )
        else:
            raise ValueError("Bad request type")
        return request
