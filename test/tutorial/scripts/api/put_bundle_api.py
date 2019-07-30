from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

dss.put_bundle(
    creator_uid=0,
    uuid="38f6c379-cb78-4a61-9310-f8cc0341c0eb",
    version="2019-07-30T174916.268875Z",
    replica="aws",
    files=[
        {
            "uuid": "ead6434d-efb5-4554-98bc-027e160547c5",
            "version": "2019-07-30T174916.268875Z",
            "name": "get_bundle.json",
            "indexed": False,
        }
    ],
)
