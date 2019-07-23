from hca import HCAConfig
from hca.dss import DSSClient
import sys

hca_config = HCAConfig()
hca_config[
    "DSSClient"
].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)
# .login()
# Command may open a browser window to ask for your conesent to use
# web service authentication credentials.
access_token = "test_access_token"
dss.login(access_token=access_token)