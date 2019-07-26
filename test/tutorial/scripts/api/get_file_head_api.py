from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

print(dss.head_file(uuid="6887bd52-8bea-47d9-bbd9-ff71e05faeee", replica="aws"))

# Can add optional version
print(dss.head_file(uuid="6887bd52-8bea-47d9-bbd9-ff71e05faeee", replica="aws", version='2019-01-30T165057.189000Z'))

