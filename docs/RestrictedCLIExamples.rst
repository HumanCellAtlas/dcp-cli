================================
CLI REstricted Endpoint Examples
================================

The HCA CLI provides users of the Human Cell Atlas (HCA) to access and download data sets from the HCA. This page
covers how to access the HCA using the HCA command line utility.

The CLI calls listed here are restricted to those with upload or ingest permissions.
Data will be submitted through a single Ingestion Service API. Submitted data will go through
basic quality assurance before it is deposited into the Data Storage System (DSS) component.

In the document that follows, *privileged user* refers to a user with proper credentials and
permission to upload/ingest data into the DSS.

*NOTE:* The HCA CLI utility is compatible with Python 3.5+.


hca delete-bundle
-----------------

Deletes an existing bundle given a UUID, version, and replica.

Example call to ``hca delete-bundle``:

.. literalinclude:: ../test/tutorial/scripts/cli/delete_bundle_cli.sh


hca put-bundle
--------------

Creates a bundle. A bundle can contain multiple files of arbitrary type.

Inputs:

* ``uuid`` - a unique, user-created UUID.

* ``creator-uid`` - a unique user ID (uid) for the bundle creator uid. This accepts integer values.

* ``version`` - a unique, user-created version number. Use the ``create_verson()`` API function to generate a ``DSS_VERSION``.

* ``replica`` - which replica to use (corresponds to cloud providers; choices: ``aws`` or ``gcp``)

* ``files`` - a valid list of file objects, separated by commas (e.g., ``[{<first_file>}, {<second_file>}, ...  ]``). Each file object must include the following details:
    * Valid UUID of the file
    * Valid version number of the file
    * Name of the file
    * Boolean value - is this file indexed

Example call to ``put_bundle()``:

.. literalinclude:: ../test/tutorial/scripts/cli/put_bundle_cli.sh

hca patch-bundle
----------------

Allows user to pass in an optional list of files to add or remove from an exisiting bundle. 

``add_files``/``remove_files`` follow this format:
::
    [
      {
        "path": "string",
        "type": "string",
        "uuid": "string",
        "version": "string"
      }
    ]

Example call to ``hca patch-bundle``:

.. literalinclude:: ../test/tutorial/scripts/cli/patch_bundle_cli.sh


hca put-file
------------

Creates a new version of a file, given an existing UUID, version, creator uid, and source URL.

Example call to ``hca put-file``:

.. literalinclude:: ../test/tutorial/scripts/cli/put_file_cli.sh


hca get-collection(s), hca put-collection, hca patch-collection, hca delete-collection
--------------------------------------------------------------------------------------

* ``hca get-collection`` - Given a collection UUID, get the collection.

* ``hca get-collections`` - Get a list of collections for a given user. 

* ``hca delete-collection`` - Given a collection UUID and replica, delete the collection from the replica. 

* ``hca put-collection`` - Create a collection.

* ``hca patch-collection`` - Add or remove a given list of files from an existing collection. 

To add or remove files with the CLI actions above, specify each file in the following format:
::
    [
      {
        "path": "string",
        "type": "string",
        "uuid": "string",
        "version": "string"
      }
    ]

Example CLI calls:

.. literalinclude:: ../test/tutorial/scripts/cli/put_delete_get_patch_collection_cli.sh

hca upload
----------

Uploads a directory of files from the local filesystem and creates a bundle containing the uploaded files.

Example call to ``hca upload``:

.. literalinclude:: ../test/tutorial/scripts/cli/upload_cli.sh
