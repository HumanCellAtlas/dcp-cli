from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

dss.download(
    bundle_uuid="ffffaf55-f19c-40e3-aa81-a6c69d357265",
    version="2019-08-01T200147.836832Z",
    replica="aws",
    download_dir="download_test",
)
