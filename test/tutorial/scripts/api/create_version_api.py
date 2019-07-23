from hca import HCAConfig
from hca.dss import DSSClient
import sys

hca_config = HCAConfig()
hca_config[
    "DSSClient"
].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

# .create_version()
# Generates a timestamp in that can be used for versioning.
# api Output: '2019-07-08T233341.765030'
dss.create_version()