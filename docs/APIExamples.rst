=================
API Examples
=================

create_version()

Prints a timestamp in DSS_VERSION (ie 1985-04-12T232050.520000Z) that can be used for versioning.    
::
    from hca.dss import DSSClient

    dss = DSSClient()

    dss.create_version()

delete_bundle()

.. note:
    Privileged Users.

Deletes an already existing bundle given a UUID, version, and replica.
::
    from hca.dss import DSSClient

    dss = DSSClient()

    print(dss.delete_bundle(reason='test', uuid='98f6c379-cb78-4a61-9310-f8cc0341c0ea', version='2019-08-02T202456.025543Z', replica='aws'))


download()

Download a bundle and save it to the local filesystem as a directory. By default, all data and metadata files are downloaded to 
cache / filestroe directory called '.hca'. 
::
    from hca.dss import DSSClient

    dss = DSSClient()

    dss.download(
        bundle_uuid="ffffaf55-f19c-40e3-aa81-a6c69d357265",
        version="2019-08-01T200147.836832Z",
        replica="aws",
        download_dir="download_test",
    )

        
download_manifest()

Files are downloaded to a cache / filestore directory called ‘.hca’. The directory is created in the current directory where download started and 
a copy of the manifest then written to the current directory.

Create a .tsv (tab-separated-file) file and input details given from get_bundle().

The header row must declare the following columns: 

bundle_uuid - the UUID of the bundle containing the file in DSS. 

bundle_version - the version of the bundle containing the file in DSS. 

file_name - the name of the file as specified in the bundle. 

file_uuid - the UUID of the file in the DSS. 

file_version - the version of the file.

file_sha256 - the SHA-256 hash of the file. file_size - the size of the file.

file_size - the size of the file
::
    from hca.dss import DSSClient
    import csv
    import json
    import pprint

    dss = DSSClient()

    with open("manifest.tsv", "w") as manifest:
        tsv = csv.DictWriter(
            manifest,
            fieldnames=(
                "bundle_uuid",
                "bundle_version",
                "file_name",
                "file_uuid",
                "file_version",
                "file_sha256",
                "file_size",
            ),
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
        )
        tsv.writeheader()

        with open("data/get_bundle.json") as jsonfile:
            try:
                data = json.load(jsonfile)
                bundle_uuid, bundle_version = (
                    data["bundle"]["uuid"],
                    data["bundle"]["version"],
                )
                pprint.pprint(data)
                for content in data["bundle"]["files"]:
                    if content["name"].endswith(".json"):
                        tsv.writerow(
                            dict(
                                bundle_uuid=bundle_uuid,
                                bundle_version=bundle_version,
                                file_name=content["name"],
                                file_uuid=content["uuid"],
                                file_version=content["version"],
                                file_sha256=content["sha256"],
                                file_size=content["size"],
                            )
                        )
            except ValueError as e:
                print("Not JSON FILE %s" % e)

    dss.download_manifest(replica="aws", manifest="manifest.tsv")

file_head()

Given a file UUID, return the metadata for the latest version of that file. 
If the version is provided, that version’s metadata is returned instead. 
The metadata is returned in the headers.
::
    from hca.dss import DSSClient

    dss = DSSClient()

    print(
        dss.head_file(
            uuid="6887bd52-8bea-47d9-bbd9-ff71e05faeee",
            replica="aws"
        )
    )

    # Can add optional version
    print(
        dss.head_file(
            uuid="6887bd52-8bea-47d9-bbd9-ff71e05faeee",
            replica="aws",
            version="2019-01-30T165057.189000Z",
        )
    )


get_bundle()

Given a bundle’s UUID and optionally a version, return the latest version. Displays details about the bundle and each file’s 
info such as name, UUID, version, etc.
::
    import json
    from hca.dss import DSSClient

    dss = DSSClient()

    bundle = dss.get_bundle(replica="aws",
                            uuid='fff746b3-e3eb-496a-88a3-5fa1fa358392',
                            version='2019-08-01T200147.130156Z')

    print('Bundle Contents:')
    for file in bundle["bundle"]["files"]:
        print(f'File: {json.dumps(file, indent=4)}')

    print(f'Bundle Creator: {bundle["bundle"]["creator_uid"]}')
    print(f'Bundle UUID   : {bundle["bundle"]["uuid"]}')
    print(f'Bundle Version: {bundle["bundle"]["version"]}')


get_bundles_checkout()

.. note:
    How to find the checkout-job-id? Run post-bundles-checkout in order to get checkout-job-id.

Check the status and location of a checkout request.    
::
    from hca.dss import DSSClient

    dss = DSSClient()

    bundle_checkout_status = dss.get_bundles_checkout(replica="aws",
                                                    checkout_job_id='4de1c603-fa8b-4c07-af37-06159e6951e0')

    print(f'Bundle checkout status: {bundle_checkout_status["status"]}!')
    if bundle_checkout_status["status"] == 'SUCCEEDED':
        print(f'File is located at: {bundle_checkout_status["location"]}')



get_file() 

Retrieve a file given a UUID, optionally a version, and displays details of the file.
::
    from hca.dss import DSSClient
    import json

    dss = DSSClient()

    json_response = dss.get_file(replica="aws", uuid="666ff3f0-67a1-4ead-82e9-3f96a8c0a9b1")


    for content in json_response:
        print(f'{content}: {json.dumps(json_response[content], indent=4)}')


login()

Configure and save authentication credentials.

This command may open a browser window to ask for your consent to use web service authentication credentials.
::
    from hca.dss import DSSClient

    dss = DSSClient()

    access_token = "test_access_token"
    dss.login(access_token=access_token)

logout()

Clear authentication credentials previously configured with login.    
::
    from hca.dss import DSSClient

    dss = DSSClient()

    dss.logout()

patch_bundle()

.. note ::
    Privileged Users

Allows user to pass in an optional list of files to add or remove from the the bundle. 

add_files/remove_files follow this format:
::
    [
        {
        "path": "string",
        "type": "string",
        "uuid": "string",
        "version": "string"
        }
    ]

::
    from hca import HCAConfig
    from hca.dss import DSSClient

    hca_config = HCAConfig()
    hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
    dss = DSSClient(config=hca_config)

    print(dss.patch_bundle(uuid='98f6c379-cb78-4a61-9310-f8cc0341c0ea', version='2019-08-02T202456.025543Z', replica='aws'))


post_bundles_checkout()

Returns a checkout-job-id (ie 4de1c603-fa8b-4c07-af37-06159e6951e0). This checkout-job-id can then
be used for get_bundles_checkout().
::
    from hca.dss import DSSClient

    dss = DSSClient()

    checkout_id = dss.post_bundles_checkout(uuid='fff746b3-e3eb-496a-88a3-5fa1fa358392', replica="aws")
    print(checkout_id)


post_search()

Find bundles by searching their metadata with an Elasticsearch query  
::
    from hca.dss import DSSClient

    dss = DSSClient()

    # Iterates through bundles.
    for results in dss.post_search.iterate(replica="aws", es_query={}):
        print(results)
        break

    # Outputs the first page of bundles.
    print(dss.post_search(replica='aws', es_query={}))

put_bundle()

.. note :: 
    Privileged Users

Creates a bundle. A bundle can contain a wide variety of files.

Inputs:

uuid: User creates a unique UUID.

creator-uid: Create a unique creator-uid. Any integer value is okay.

version: User creates a new version number. One can use create create_verson() to generate a DSS_VERSION.

replica: Choose a replica, either AWS or GCP.

files: Enter valid list of file objects, separated by commas, (ie `[{<first_file>} , {<second_file>}, ... ]` ) 
with the following details:

-Enter valid UUID of the file.

-Enter valid version number of the file.

-Enter the name of the file.

-Enter a boolean value whether the file is indexed or not.
::
    from hca.dss import DSSClient
    import os

    dss = DSSClient()

    dss.put_bundle(
        creator_uid=0,
        uuid="98f6c379-cb78-4a61-9310-f8cc0341c0ea",
        version="2019-08-02T202456.025543Z",
        replica="aws",
        files=[
            {
                "uuid": "2196a626-38da-4489-8b2f-645d342f6aab",
                "version": "2019-07-10T001103.121000Z",
                "name": "process_1.json1",
                "indexed": False,
            }
        ],
    )

put_file()

.. note :: 
    Privileged Users

Create a new version of a file given an existing UUID, verison, creator_uid, and soruce_url.
::
    from hca import HCAConfig
    from hca.dss import DSSClient

    hca_config = HCAConfig()
    hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
    dss = DSSClient(config=hca_config)

    print(
        dss.put_file(
            uuid="ead6434d-efb5-4554-98bc-027e160547c5",
            version="2019-07-30T174916.268875Z",
            creator_uid=0,
            source_url="s3://bucket-test/ead6434d-efb5-4554-98bc-027e160547c5/get_bundle.json",
        )
    )

(put/delete/patch/get)-collection and get-collections

.. note ::
    Privileged Users

get-collections: Get a list of users collections

put-collection: Create a collection for the user.

patch-collection: Allows user to pass in an optional list of files to add or remove from the collection. 

add-files/remove-files follow this format:
::
    [
        {
        "path": "string",
        "type": "string",
        "uuid": "string",
        "version": "string"
        }
    ]

get-collection: Given the UUID of the collection, show a collection that the user created. 

delete-collection: Given a UUID and rpelica or the subscription, delete the collection the user created. 
::
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


(put/delete/get)-subscription and get-subscriptions

get-subscritpions: Get a list of users subscriptions

put-subscription: Create a subscritpion for the user.

get-subscription: Given the UUID of the subscription, show a subscription that the user created. 

delete-subscription: Given a UUID and rpelica or the subscription, delete the subscription the user created. 
::
    from hca.dss import DSSClient

    dss = DSSClient()

    # Creates a sub based given a replica and a url
    subscription = dss.put_subscription(
        replica="aws", callback_url=" https://www.example.com"
    )

    callback, owner, replica, uuid = (
        subscription["callback_url"],
        subscription["owner"],
        subscription["replica"],
        subscription["uuid"],
    )

    # Lists all of subs created
    print(dss.get_subscriptions(replica="aws"))

    # List a sub
    print(dss.get_subscription(replica="aws", uuid=uuid))

    # Deletes a sub based on a UUID
    print(dss.delete_subscription(replica="aws", uuid=uuid))

(put/delete/get/patch)_collection() and get_collections()

.. note ::
    Privileged Users. 

Allows privileged user to create a collection, a bundle that can hold files, bundles, and other collections.
::
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


(put/delete/get)_subscription() and get_subscriptions()

get-subscritpions: Get a list of users subscription.

put-subscription: Create a collection for the user.

get-subscription: Given the UUID of the subscription, show a subscription that the user created. 

delete-subscription: Given a UUID and rpelica or the subscription, delete the subscription the user created. 
::
    from hca.dss import DSSClient

    dss = DSSClient()

    # Creates a sub based given a replica and a url
    subscription = dss.put_subscription(
        replica="aws", callback_url=" https://www.example.com"
    )

    callback, owner, replica, uuid = (
        subscription["callback_url"],
        subscription["owner"],
        subscription["replica"],
        subscription["uuid"],
    )

    # Lists all of subs created
    print(dss.get_subscriptions(replica="aws"))

    # List a sub
    print(dss.get_subscription(replica="aws", uuid=uuid))

    # Deletes a sub based on a UUID
    print(dss.delete_subscription(replica="aws", uuid=uuid))


refresh_swagger()

Manually refresh the swagger document. This can help resolve errors communicate with the API.
::
    from hca.dss import DSSClient

    dss = DSSClient()

    dss.refresh_swagger()

upload()

.. note :: 
    Privileged Users

Upload a directory of files from the local filesystem and create a 
bundle containing the uploaded files.
::
    from hca import HCAConfig
    from hca.dss import DSSClient

    hca_config = HCAConfig()
    hca_config["DSSClient"].swagger_url = f"https://dss.dev.data.humancellatlas.org/v1/swagger.json"
    dss = DSSClient(config=hca_config)

    print(dss.upload(src_dir="./data", replica="aws", staging_bucket="bucket-test"))

