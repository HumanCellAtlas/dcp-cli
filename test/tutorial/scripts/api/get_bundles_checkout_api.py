from hca.dss import DSSClient

dss = DSSClient()

bundle_checkout_status = dss.get_bundles_checkout(replica="aws",
                                                  checkout_job_id='4de1c603-fa8b-4c07-af37-06159e6951e0')

print(f'Bundle checkout status: {bundle_checkout_status["status"]}!')
if bundle_checkout_status["status"] == 'SUCCEEDED':
    print(f'File is located at: {bundle_checkout_status["location"]}')
