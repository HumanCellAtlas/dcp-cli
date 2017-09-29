import argparse
import json
import logging
import os
import re
import sys

import jsonschema
import requests
import six
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials as OAuth2Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from tweak import Config

from .. import TWEAK_PROJECT_NAME
from .cli import parse_args
from .constants import Constants


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
                help=positional_arg['description'],
                type=argtype
            )

    @classmethod
    def _add_optional_args(cls, subparser):
        endpoint_info = cls._get_endpoint_info()
        for optional_name, optional_data in endpoint_info.get('options', {}).items():
            argtype = cls._get_arg_type(optional_data['type'])
            actiontype = cls._get_action(optional_data['type'])

            optional_name_with_dashes = optional_name.replace("_", "-")
            subparser.add_argument(
                "--" + optional_name_with_dashes,
                dest=optional_name,  # So we can send correctly formatted objects to api.
                metavar=optional_data['metavar'],
                required=optional_data['required'],
                nargs="+" if optional_data['array'] else None,
                help=optional_data['description'],
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
        subparser.set_defaults(func=cls.run_from_cli)

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

            payload_format = endpoint_info['options'][arg_name].get('in', None)
            if payload_format == "body":
                hierarchy = endpoint_info["options"][arg_name]["hierarchy"]
                cls._add_arg(arg, body_payload, hierarchy)
        return body_payload

    @classmethod
    def _get_auth_header(cls, args, retry=False):
        """
        Called in run when a user calls an authenticated method. retry=True if authenticated method returns 401.

        :param args: Dict of arguments for any given function.
        :param retry: Boolean indicating if this is the second time trying to authenticate. If so, refresh token.
        """
        token = cls._get_access_token(args, retry)
        return {'Authorization': "Bearer {}".format(token)}

    @classmethod
    def _get_access_token(cls, args, retry):
        config = Config(TWEAK_PROJECT_NAME, autosave=True)

        # kwargs access_token input
        if 'access_token' in args.get('kwargs', {}):
            if retry:
                logging.info("Access token taken from kwargs invalid.")
                raise ValueError("The supplied access token is not valid."
                                 " Please refresh or run `hca login`"
                                 " to get a more permanent hca configuration.")
            else:
                logging.info("Found access token in kwargs.")
                access_token = args['kwargs']['access_token']

        # Checking config
        elif config.get('login', None) and config.login.get('access_token', None):
            # There is a refresh token
            if retry and config.login.get('refresh_token', None):
                logging.info("The access token stored in {} is not valid."
                             " Attempting with refresh token.".format(config.config_files[-1]))
                credentials = OAuth2Credentials(
                    token=None,
                    client_id=config.login.client_id,
                    client_secret=config.login.client_secret,
                    scopes=["https://www.googleapis.com/auth/userinfo.email"],
                    refresh_token=config.login.refresh_token,
                    token_uri=config.login.token_uri,
                )

                r = GoogleAuthRequest()
                credentials.refresh(r)
                r.session.close()

                config.login.access_token = credentials.token
                access_token = credentials.token
            # No refresh token
            elif retry:
                logging.info("The access token stored in {} is not valid and there is"
                             " no supplied refresh token.".format(config.config_files[-1]))
                raise ValueError("The access_token in your config file is invalid"
                                 " and there is no refresh_token to refresh it."
                                 " You may run `hca login` to easily reset your"
                                 " hca configuration.")
            # First attempt
            else:
                logging.info("Found access token in {}.".format(config.config_files[-1]))
                access_token = config.login.access_token

        # Service account handling
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            logging.info("Found GOOGLE_APPLICATION_CREDENTIALS environment variable."
                         " Grabbing service account credentials from there.")
            service_account_credentials_filename = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

            if not os.path.isfile(service_account_credentials_filename):
                raise EnvironmentError(
                    "File {} (pointed by GOOGLE_APPLICATION_CREDENTIALS"
                    " environment variable) does not exist!".format(service_account_credentials_filename))

            service_account_credentials = ServiceAccountCredentials.from_service_account_file(
                service_account_credentials_filename,
                scopes=["https://www.googleapis.com/auth/userinfo.email"]
            )

            r = GoogleAuthRequest()
            service_account_credentials.refresh(r)
            r.session.close()

            access_token = service_account_credentials.token

        else:
            raise ValueError("Run `hca login` or export GOOGLE_APPLICATION_CREDENTIALS environment variable"
                             " to load credentials. See <Insert doc here>")

        return access_token

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
        for arg_name, arg in namespace.items():
            # If the argument is positional, belongs in path, not a payload
            if arg_name not in endpoint_info["options"]:
                continue

            if endpoint_info['body_params'].get(arg_name, None):
                # Check that it conforms to the right schema
                try:
                    jsonschema.validate(arg, endpoint_info['body_params'][arg_name])
                except jsonschema.ValidationError as e:
                    raise ValueError("Argument {} has an invalid input type.".format(arg_name), e)

                # If it does, set the payload to the given input.
                body_payload[arg_name] = arg
                continue

            payload_format = endpoint_info["options"][arg_name]["in"]
            hierarchy = endpoint_info["options"][arg_name]["hierarchy"]
            if payload_format == "query":
                cls._add_arg(arg, query_payload, hierarchy)
            if payload_format == "header":
                cls._add_arg(arg, header_payload, hierarchy)

        return query_payload, body_payload, header_payload

    @classmethod
    def run_from_cli(cls, argparser_args):
        """Run this command using args from the cli. Override this to add higher-level commands."""
        args_dict = parse_args(argparser_args)
        body_payload = cls._build_body_payload(args_dict)
        args_dict.update(body_payload)
        response = cls.run(args_dict)
        cls._render_output(response)

    @classmethod
    def run(cls, args):
        """Function that will be exposed to the api users."""
        endpoint_name = cls.get_command_name()

        split_endpoint = endpoint_name.split("-")[1]
        query_route = [split_endpoint]
        query_route.extend(cls._get_ordered_path_args(args))

        kwargs = args.get('kwargs', {})
        base_url = kwargs.get('api_url', cls._get_base_url())
        url = base_url + "/" + "/".join(query_route)

        query_payload, body_payload, header_payload = cls._build_non_body_payloads(args)

        param_methods = ["get", "options", "head", "delete"]
        json_methods = ["post", "put", "patch"]
        method = endpoint_name[:endpoint_name.find("-")]

        if method not in json_methods and method not in param_methods:
            raise ValueError("Bad request type")

        request_args = {
            'method': method,
            'url': url,
            'params': query_payload,
            'headers': header_payload,
            'json': body_payload if method in json_methods else None,
            'stream': args.get('stream', True)  # Default to stream
        }

        requires_auth = cls._get_endpoint_info().get('requires_auth', False)

        if requires_auth:
            header_payload.update(cls._get_auth_header(args))

        response = requests.request(**request_args)

        # Maybe auth didn't work. Refresh token and try again.
        if response.status_code == requests.codes.unauthorized and requires_auth:
            header_payload.update(cls._get_auth_header(args, True))
            response = requests.request(**request_args)

        return response

    @classmethod
    def _render_output(cls, response):
        if isinstance(response, requests.Response):
            for chunk in response.iter_content(chunk_size=Constants.CHUNK_SIZE, decode_unicode=True):
                if chunk:  # filter out keep-alive new chunks
                    if six.PY3:
                        sys.stdout.buffer.write(chunk)
                    else:
                        sys.stdout.write(chunk)
        elif isinstance(response, dict):
            print(json.dumps(response))
        elif isinstance(response, str):
            print(response)
        else:  # Unicode
            print(response.decode())
