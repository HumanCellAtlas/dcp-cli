from urllib.parse import urljoin

import argparse
import requests

from hca.auth import AuthClient

client = AuthClient()
config = get_config()

def application_secrets():

    if "application_secrets" not in config:
        # TODO we need to use the same secret for any service using the HCA CLI
        app_secrets_url = "https://{}/internal/application_secrets".format(self._swagger_spec["host"])
        config.application_secrets = requests.get(app_secrets_url).json()
    return config.application_secrets


def logout(revoke=False):
    """
    Clear {prog} authentication credentials previously configured with ``{prog} login``.

    If revoke is True all refresh tokens will be revoked for the user. This should be used if the system has been
    compromised.
    """
    for keys in ["application_secrets", "oauth2_token"]:
        try:
            del config[keys]
        except KeyError:
            pass


def login(access_token="", remote=False, stay_logged_in=False):
    """
    Configure and save {prog} authentication credentials.

    This command may open a browser window to ask for your
    consent to use web service authentication credentials.

    Use --remote if using the CLI in a remote environment
    Use --stay-logged-in to generate a refresh token that will be used to automatically retrieve new credentials
    when current credentials expire. Only use this if the system you are using is secure.
    """
    if access_token:
        credentials = argparse.Namespace(token=access_token, refresh_token=None, id_token=None)
    else:
        scopes = ["openid", "email", "offline_access"]
        if remote:
            import google_auth_oauthlib.flow
            application_secrets = application_secrets()
            redirect_uri = urljoin(application_secrets['installed']['auth_uri'], "/echo")
            flow = google_auth_oauthlib.flow.Flow.from_client_config(application_secrets, scopes=scopes,
                                                                     redirect_uri=redirect_uri)

            authorization_url, _ = flow.authorization_url()
            print("please authenticate at the url: {}".format(authorization_url))
            code = input("pass 'code' value from within query_params: ")
            flow.fetch_token(code=code)
            credentials = flow.credentials
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_config(application_secrets, scopes=scopes)
            msg = "Authentication successful. Please close this tab and run HCA CLI commands in the terminal."
            credentials = flow.run_local_server(success_message=msg, audience=_audience)

    # TODO: (akislyuk) test token autorefresh on expiration
    config.oauth2_token = dict(access_token=credentials.token,
                                    refresh_token=credentials.refresh_token,
                                    id_token=credentials.id_token,
                                    expires_at="-1",
                                    token_type="Bearer")
    print("Storing access credentials")