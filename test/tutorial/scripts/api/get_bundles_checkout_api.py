from hca import HCAConfig
from hca.dss import DSSClient

hca_config = HCAConfig()
hca_config["DSSClient"].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

bundle_checkout_status = dss.get_bundles_checkout(replica="aws",
                                                  checkout_job_id='4de1c603-fa8b-4c07-af37-06159e6951e0')

print(f'Bundle checkout status: {bundle_checkout_status["status"]}!')
if bundle_checkout_status["status"] == 'SUCCEEDED':
    print(f'File is located at: {bundle_checkout_status["location"]}')
