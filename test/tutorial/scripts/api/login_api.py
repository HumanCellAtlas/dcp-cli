from hca.dss import DSSClient

dss = DSSClient()

access_token = "test_access_token"
dss.login(access_token=access_token)
