from hca import HCAConfig
from hca.dss import DSSClient
import uuid
import os

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

# Creates a new collection
collection = dss.put_collection(
    uuid=str(uuid.uuid4()),
    version="2018-09-17T161441.564206Z",  # arbitrary
    description="foo",
    details={},
    replica="aws",
    name="bar",
    contents=[
        {
            "type": "bundle",
            "uuid": "ff818282-9735-45fa-a094-e9f2d3d0a954",  # overwrite if necessary
            "version": "2019-08-06T170839.843085Z",  # arbitrary
            "path": "https://dss.dev.data.humancellatlas.org/v1/bundles/ff818282-9735-45fa-a094-e9f2d3d0a954?version=2019-08-06T170839.843085Z&replica=aws",
        }
    ],
)

uuid, version = collection["uuid"], collection["version"]

# Gets a list of collections
print(dss.get_collections(replica="aws"))

# Can add/remove files from a collection
print(dss.patch_collection(replica="aws", uuid=uuid, version=version))

# Gets a collection based on replcia and uuid
print(dss.get_collection(replica="aws", uuid=uuid))

# Deletes a colelction based on replica and uuid
print(dss.delete_collection(replica="aws", uuid=uuid))
