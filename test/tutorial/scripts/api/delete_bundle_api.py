from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

print(dss.delete_bundle(reason='test', uuid='98f6c379-cb78-4a61-9310-f8cc0341c0ea', version='2019-08-02T202456.025543Z', replica='aws'))
