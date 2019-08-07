from hca.dss import DSSClient

dss = DSSClient()

dss.download(
    bundle_uuid="ffffaf55-f19c-40e3-aa81-a6c69d357265",
    version="2019-08-01T200147.836832Z",
    replica="aws",
    download_dir="download_test",
)
