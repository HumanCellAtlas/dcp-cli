from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

# Creates a sub based given a replica and a url
subscription = dss.put_subscription(
    replica="aws",
    callback_url=" https://dcp-cli-tutorials-put-delete-get-sub-api.humancellatlas.org`"
)

callback, owner, replica, uuid = (
    subscription["callback_url"],
    subscription["owner"],
    subscription["replica"],
    subscription["uuid"],
)

# Lists all subs created
print(dss.get_subscriptions(replica="aws"))

# Lists a sub
print(dss.get_subscription(replica="aws", uuid=uuid))

# Deletes a sub based on a UUID
print(dss.delete_subscription(replica="aws", uuid=uuid))
