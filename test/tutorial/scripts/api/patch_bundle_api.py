from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

print(dss.patch_bundle(replica="aws", uuid='38f6c379-cb78-4a61-9310-f8cc0341c0ea', version='2019-07-30T164352.961501Z'))
