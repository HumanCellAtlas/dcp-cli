from hca import HCAConfig
from hca.dss import DSSClient
import json

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)


json_response = dss.get_file(replica="aws", uuid="666ff3f0-67a1-4ead-82e9-3f96a8c0a9b1")


for content in json_response:
    print(f'{content}: {json.dumps(json_response[content], indent=4)}')
