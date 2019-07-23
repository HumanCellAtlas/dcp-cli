from hca import HCAConfig
from hca.dss import DSSClient
import sys

hca_config = HCAConfig()
hca_config[
    "DSSClient"
].swagger_url = f"https://dss.data.humancellatlas.org/v1/swagger.json"
dss = DSSClient(config=hca_config)

# .create_version()
# Generates a timestamp in that can be used for versioning.
# api Output: '2019-07-08T233341.765030'
dss.create_version()

# .login()
# Command may open a browser window to ask for your conesent to use
# web service authentication credentials.
access_token = "test_access_token"
dss.login(access_token=access_token)

# .refresh_swagger():
# Refreshes Swagger document. Can help resolve errors communicate with the API.
dss.refresh_swagger()


# get_bundles_checkout, download, get_bundle
# .post-serach():
# JSON query and returns matching bundle identifiers.
for results in dss.post_search.iterate(replica="aws", es_query={}):
    uuid, version = results["bundle_fqid"].split(".", 1)
    try:
        # .post_checkout()
        # Initiate asynchronous checkout of a bundle.
        # api Output:
        # {
        #   "checkout_job_id": "6a7438be-3998-4f1b-807c-7848dceaf351"
        # }
        s = f"Bundle: {uuid}.{version}\n"
        checkout_id = dss.post_bundles_checkout(uuid=uuid, replica="aws")[
            "checkout_job_id"
        ]

        # .get_bundles_checkout()
        # A JSON response that displays status and/or location of checkout.
        bundle_checkout_status = dss.get_bundles_checkout(
            replica="aws", checkout_job_id=checkout_id
        )["status"]
        print(checkout_id + " " + bundle_checkout_status)

        # .download()
        # Download a bundle and save it to the local filesystem as a directory.
        dss.download(
            bundle_uuid=uuid,
            replica="aws",
            version=version,
            download_dir="./download_test",
        )

        # .get_bundle()
        # Retrieves a bundle given a UUID and optionally a version.
        files_uuid = []
        for bundle in dss.get_bundle(replica="aws", uuid=uuid, version=version)[
            "bundle"
        ]["files"]:
            file_version = bundle["version"]
            file_uuid = bundle["uuid"]
            file_name = bundle["name"]
            file_sha256 = bundle["sha256"]
            files_uuid.append(file_uuid)
            s += f" File: {file_name} \n"
            s += f"   Sha_256:{file_sha256} \n"
            s += f"     UUID/Version:{file_uuid}.{file_version} \n"
        print(s[:-1])
        break
    except:
        pass  # print(f'Does not exist: {uuid}.{version}')


for file_uuid in files_uuid:
    # .get_file():
    # Given a file UUID, return latest version of the file.
    try:
        fh = dss.get_file(replica="aws", uuid=file_uuid)
        print(dss.head_file(uuid=file_uuid, replica="aws"))
        print(fh["describedBy"] + " \n   type:" + fh["schema_type"])
    except TypeError:
        pass

# print("UPLOADING")

# STILL RUNS INTO 500 ERROR BUT STILL GOES THROUGH
# dss.upload(
#     src_dir="./upload_test",
#     replica="aws",
#     staging_bucket="jeffwu-test",
#     timeout_seconds=1200,
# )

# .logout()
# Clear sphinx-build dss authentication credentials previously
# configured with sphinx-build dss login
dss.logout()
