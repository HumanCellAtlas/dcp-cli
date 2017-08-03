"""Utility for making samples. 

Modified from https://github.com/google/google-api-python-client/blob/master/googleapiclient/sample_tools.py

Key modifications: 

1. Check if os.isatty() before launching browser.
2. Only launch browser if Credentials is none - otherwise, try to refresh token. 
"""
from __future__ import absolute_import

import os
import sys

from oauth2client import client
from oauth2client import file
from oauth2client import tools


def get_access_token(name, filename, scope=None):
    """A common initialization routine for samples.

    Many of the sample applications do the same initialization, which has now
    been consolidated into this function. This function uses common idioms found
    in almost all the samples, i.e. for an API with name 'apiname', the
    credentials are stored in a file named apiname.dat, and the
    client_secrets.json file is stored in the same directory as the application
    main file.

    Args:
        name: string, name of the API.
        filename: string, filename of the application. Usually set to __file__.
        scope: string, The OAuth scope used.

    Returns:
        A tuple of (service, flags), where service is the service object and flags
        is the parsed command-line flags.
    """
    if scope is None:
        scope = 'https://www.googleapis.com/auth/' + name

    # Name of a file containing the OAuth 2.0 information for this
    # application, including client_id and client_secret, which are found
    # on the API Access tab on the Google APIs
    # Console <http://code.google.com/apis/console>.
    client_secrets = os.path.join(os.path.dirname(filename),
                                  'client_secrets.json')

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(client_secrets,
                                          scope=scope,
                                          message=tools.message_if_missing(client_secrets))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage(name + '.dat')
    credentials = storage.get()

    if not credentials:
        if sys.stdin.isatty():
            flow = client.flow_from_clientsecrets(client_secrets,
                                                  scope=scope,
                                                  message=tools.message_if_missing(client_secrets))
            credentials = tools.run_flow(flow, storage)
        else:
            raise Exception("Store JSON-formatted oauth2client.client.OAuth2Credentials in {}.dat!".format(name))

    return credentials.get_access_token()
