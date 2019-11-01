===================================
Python Restricted Endpoint Examples
===================================

The HCA API provides several ways for users of the Human Cell Atlas (HCA) to access and download
data sets from the HCA. This page covers how to access the HCA using Python API bindings.

The API calls listed here are restricted to those with upload or ingest permissions.
Data will be submitted through a single Ingestion Service API. Submitted data will go through
basic quality assurance before it is deposited into the Data Storage System (DSS) component.

In the document that follows, *privileged user* refers to a user with proper credentials and
permission to upload/ingest data into the DSS.

*NOTE:* The HCA CLI utility is compatible with Python 3.5+.


delete_bundle()
---------------

Deletes an existing bundle given a UUID, version, and replica.

Example call to ``delete_bundle()``:

.. literalinclude:: ../test/tutorial/scripts/api/delete_bundle_api.py

put_bundle()
------------

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

.. literalinclude:: ../test/tutorial/scripts/api/put_bundle_api.py

patch_bundle()
--------------

Allows a user to modify an existing bundle. User passes in an optional list of files to add or remove from an existing bundle.

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

Example call to ``patch_bundle()``:

.. literalinclude:: ../test/tutorial/scripts/api/patch_bundle_api.py


put_file()
----------

Creates a new version of a file, given an existing UUID, version, creator uid, and source URL.

Example call to ``put_file()``:

.. literalinclude:: ../test/tutorial/scripts/api/put_file_api.py


put_collection(), delete_collection(), patch_collection(), get_collection(s)()
------------------------------------------------------------------------------

* ``get_collection()`` - Given a collection UUID, get the collection.

* ``get_collections()`` - Get a list of collections for a given user.

* ``delete_collection()`` - Given a collection UUID and replica, delete the collection from the replica.

* ``put_collection()`` - Create a collection.

* ``patch_collection()`` - Add or remove a given list of files from an existing collection.

To add or remove files with the API endpoints above, specify each file in the following format:
::

    [
      {
        "path": "string",
        "type": "string",
        "uuid": "string",
        "version": "string"
      }
    ]

Example API calls:

.. literalinclude:: ../test/tutorial/scripts/api/put_delete_get_patch_collection_api.py


upload()
--------

Uploads a directory of files from the local filesystem and creates a bundle containing the uploaded files.

Example call to ``upload()``:

.. literalinclude:: ../test/tutorial/scripts/api/upload_api.py
