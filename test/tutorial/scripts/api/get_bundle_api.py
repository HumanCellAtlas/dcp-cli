import json
from hca.dss import DSSClient

dss = DSSClient()

bundle = dss.get_bundle(replica="aws",
                        uuid='fff746b3-e3eb-496a-88a3-5fa1fa358392',
                        version='2019-08-01T200147.130156Z')

print('Bundle Contents:')
for file in bundle["bundle"]["files"]:
    print(f'File: {json.dumps(file, indent=4)}')

print(f'Bundle Creator: {bundle["bundle"]["creator_uid"]}')
print(f'Bundle UUID   : {bundle["bundle"]["uuid"]}')
print(f'Bundle Version: {bundle["bundle"]["version"]}')
