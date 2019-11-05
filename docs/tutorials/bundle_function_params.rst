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
