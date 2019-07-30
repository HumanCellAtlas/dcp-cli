from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

checkout_id = dss.post_bundles_checkout(uuid='fbafd0e3-b3bf-40da-9bf4-9596989800d8', replica="aws")
print(checkout_id)
