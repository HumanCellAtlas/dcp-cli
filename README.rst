HCA DSS CLI
===========
This repository contains a prototype for interacting with the replicated data storage system (aka the "blue box") of the Human Cell Atlas.

This prototype uses a local version of the blue box API spec (using Swagger) to generate a command line client that will make requests to the blue box. Currently, the commands listed are: 
- upload        Upload a file or directory to the cloud, register each of the files, and bundle them together.
- download      Download a full bundle or file to local.
- get-search    Returns a list of bundles matching the given simple criteria.
- post-search   Accepts Elasticsearch JSON query and returns matching bundle identifiers.
- get-files     Returns a list of files matching given criteria.
- head-files    Get the associated metadata from a file with a given uuid.
- put-files     Create a new file with a given UUID. The file content is passed in through a cloud URL. The file on the cloud provider must have metadata set reflecting the file checksums and the file content type.
- get-bundles   Returns a list of bundles matching given criteria.
- put-bundles   Create a new bundle with a given UUID. The list of files UUID+versions to be included must be provided.

Installation
------------
To install this package, run :code:`pip install hca-cli`. This will automatically hook up with the api endpoint as defined in the package published last. 

To use the command line interface with a local or test blue box, open <directory_holding_hca_module>/hca/api_spec.json. Change :code:`host` to the host you want (if you're running on a local blue box, this will likely be :code:`localhost:5000`) and the first argument of :code:`schemes` should be the scheme you want (:code:`http` if running locally, :code:`https` otherwise).

Usage
-----
The entry to this package is the key word :code:`hca`. Merely typing :code:`hca` will list all commands that are possible in a manner similar to the above. 

Each of the above commands has its own associated optional or required arguments. To see these, type :code:`hca <command> -h`. These arguments are listed in a style common to most argparse parsers. For instance: 

:code:`hca put-bundles [-h] [--version VERSION] --replica REPLICA --files INDEXED/NAME/UUID/VERSION [INDEXED/NAME/UUID/VERSION ...] --creator-uid CREATOR_UID uuid`

Here is a list of what each type means. 

- Positional arguments: These don't have a flag in front of them. If they are surrounded by brackets, they are optional.
- Optional agruments: Note that the term optional in this sense doesn't mean that the argument is not required. It means that the argument is identified by a flag. If the argument and the flag (A word with "--" in front of it). are surrounded in brackets, this input is optional. If an arument is repeated multiple times with the later arguments surrounded in brackets, it means the parser accepts a list of these arguments. 
- Objects: Because the REST API sometimes consumes lists of objects, it is important to be able to pass these into the command line interface. To pass in an object, it is a number of arguments separated by slashes, as seen in the example above. An example input to this could be :code:`True/Bob/3806d74a-6ab5-4a6d-ba00-667ea858c7b5/2017-06-30T19:33:38+00:00`. If an argument within an object is optional and you don't have an input for it, you can replace it's supposed place with :code:`None`.


Bugs
~~~~
Please report bugs, issues, feature requests, etc. on `GitHub <https://github.com/HumanCellAtlas/data-store-cli/issues>`_.

License
-------
Licensed under the terms of the `Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.

.. image:: https://img.shields.io/travis/HumanCellAtlas/data-store-cli.svg
        :target: https://travis-ci.org/HumanCellAtlas/data-store-cli
.. image:: https://codecov.io/github/HumanCellAtlas/data-store-cli/coverage.svg?branch=master
        :target: https://codecov.io/github/HumanCellAtlas/data-store-cli?branch=master
.. image:: https://img.shields.io/pypi/v/hca-cli.svg
        :target: https://pypi.python.org/pypi/hca-cli
.. image:: https://img.shields.io/pypi/l/hca-cli.svg
        :target: https://pypi.python.org/pypi/hca-cli
.. image:: https://readthedocs.org/projects/hca-cli/badge/?version=latest
        :target: https://hca-cli.readthedocs.io/
