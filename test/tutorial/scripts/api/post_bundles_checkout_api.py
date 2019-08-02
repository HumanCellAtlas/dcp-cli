from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

checkout_id = dss.post_bundles_checkout(uuid='fff746b3-e3eb-496a-88a3-5fa1fa358392', replica="aws")
print(checkout_id)
