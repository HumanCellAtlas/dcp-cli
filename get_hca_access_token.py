"""Save access token to $HCA_ACCESS_TOKEN for Travis. Run with $(python get_hca_access_token.py)."""
from google import auth
from google.auth.transport.requests import Request

creds, _ = auth.default(scopes=["https://www.googleapis.com/auth/userinfo.email"])

r = Request()
creds.refresh(r)
r.session.close()

print("export HCA_ACCESS_TOKEN={}".format(creds.token))
