from hca.dss import DSSClient

dss = DSSClient()

UUID = "ffffaf55-f19c-40e3-aa81-a6c69d357265"
VERSION = "ffffaf55-f19c-40e3-aa81-a6c69d357265"

# Download the metadata only
dss.download(
    bundle_uuid=UUID,
    version=VERSION,
    replica="aws",
    download_dir=".hca_metadata_only"
)

# Download the data only
dss.download(
    bundle_uuid=UUID,
    version=VERSION,
    replica="aws",
    download_dir=".hca_data_only"
)
