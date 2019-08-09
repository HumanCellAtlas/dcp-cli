=================
CLI Examples
=================

create-version

Prints a timestamp in DSS_VERSION (ie 1985-04-12T232050.520000Z) that can be used for versioning.    
::
    #!/usr/bin/env bash
   
    hca dss create-version

delete-bundle

.. note ::
    Privileged Users Only

Deletes an existing bundle given a UUID, version, replica, and a reason.
::
    #!/usr/bin/env bash

    hca dss delete-bundle --reason test --uuid 98f6c379-cb78-4a61-9310-f8cc0341c0ea --version 2019-08-02T202456.025543Z --replica gcp

download

Download a bundle and save it to the local filesystem as a directory given a UUID, version, local download directory, and a replica.     
::
    #!/usr/bin/env bash

    hca dss download --replica aws --bundle-uuid ffffa79b-99fe-461c-afa1-240cbc54d071 \
    --version 2019-03-26T130456.302299Z --download-dir  download_test

download-manifest

Files are downloaded to a cache / filestore directory called ‘.hca’. The directory is created in the current directory where download started and 
a copy of the manifest then written to the current directory.

Create a .tsv (tab-separated-file) file and input details given from get-bundle.

The header row must declare the following columns: 

bundle_uuid - the UUID of the bundle containing the file in DSS. 

bundle_version - the version of the bundle containing the file in DSS. 

file_name - the name of the file as specified in the bundle. 

file_uuid - the UUID of the file in the DSS. 

file_version - the version of the file.

file_sha256 - the SHA-256 hash of the file. file_size - the size of the file.

file_size - the size of the file
::
    #!/usr/bin/env bash

    touch manifest.tsv

    echo "bundle_uuid	bundle_version	file_name	file_uuid	file_version	file_sha256 file_size" >> ./manifest.tsv

    echo "<bundle_uuid>   <bundle_version> ... <file_sha256>  20" >> ./manifest.tsv  

    hca dss download-manifest --replica aws --manifest manifest.tsv

file-head

Given a file UUID, return the metadata for the latest version of that file. 
If the version is provided, that version’s metadata is returned instead. 
The metadata is returned in the headers.    
::
    #!/usr/bin/env bash

    hca dss head-file --replica aws --uuid 666ff3f0-67a1-4ead-82e9-3f96a8c0a9b1
    
    hca dss head-file --uuid 6887bd52-8bea-47d9-bbd9-ff71e05faeee --replica aws --version 2019-01-30T165057.189000Z


get-bundle

Given a bundle’s UUID and optionally a version, return the latest version. Displays details about the bundle and each file’s 
info such as name, uuid, version, etc.  
::
    #!/usr/bin/env bash

    hca dss get-bundle --replica aws --uuid ffffa79b-99fe-461c-afa1-240cbc54d071 \
    --version 2019-03-26T130456.302299Z

get-bundles-checkout

.. note::
    How to find the checkout-job-id? Run `post-bundles-checkout` in order to get checkout-job-id.

Check the status and location of a checkout request.    
::
    #!/usr/bin/env bash

    hca dss get-bundles-checkout --replica aws \
    --checkout-job-id 4de1c603-fa8b-4c07-af37-06159e6951e0

get-file

Retrieve a file given a UUID, optionally a version, and displays details of the file.
::
    #!/usr/bin/env bash

    hca dss get-file --replica aws \
        --uuid 666ff3f0-67a1-4ead-82e9-3f96a8c0a9b1 --verison <optional_version_here>

login

Configure and save authentication credentials.

This command may open a browser window to ask for your consent to use web service authentication credentials.

Use –remote if using the CLI in a remote environment    
::
    #!/usr/bin/env bash

    hca dss login --access-token test

logout

Clear authentication credentials previously configured with login.    
::
    #!/usr/bin/env bash

    hca dss logout

post-bundles-checkout

Check out a bundle to DSS-managed or user-managed cloud object storage destination.

Returns a checkout-job-id (ie 4de1c603-fa8b-4c07-af37-06159e6951e0). This checkout-job-id can then
be used for get-bundles-checkout.
::
    #!/usr/bin/env bash

    hca dss post-bundles-checkout --uuid fbafd0e3-b3bf-40da-9bf4-9596989800d8 --replica aws

patch-bundle

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
    #!/usr/bin/env bash

    hca dss patch-bundle --replica aws --uuid 98f6c379-cb78-4a61-9310-f8cc0341c0ea --version 2019-08-02T202456.025543Z

post-search

Find bundles by searching their metadata with an Elasticsearch.
::
    #!/usr/bin/env bash

    hca dss post-search --replica aws --es-query {}

put-bundle

.. note :: 
    Privileged Users

Creates a bundle given creator-id, version, replcia, and valid files.

Inputs:

uuid: User creates a unique UUID.

creator-uid: User creates a unique creator-uid. Any integer value is okay.

version: Create a new version number. One can use create create-verson (CLI) cmd to generate a DSS_VERSION.

replica: Enter a valid service, either AWS or GCP.

files: Enter valid file objects, separated by commas, (ie `{<first_file>} , {<second_file>}, ...` ) 
with the following details:

-Enter valid UUID of the file.

-Enter valid version number of the file.

-Enter the name of the file.

-Enter a boolean value whether the file is indexed or not.
::
    #!/usr/bin/env bash

    hca dss put-bundle --creator-uid 0 --uuid 38f6c379-cb78-4a61-9310-f8cc0341c0ea --version 2019-07-30T164352.961501Z --replica aws --files '{"uuid": "930a927d-0138-4a79-8c87-e45936fe4fc3","version":"2019-07-30T164352.961501Z","name":"get_bundle.json","indexed":false}'

put-file

.. note :: 
    Privileged Users

Create a new version of a file given an existing uuid, verison, creator_uid, and souce_url.
::
    #!/usr/bin/env bash

    hca dss put-file --uuid 38f6c379-cb78-4a61-9310-f8cc0341c0eb --version 2019-07-30T164352.961501Z --creator-uid 0 --source-url s3://bucket-test/930a927d-0138-4a79-8c87-e45936fe4fc3/get_bundle.json


(put/delete/patch/get)-collection and get-collections

.. note ::
    Privileged Users

get-collections: Get a list of users subscriptions.

put-collection: Create a collection for the user.

patch-collection: Allows user to pass in an optional list of files to add or remove from the collection. 

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

get-collection: Given the UUID of the collection, show a collection that the user created. 

delete-collection: Given a UUID and rpelica or the collection, delete the collection the user created. 
::
    #!/usr/bin/env bash

    info_instance=$(hca dss put-collection --uuid fff01947-bf94-43e9-86ca-f6ff6ae45d2c --description foo --details {}  --version 2018-09-17T161441.564206Z  --replica aws --name bar --contents '{"path": "https://dss.dev.data.humancellatlas.org/v1/bundles/ff818282-9735-45fa-a094-e9f2d3d0a954?version=2019-08-06T170839.843085Z&replica=aws",  "version": "2019-08-06T170839.843085Z", "type": "bundle", "uuid": "ff818282-9735-45fa-a094-e9f2d3d0a954"}')

    ID=`echo ${info_instance} | jq -r '.uuid'`
    VERSION=`echo ${info_instance} | jq -r '.version'`

    hca dss get-collections

    hca dss patch-collection --replica aws --uuid $ID --verison $VERSION

    hca dss get-collection --replica aws --uuid $ID

    hca dss delete-collection --replica aws --uuid $ID


(put/delete/get)-subscription and get-subscriptions

get-subscritpions: Get a list of users subscription.

put-subscription: Create a collection for the user.

get-subscription: Given the UUID of the subscription, show a subscription that the user created. 

delete-subscription: Given a UUID and rpelica or the subscription, delete the subscription the user created. 
::
    #!/usr/bin/env bash

    # Creates a sub based given a replica and a url
    instance_info=$(hca dss put-subscription --callback-url https://www.example.com --replica aws) 

    ID=`echo ${instance_info} | jq -r '.uuid'`

    echo $ID

    # Lists all of subs created
    hca dss get-subscriptions --replica aws

    # List a sub
    hca dss get-subscription --replica aws --uuid $ID

    # Deletes a sub based on a UUID
    hca dss delete-subscription --replica aws --uuid $ID

refresh-swagger

Manually refresh the swagger document. This can help resolve errors communicate with the API.
::
    #!/usr/bin/env bash

    hca dss refresh-swagger

upload

.. note :: 
    Privileged Users

Upload a directory of files from the local filesystem and create a 
bundle containing the uploaded files.
::
    #!/usr/bin/env bash

    hca dss upload --src-dir test_data --replica aws --staging-bucket bucket-test

