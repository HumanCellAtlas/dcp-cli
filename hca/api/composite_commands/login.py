from __future__ import absolute_import, division, print_function, unicode_literals

import sys

import requests
from google_auth_oauthlib.flow import InstalledAppFlow as GoogleAuthFlow
from tweak import Config

from ...added_command import AddedCommand
from ...constants import Constants


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
    def run_cli(cls, args):
        """Download a bundle/file from blue box to local with arguments given from cli."""
        return cls.run(args)

    @classmethod
    def run(cls, args):
        """Download a bundle or file from the blue box to local."""
        client_secrets = requests.get(Constants.APPLICATION_SECRETS_ENDPOINT).json()

        config = Config(Constants.TWEAK_PROJECT_NAME, autosave=True)
        config.client_id = client_secrets['installed']['client_id']
        config.client_secret = client_secrets['installed']['client_secret']
        config.token_uri = client_secrets['installed']['token_uri']

        if args.get('access_token', None):
            config.access_token = args['access_token']
            config.refresh_token = None

        elif sys.stdin.isatty():
            flow = GoogleAuthFlow.from_client_config(
                client_secrets,
                scopes=["https://www.googleapis.com/auth/userinfo.email"]
            )
            credential = flow.run_local_server()

            config.access_token = credential.token
            config.refresh_token = credential.refresh_token

        else:
            raise Exception("You have to be in a terminal or provide an access_token for this command to work.")

        return {'completed': True}
