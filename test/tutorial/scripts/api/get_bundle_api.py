from hca import HCAConfig
from hca.dss import DSSClient
import sys

hca_config = HCAConfig()
hca_config[
    "DSSClient"
].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

files_uuid = []
s = ''
for bundle in dss.get_bundle(replica="aws", uuid='ffffa79b-99fe-461c-afa1-240cbc54d071', version='2019-03-26T130456.302299Z')[
    "bundle"
]["files"]:
    file_version = bundle["version"]
    file_uuid = bundle["uuid"]
    file_name = bundle["name"]
    file_sha256 = bundle["sha256"]
    files_uuid.append(file_uuid)
    s += f" File: {file_name} \n"
    s += f"   Sha_256:{file_sha256} \n"
    s += f"     UUID/Version:{file_uuid}.{file_version} \n"
print(s[:-1])

# ffffa79b-99fe-461c-afa1-240cbc54d071.2019-03-26T130456.302299Z