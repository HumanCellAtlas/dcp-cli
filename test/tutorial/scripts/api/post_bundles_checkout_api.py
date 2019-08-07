from hca.dss import DSSClient

dss = DSSClient()

checkout_id = dss.post_bundles_checkout(uuid='fff746b3-e3eb-496a-88a3-5fa1fa358392', replica="aws")
print(checkout_id)
