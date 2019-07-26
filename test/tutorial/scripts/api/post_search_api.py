from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

# Iterates through bundles.
for results in dss.post_search.iterate(replica="aws", es_query={}):
    print(results)
    break

# Outputs the first page of bundles.
print(dss.post_search(replica='aws', es_query={}))