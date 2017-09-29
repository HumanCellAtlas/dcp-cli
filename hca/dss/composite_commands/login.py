from __future__ import absolute_import, division, print_function, unicode_literals

import sys

import requests
from google_auth_oauthlib.flow import InstalledAppFlow as GoogleAuthFlow
from tweak import Config

from ... import TWEAK_PROJECT_NAME
from ..added_command import AddedCommand
from ..constants import Constants
from ..cli import parse_args


class Login(AddedCommand):
    """Functions needed to fully add this functionality to the command line parser."""

    @classmethod
    def _get_endpoint_info(cls):
        return {
            'body_params': {},
            'description': "Setup authentication credentials. If you give access_token"
                           " and refresh_token then these will be saved to config file."
                           " If not and you're using a terminal, a browser will pop up for"
                           " you to sign in to Google to grant oauth credentials. This is"
                           " the recommended usage pattern. Otherwise,"
                           " this will raise an exception.",
            'positional': [],
            'options': {
                'access_token': {
                    'description':
                        "A Google OAuth access token with https://www.googleapis.com/auth/userinfo.email scope"
                        " Using this parameter will set the config access_token, but when it has expired there"
                        " it will not automatically refresh.",
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False
                }
            }
        }

    @classmethod
    def run_from_cli(cls, argparser_args):
        """Run this command using args from the cli. Override this to add higher-level commands."""
        args_dict = parse_args(argparser_args)
        response = cls.run(args_dict)
        cls._render_output(response)

    @classmethod
    def run(cls, args):
        """Authenticate to the Data Store using OAuth2."""
        client_secrets = requests.get(Constants.APPLICATION_SECRETS_ENDPOINT).json()

        config = Config(TWEAK_PROJECT_NAME, autosave=True)
        config.login = {}
        config.login.client_id = client_secrets['installed']['client_id']
        config.login.client_secret = client_secrets['installed']['client_secret']
        config.login.token_uri = client_secrets['installed']['token_uri']

        if args.get('access_token', None):
            config.login.access_token = args['access_token']
            config.login.refresh_token = None

        elif sys.stdin.isatty():
            flow = GoogleAuthFlow.from_client_config(
                client_secrets,
                scopes=["https://www.googleapis.com/auth/userinfo.email"]
            )
            credential = flow.run_local_server()

            config.login.access_token = credential.token
            config.login.refresh_token = credential.refresh_token

        else:
            raise Exception("You have to be in a terminal or provide an access_token for this command to work.")

        return {'completed': True}
