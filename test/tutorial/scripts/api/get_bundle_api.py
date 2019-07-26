from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

files_uuid = []
s = ''
for bundle in dss.get_bundle(replica="aws", uuid='ffffa79b-99fe-461c-afa1-240cbc54d071', version='2019-03-26T130456.30\
2299Z')["bundle"]["files"]:
    print(bundle)
print(s[:-1])