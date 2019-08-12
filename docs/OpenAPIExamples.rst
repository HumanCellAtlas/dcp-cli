===============================
API Examples (Open End-points))
===============================

The HCA API ensures and provides a simple and open access to Human Cell Atlas data. This way, it allows researchers and
curious users to be able to download repuitable data and use it to compute either locally on their own systems or
in the cloud. 


Compliant with python 3.5+

=============================
create_version()
=============================

Returns a timestamp in DSS_VERSION format (ie 1985-04-12T232050.520000Z) that can be used for versioning.    

.. literalinclude:: ../test/tutorial/scripts/api/create_version_api.py

=============================
download()
=============================

Download a bundle to the local filesystem as a directory. By default, all data and metadata files 
are downloaded to cache / filestore directory called '.hca'. 

.. note::
  A version is a timestamp in RFC3339 format that keeps track of the most recent iteration of a bundle/file.

  A bundle consists of many different data files.

Example bundle (use get_bundle()):
::
  {
    "bundle": {
      "creator_uid": 8008,
      "files": [
        {
          "content-type": "application/json; dcp-type=\"metadata/biomaterial\"",
          "crc32c": "5c084696",
          "indexed": true,
          "name": "cell_suspension_0.json",
          "s3_etag": "bd60da05055d1cd544855dd35cb12470",
          "sha1": "fdeb52d3caf0becce0575528c81bf0a06cb4a023",
          "sha256": "e0ff1c402a4d6c659937f90d00d9820a2ebf0ebc920260a2a2bddf0961c30de5",
          "size": 847,
          "uuid": "134c0f04-76ae-405d-aea4-b72c08a53dd9",
          "version": "2019-07-09T230754.589000Z"
        },
        {
          "content-type": "application/json; dcp-type=\"metadata/biomaterial\"",
          "crc32c": "39e6f9e1",
          "indexed": true,
          "name": "specimen_from_organism_0.json",
          "s3_etag": "f30917f841530d78e16223354049c8dc",
          "sha1": "98171c05647a3b771afb3bd61e65d0a25b0afe7f",
          "sha256": "35406f0b8fa1ece3e3589151978aefef28f358afa163874b286eab837fcabfca",
          "size": 864,
          "uuid": "577a91d8-e579-41b6-9353-7e4e774c161a",
          "version": "2019-07-09T222811.151000Z"
        },
        ...
        },
        {
          "content-type": "application/gzip; dcp-type=data",
          "crc32c": "38f31e58",
          "indexed": false,
          "name": "SRR6579532_2.fastq.gz",
          "s3_etag": "ac67e10df687471f5808be96499836c6",
          "sha1": "8743feb4d1ce82328127d10e2b1dfa35e5ae4b5a",
          "sha256": "3d788e06b5ca4c8fc679b47c790b1e266f73d48818a1749743ec85f096d657ea",
          "size": 43810957,
          "uuid": "1330ef1a-7a21-40c6-84c5-5cec18204028",
          "version": "2019-08-03T150636.729022Z"
        }
      ],
      "uuid": "ffffaf55-f19c-40e3-aa81-a6c69d357265",
      "version": "2019-08-01T200147.836832Z"
    }
  }

.. literalinclude:: ../test/tutorial/scripts/api/download_api.py

=============================    
download_manifest()
=============================

Files are downloaded to a cache / filestore directory called ‘.hca’. The directory is created in the current directory where download started and 
a copy of the manifest then written to the directory.

Before running download_manifest(), create a .tsv (tab-separated-file) file and input details given from get_bundle().

The header row must declare the following columns: 

bundle_uuid - the UUID of the bundle containing the file in DSS. 

bundle_version - the version of the bundle containing the file in DSS. 

file_name - the name of the file as specified in the bundle. 

file_uuid - the UUID of the file in the DSS. 

file_version - the version of the file.

file_sha256 - the SHA-256 hash of the file. file_size - the size of the file.

file_size - the size of the file

.. literalinclude:: ../test/tutorial/scripts/api/download_manifest_api.py

=============================
file_head()
=============================

Given a file UUID, return the metadata for the latest version of that file. 
If the version is provided, that version’s metadata is returned instead. 
The metadata is returned in the headers.

.. literalinclude:: ../test/tutorial/scripts/api/get_file_head_api.py

=============================
get_bundle()
=============================

Given a bundle’s UUID and optionally a version, return the latest version of the bundle. 
Displays details about the bundle and each file’s info such as name, UUID, version, etc.

.. literalinclude:: ../test/tutorial/scripts/api/get_bundle_api.py

=============================
get_bundles_checkout()
=============================

.. note:
    How to find the checkout-job-id? Run post-bundles-checkout in order to get checkout-job-id.

Check the status and location of a checkout request.    

Example output:
::
    {
    "location": "s3://org-hca-dss-checkout-prod/bundles/fff54b87-26fe-42a9-be54-3f5a7ef8176e.2019-03-26T131455.775610Z",
    "status": "SUCCEEDED"
    }


.. literalinclude:: ../test/tutorial/scripts/api/get_bundles_checkout_api.py

=============================
get_file() 
=============================

Retrieves a file given a UUID, optionally a version, and displays the details of the file.

Example output:
::
    {
    "describedBy": "https://schema.humancellatlas.org/type/file/7.0.2/sequence_file",
    "schema_type": "file",
    "file_core": {
        "file_name": "SRR6546754_2.fastq.gz",
        "file_format": "fastq.gz"
    },
    "read_index": "read2",
    "insdc_run": [
        "SRR6546754"
    ],
    "technical_replicate_group": "Rep_id_7031",
    "provenance": {
        "document_id": "39a93f75-0db3-4ee2-ab22-3eaa9932cf67",
        "submission_date": "2019-01-30T11:15:21.403Z",
        "update_date": "2019-02-19T17:17:10.540Z"
    }

.. literalinclude:: ../test/tutorial/scripts/api/get_file_api.py

=============================
login()
=============================

Configure and save authentication credentials.

.. literalinclude:: ../test/tutorial/scripts/api/login_api.py

=============================
logout()
=============================

Clear authentication credentials previously configured with login.    

.. literalinclude:: ../test/tutorial/scripts/api/logout_api.py

=============================
post_bundles_checkout()
=============================

Returns a checkout-job-id (ie 4de1c603-fa8b-4c07-af37-06159e6951e0). This checkout-job-id can then
be used for get_bundles_checkout().

.. literalinclude:: ../test/tutorial/scripts/api/post_bundles_checkout_api.py

=============================
post_search()
=============================

Find bundles by listing bundle_fqid, which consists of the bundles UUID and version separated by a dot(.), 
and the bundle_url. 

.. note::
    "bundle_fqid": "fff807ba-bc98-4247-a560-49fb90c9675c.2019-08-01T200147.111027Z"
    
    Before the dot (.) is the UUID, a string that defines the unique bundle,
    and the version follows.

Example output:
::
    {
    ...
    },
    {
      "bundle_fqid": "fff807ba-bc98-4247-a560-49fb90c9675c.2019-08-01T200147.111027Z",
      "bundle_url": "https://dss.data.humancellatlas.org/v1/bundles/fff807ba-bc98-4247-a560-49fb90c9675c?version=2019-08-01T200147.111027Z&replica=aws",
      "search_score": null
    },
    {
        ...
    },

.. literalinclude:: ../test/tutorial/scripts/api/post_search_api.py

(put/delete/get)_subscription() and get_subscriptions()

get-subscritpions: Gets a list of users subscription.

put-subscription: Create a collection for the user given a replica and a call-back url.

get-subscription: Given the UUID of the subscription, show a subscription that the user created. 

delete-subscription: Given a UUID and rpelica or the subscription, delete the subscription the user created. 

.. literalinclude:: ../test/tutorial/scripts/api/put_delete_get_sub_api.py

=============================
refresh_swagger()
=============================

Manually refresh the swagger document.

.. literalinclude:: ../test/tutorial/scripts/api/refresh_swagger_api.py
