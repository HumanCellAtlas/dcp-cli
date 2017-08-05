"""Utility for making samples.

Modified from https://github.com/google/google-api-python-client/blob/master/googleapiclient/sample_tools.py

Key modifications:

1. Check if os.isatty() before launching browser.
2. Only launch browser if Credentials is none - otherwise, try to refresh token.
"""
from __future__ import absolute_import

import argparse
import os
import sys
from io import open

from oauth2client import client
from oauth2client import file
from oauth2client import tools


def get_access_token(path_to_credentials_file, client_secrets_directory, scope):
    """A common initialization routine for samples.

    Many of the sample applications do the same initialization, which has now
    been consolidated into this function. This function uses common idioms found
    in almost all the samples, i.e. for an API with name 'apiname', the
    credentials are stored in a file named apiname.dat, and the
    client_secrets.json file is stored in the same directory as the application
    main file.

    Args:
        path_to_credentials_file: Path to the credentials file to load/store.
        client_secrets_directory: string, client_secrets_directory that will hold popup info. Usually set to __file__.
        scope: string, The OAuth scope used.

    Returns:
        A tuple of (service, flags), where service is the service object and flags
        is the parsed command-line flags.
    """
    # parent_parsers = [tools.argparser]
    # parser = argparse.ArgumentParser(
    #     description="hca cli",
    #     formatter_class=argparse.RawDescriptionHelpFormatter,
    #     parents=parent_parsers
    # )
    # flags = parser.parse_args([])

    # # Name of a file containing the OAuth 2.0 information for this
    # # application, including client_id and client_secret, which are found
    # # on the API Access tab on the Google APIs
    # # Console <http://code.google.com/apis/console>.
    # client_secrets = os.path.join(os.path.dirname(client_secrets_directory),
    #                               'client_secrets.json')

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    if not os.path.isfile(path_to_credentials_file):
        open(path_to_credentials_file, 'a').close()
    storage = file.Storage(path_to_credentials_file)
    credentials = storage.get()

    if not credentials:
        # HAS_JOSH_K_SEAL_OF_APPROVAL is an environment variable set in travis
        # that's very unique. Travis is a tty but should not expect an internet popup.
        # if sys.stdin.isatty() and 'HAS_JOSH_K_SEAL_OF_APPROVAL' not in os.environ:
        #     # Set up a Flow object that will bring people to a browser to authenticate.
        #     flow = client.flow_from_clientsecrets(client_secrets,
        #                                           scope=scope,
        #                                           message=tools.message_if_missing(client_secrets))
        #     credentials = tools.run_flow(flow, storage, flags)
        # else:
        try:
            credentials = client.GoogleCredentials.get_application_default()
            credentials.scopes = set([scope])

            storage.put(credentials)
            credentials.set_store(storage)

        except client.ApplicationDefaultCredentialsError:
            raise client.ApplicationDefaultCredentialsError(
                "Store JSON-formatted oauth2client.client.OAuth2Credentials in {}."
                .format(path_to_credentials_file)
            )

    return credentials.get_access_token()
