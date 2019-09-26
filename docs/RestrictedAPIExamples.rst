===================================
API Examples (Restricted End-points)
===================================

The HCA API ensures and provides a simple and open access to Human Cell Atlas data. This way, it allows researchers and
curious users to be able to download repuitable data and use it to compute either locally on their own systems or
in the cloud. 

API calls listed here are restricted to those with proper permission to upload/ingest. Data 
will be submitted through a single Ingestion Service API. Submitted data will go through basic quality 
assurance before depositing the data into the Data Store.

Privileged users are those with proper credentials who can upload/ingest data into the Data Store.  

Compliant with python 3.5+


delete_bundle()
------------------------

.. note:
    Privileged Users.

Deletes an existing bundle given a UUID, version, and replica.

.. literalinclude:: ../test/tutorial/scripts/api/delete_bundle_api.py

put_bundle()
------------------------

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

.. literalinclude:: ../test/tutorial/scripts/api/put_bundle_api.py

patch_bundle()
------------------------

.. note ::
    Privileged Users

Allows user to pass in an optional list of files to add or remove from an existing bundle. 

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

.. literalinclude:: ../test/tutorial/scripts/api/patch_bundle_api.py

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

.. literalinclude:: ../test/tutorial/scripts/api/put_bundle_api.py

put_file()
------------------------

.. note :: 
    Privileged Users

Creates a new version of a file given an existing UUID, verison, creator_uid, and soruce_url.

.. literalinclude:: ../test/tutorial/scripts/api/put_file_api.py

(put/delete/patch/get)-collection and get-collections
------------------------

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

.. literalinclude:: ../test/tutorial/scripts/api/put_delete_get_patch_collection_api.py

upload()
------------------------

.. note :: 
    Privileged Users

Upload a directory of files from the local filesystem and create a 
bundle containing the uploaded files.

.. literalinclude:: ../test/tutorial/scripts/api/upload_api.py