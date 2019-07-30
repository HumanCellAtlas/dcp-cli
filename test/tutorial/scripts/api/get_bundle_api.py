import json
from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

bundle = dss.get_bundle(replica="aws",
                        uuid='ffffa79b-99fe-461c-afa1-240cbc54d071',
                        version='2019-03-26T130456.302299Z')

print('Bundle Contents:')
for file in bundle["bundle"]["files"]:
    print(f'File: {json.dumps(file, indent=4)}')

print(f'Bundle Creator: {bundle["bundle"]["creator_uid"]}')
print(f'Bundle UUID   : {bundle["bundle"]["uuid"]}')
print(f'Bundle Version: {bundle["bundle"]["version"]}')
