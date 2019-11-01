==========================
CLI Open Endpoint Examples
==========================

The HCA CLI provides users of the Human Cell Atlas (HCA) to access and download data sets from the HCA. This page
covers how to access the HCA using the HCA command line utility.

*NOTE:* The HCA CLI utility is compatible with Python 3.5+.


hca create-version
------------------

Returns a timestamp in ``DSS_VERSION`` format (e.g., ``1985-04-12T232050.520000Z``), useful for
versioning bundles or files.

.. note::
  A version is a timestamp in RFC3339 format that keeps track of the most recent iteration of a
  bundle or file. A bundle consists of many different data files, and both bundles and files have
  version numbers.

Example call to ``hca create-version``:

.. literalinclude:: ../test/tutorial/scripts/cli/create_version_cli.sh

hca download
------------

Downloads a bundle to the local filesystem as a directory. By default, both data and metadata files
are downloaded (flags can be added to download only the data or the metadata).

Implementation detail: All files are downloaded to a local cache directory called ``.hca`` that is
created in the directory where the download is initiated. The user should never need to interact
directly with the ``.hca`` directory.

See note above regarding version numbering.

Example call to ``hca get-bundle``:

.. literalinclude:: ../test/tutorial/scripts/cli/download_cli.sh

Example response:
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
    
hca download-manifest
---------------------

Downloads a list of files specified in a user-provided manifest file.

The manifest file should be in TSV (tab-separated variable) format, with one line in the manifest
per file to download. The manifest should contain information about files (one file per line).
The information that must be provided for a given bundle is available from the ``get_bundle()``
method.

The header row must define the columns:

* ``bundle_uuid`` - UUID of the requested bundle
* ``bundle_version`` - the version of the requested bundle
* ``file_name`` - the name of the file as specified in the bundle
* ``file_uuid`` - the UUID of the file in the DSS
* ``file_sha256`` - the SHA-256 hash of the file
* ``file_size`` - the size of the file

Example call to ``hca download-manifest``:

.. literalinclude:: ../test/tutorial/scripts/cli/download_manifest_cli.sh

Example manifest TSV file:

::

    bundle_uuid                             bundle_version              file_name               file_uuid                               file_version                file_sha256                                                         file_size   file_path
    002aeac5-4d74-462d-baea-88f5c620cb50    2019-08-01T200147.836900Z   cell_suspension_0.json  c14b99ea-d8e2-4c84-9dc2-ce2245d8a743    2019-07-09T231935.003000Z   b43cebcca9cd5213699acce7356d226de07edef5c5604510a697159af1a12149    847         .hca/v2/files_2_4/b4/3ceb/b43cebcca9cd5213699acce7356d226de07edef5c5604510a697159af1a12149


hca file-head
-------------

Returns the metadata for the latest version of a file with a given UUID. If the version is provided,
the metadata for that specific version is returned instead. The metadata is returned in the headers.

Example call to ``hca file-head``:

.. literalinclude:: ../test/tutorial/scripts/cli/get_file_head_cli.sh

Example JSON header returned by API:
::

    {
        "Date": "Tue, 22 Oct 2019 19:16:50 GMT",
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": "0",
        "Connection": "keep-alive",
        "x-amzn-RequestId": "bea3fd18-f373-4cb9-b0d2-0642c955eb5b",
        "X-DSS-SHA1": "ccac0f3fb16d1209ac88de8f293e61a115cfee38",
        "Access-Control-Allow-Origin": "*",
        "X-DSS-S3-ETAG": "d1634210a190ae78f6dd7a21f3c6ef1d",
        "X-DSS-SHA256": "24265fd0ebcdfe84eb1a09227c58c117ed03006b1de3f1e0694e50ed63b2f9e7",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Amz-Date,X-Amz-Security-Token,X-Api-Key",
        "X-DSS-CONTENT-TYPE": 'application/json; dcp-type="metadata/biomaterial"',
        "X-DSS-CRC32C": "ec41da6a",
        "X-DSS-CREATOR-UID": "8008",
        "x-amz-apigw-id": "B-pROGlIoAMFUwg=",
        "X-DSS-VERSION": "2019-01-30T165057.189000Z",
        "X-Amzn-Trace-Id": "Root=1-5daf55a1-132caa16297ffc40a4046739;Sampled=0",
        "X-AWS-REQUEST-ID": "eeeb46a0-61a2-4fb5-aae9-21fe6a01f277",
        "X-DSS-SIZE": "856",
    }


hca get-bundle
--------------

For a given bundle UUID and optionally a bundle version, returns information about the latest version
of that bundle. Information returned includes the bundle creator, UUID, and version, as well as 
information about each file in the bundle, such as the file name, UUID, version, etc.

Example call to ``hca get-bundle``:

.. literalinclude:: ../test/tutorial/scripts/cli/get_bundle_cli.sh

Example JSON returned by ``hca get-bundle``:
::

    {
      "bundle": {
        "creator_uid": 8008,
        "files": [
          {
            "name": "cell_suspension_0.json",
            "uuid": "c14b99ea-d8e2-4c84-9dc2-ce2245d8a743",
            "version": "2019-07-09T231935.003000Z"
            "content-type": "application/json; dcp-type=\"metadata/biomaterial\"",
            "crc32c": "892ad18b",
            "indexed": true,
            "s3_etag": "57814b3405165d975a6688dc8110dea0",
            "sha1": "849ebad4cff8f4fdf10ad25ad801ebb8aacc58b7",
            "sha256": "b43cebcca9cd5213699acce7356d226de07edef5c5604510a697159af1a12149",
            "size": 847,
          },
          {
            "name": "specimen_from_organism_0.json",
            "uuid": "05998af7-fa6f-44fe-bd16-ac8eafb42f28",
            "version": "2019-07-09T222953.739000Z"
            "content-type": "application/json; dcp-type=\"metadata/biomaterial\"",
            "crc32c": "8686eb38",
            "indexed": true,
            "s3_etag": "c3079914aa72f4aafa926594c756c978",
            "sha1": "885f0d6c524796116394fc4e60f0d9f65988765f",
            "sha256": "d0c8cc0d13e30b73241405035d98265eab891ea94fbccc3da4bb0ca10c3d0f24",
            "size": 872,
          },
          ...
        ],
        "uuid": "002aeac5-4d74-462d-baea-88f5c620cb50",
        "version": "2019-08-01T200147.836900Z"
      }
    }


hca get-bundles-checkout
------------------------

.. note:
    To get the ``checkout-job-id``, use the ``hca post-bundles-checkout`` action.

Check the status and location of a checkout request.

Example call to ``hca get-bundles-checkout``:

.. literalinclude:: ../test/tutorial/scripts/cli/get_bundles_checkout_cli.sh

Example JSON returned by ``hca get-bundles-checkout``:
::

    {
      "location": "s3://org-hca-dss-checkout-prod/bundles/fff54b87-26fe-42a9-be54-3f5a7ef8176e.2019-03-26T131455.775610Z",
      "status": "SUCCEEDED"
    }


hca get-file 
------------

Retrieves a file given a UUID, optionally a version, and displays the details of the file.

Example call to ``hca get-file``:

.. literalinclude:: ../test/tutorial/scripts/cli/get_file_cli.sh

Example JSON returned by ``hca get-file``:
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
    }


hca login
---------

Configures and saves authentication credentials.

Example call to ``hca login``:

.. literalinclude:: ../test/tutorial/scripts/cli/login_cli.sh


hca logout
----------

Clears authentication credentials previously configured with login.

Example call to ``hca logout``:

.. literalinclude:: ../test/tutorial/scripts/cli/logout_cli.sh


hca post-bundles-checkout
-------------------------

Returns a ``checkout-job-id`` (e.g., ``4de1c603-fa8b-4c07-af37-06159e6951e0``). This
``checkout-job-id`` can then be used with the ``get_bundles_checkout()`` method.

Example call to ``hca post-bundles-checkout``:

.. literalinclude:: ../test/tutorial/scripts/cli/post_bundles_checkout_cli.sh


hca post-search
---------------

Find bundles by their ``bundle_fqid``, which is the bundle's UUID and version separated by a dot (.).

For example, the bundle FQID ``fff807ba-bc98-4247-a560-49fb90c9675c.2019-08-01T200147.111027Z`` is
a bundle with the UUID ``fff807ba-bc98-4247-a560-49fb90c9675c`` and the version number 
``2019-08-01T200147.111027Z``.

This method returns an FQID and URL for each matching bundle.

Example call to ``hca post-search``:

.. literalinclude:: ../test/tutorial/scripts/cli/post_search_cli.sh

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
    }

hca get-subscription(s), hca put-subscription, hca delete-subscription
----------------------------------------------------------------------

* ``get_subscriptions()``: Gets a list of users subscription.

* ``put_subscription()``: Create a collection for the user given a replica and a call-back url.

* ``get_subscription()``: Given the UUID of the subscription, show a subscription that the user created.

* ``delete_subscription()``: Given a UUID and rpelica or the subscription, delete the subscription the user created.

Example CLI calls:

.. literalinclude:: ../test/tutorial/scripts/cli/put_delete_get_sub_cli.sh


hca refresh-swagger
-------------------

Manually refresh the swagger document.

.. literalinclude:: ../test/tutorial/scripts/cli/refresh_swagger_cli.sh
