import json
from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

bundle = dss.get_bundle(replica="aws",
                        uuid='fff746b3-e3eb-496a-88a3-5fa1fa358392',
                        version='2019-08-01T200147.130156Z')

print('Bundle Contents:')
for file in bundle["bundle"]["files"]:
    print(f'File: {json.dumps(file, indent=4)}')

print(f'Bundle Creator: {bundle["bundle"]["creator_uid"]}')
print(f'Bundle UUID   : {bundle["bundle"]["uuid"]}')
print(f'Bundle Version: {bundle["bundle"]["version"]}')
