from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import socket
import sys
from io import open

import oauth2client
import oauth2client.client
import oauth2client.tools
import requests
from tweak import Config

from ...added_command import AddedCommand
from ...constants import Constants


_FAILED_START_MESSAGE = """
Failed to start a local webserver listening on either port 8080
or port 8090. Please check your firewall settings and locally
running programs that may be blocking or using those ports.
Falling back to authorization with no webserver.
"""

_BROWSER_OPENED_MESSAGE = """
Your browser has been opened to visit:
    {address}
If your browser is on a different machine then exit and re-run this
command with the access_token and refresh_token parameters.
"""

_GO_TO_LINK_MESSAGE = """
Go to the following link in your browser:
    {address}
"""


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
                        "A Google OAuth access token with https://www.googleapis.com/auth/userinfo.email scope",
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False
                },
                'refresh_token': {
                    'description':
                        "A Google OAuth refresh token with https://www.googleapis.com/auth/userinfo.email scope",
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False,
                }
            }
        }

    @classmethod
    def _get_credential_from_popup(cls, client_secrets_file_path):
        """
        Function to popup browser and grab user credentials.

        Taken mostly from https://github.com/google/oauth2client/blob/master/oauth2client/tools.py
        Not just importing the package because it requires a user to write a credentials file
        and some of the error messaging is not relevant to running it from within this application.
        """

        flow = oauth2client.client.flow_from_clientsecrets(
            client_secrets_file_path,
            scope="https://www.googleapis.com/auth/userinfo.email",
            message=oauth2client.tools.message_if_missing(client_secrets_file_path)
        )

        success = False
        port_number = 0

        auth_host_name = "localhost"
        auth_host_port = [8080, 8090]

        for port in auth_host_port:
            port_number = port
            try:
                httpd = oauth2client.tools.ClientRedirectServer(
                    (auth_host_name, port),
                    oauth2client.tools.ClientRedirectHandler
                )
            except socket.error:
                pass
            else:
                success = True
                break
        if not success:
            print(_FAILED_START_MESSAGE)

        if success:
            oauth_callback = 'http://{host}:{port}/'.format(
                host=auth_host_name, port=port_number)
        else:
            oauth_callback = oauth2client.client.OOB_CALLBACK_URN
        flow.redirect_uri = oauth_callback
        authorize_url = flow.step1_get_authorize_url()

        if success:
            import webbrowser
            webbrowser.open(authorize_url, new=1, autoraise=True)
            print(_BROWSER_OPENED_MESSAGE.format(address=authorize_url))
        else:
            print(_GO_TO_LINK_MESSAGE.format(address=authorize_url))

        code = None
        if success:
            httpd.handle_request()
            if 'error' in httpd.query_params:
                sys.exit('Authentication request was rejected.')
            if 'code' in httpd.query_params:
                code = httpd.query_params['code']
            else:
                print('Failed to find "code" in the query parameters '
                      'of the redirect.')
                sys.exit('Try setting access_token and refresh_token in the console.')
        else:
            code = input('Enter verification code: ').strip()

        try:
            credential = flow.step2_exchange(code)
        except oauth2client.client.FlowExchangeError as e:
            sys.exit('Authentication has failed: {0}'.format(e))

        print('Authentication successful.')

        return json.loads(credential.to_json())

    @classmethod
    def run_cli(cls, args):
        """Download a bundle/file from blue box to local with arguments given from cli."""
        return cls.run(args)

    @classmethod
    def run(cls, args):
        """Download a bundle or file from the blue box to local."""
        client_secrets = requests.get("https://hca-dss.czi.technology/internal/application_secrets").json()

        config = Config(Constants.TWEAK_PROJECT_NAME)
        config.client_id = client_secrets['installed']['client_id']
        config.client_secret = client_secrets['installed']['client_secret']
        config.token_uri = client_secrets['installed']['token_uri']

        if 'access_token' in args or 'refresh_token' in args:
            config.access_token = args.get('access_token', None)
            config.refresh_token = args.get('refresh_token', None)

        elif sys.stdin.isatty():
            home_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            client_secrets_file_path = os.path.join(home_dir, "util", "client_secrets.json")

            # flow_from_clientsecrets requires a file path.
            with open(client_secrets_file_path, "w") as cs:
                cs.write(json.dumps(client_secrets))

            credential = cls._get_credential_from_popup(client_secrets_file_path)

            # client_secrets.json shouldn't stick around
            if os.path.exists(client_secrets_file_path):
                os.remove(client_secrets_file_path)

            config.access_token = credential['access_token']
            config.refresh_token = credential['refresh_token']

        return {'hello': "world"}
