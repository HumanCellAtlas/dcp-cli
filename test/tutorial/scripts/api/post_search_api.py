from hca import HCAConfig
from hca.dss import DSSClient
import sys

hca_config = HCAConfig()
hca_config[
    "DSSClient"
].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

# get_bundles_checkout, download, get_bundle
# .post-serach():
# JSON query and returns matching bundle identifiers.
for results in dss.post_search.iterate(replica="aws", es_query={}):
    print(results)
    break