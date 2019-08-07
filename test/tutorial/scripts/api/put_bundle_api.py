from hca import HCAConfig
from hca.dss import DSSClient


hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

dss.put_bundle(
    creator_uid=0,
    uuid="98f6c379-cb78-4a61-9310-f8cc0341c0ea",
    version="2019-08-02T202456.025543Z",
    replica="aws",
    files=[
        {
            "uuid": "2196a626-38da-4489-8b2f-645d342f6aab",
            "version": "2019-07-10T001103.121000Z",
            "name": "process_1.json1",
            "indexed": False,
        }
    ],
)
