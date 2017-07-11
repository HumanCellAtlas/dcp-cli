HCA DSS CLI
===========
This repository contains a prototype for interacting with the replicated Data Storage System 
(hereafter the DSS) of the Human Cell Atlas.

This prototype uses a local version of the DSS API spec (using Swagger) to generate a command 
line client that will make requests to the DSS. Please run :code:`hca --help` to see an overview of available commands.

Installation
------------
To install this package, run :code:`pip install hca-cli`. This will automatically hook up with the api 
endpoint as defined in the package published last. 

To use the command line interface with a local or test DSS, open <directory_holding_hca_module>/hca/api_spec.json. Change :code:`host` to the host you want (if you're running on a local DSS, this will likely be :code:`localhost:5000`) and the first argument of :code:`schemes` should be the scheme you want (:code:`http` if running locally, :code:`https` otherwise).

Usage
-----
The command-line utility hca is the entry point to the CLI provided by this package.

Each of the above commands has its own associated optional or required arguments. To see these, type :code:`hca <command> -h`. These arguments are listed in a style common to most argparse parsers. For instance: 

:code:`hca put-bundles [-h] [--version VERSION] --replica REPLICA --files INDEXED/NAME/UUID/VERSION [INDEXED/NAME/UUID/VERSION ...] --creator-uid CREATOR_UID uuid`

Here is a list of what each type means. 

- Positional arguments: These don't have a flag in front of them. If they are surrounded by brackets, they are optional.
- Optional arguments: Note that the term optional in this sense doesn't mean that the argument is not required. It means that the argument is identified by a flag. If the argument and the flag (A word with "--" in front of it). are surrounded in brackets, this input is optional. If an arument is repeated multiple times with the later arguments surrounded in brackets, it means the parser accepts a list of these arguments. 
- Objects: Because the REST API sometimes consumes lists of objects, it is important to be able to pass these into the command line interface. To pass in an object, it is a number of arguments separated by slashes, as seen in the example above. An example input to this could be :code:`True/Bob/3806d74a-6ab5-4a6d-ba00-667ea858c7b5/2017-06-30T19:33:38+00:00`. If an argument within an object is optional and you don't have an input for it, you can replace it's supposed place with :code:`None`.


Bugs
~~~~
Please report bugs, issues, feature requests, etc. on `GitHub <https://github.com/HumanCellAtlas/data-store-cli/issues>`_.

License
-------
Licensed under the terms of the `MIT License <https://opensource.org/licenses/MIT>`_.

.. image:: https://img.shields.io/travis/HumanCellAtlas/data-store-cli.svg
        :target: https://travis-ci.org/HumanCellAtlas/data-store-cli
.. image:: https://codecov.io/github/HumanCellAtlas/data-store-cli/coverage.svg?branch=master
        :target: https://codecov.io/github/HumanCellAtlas/data-store-cli?branch=master
.. image:: https://img.shields.io/pypi/v/hca.svg
        :target: https://pypi.python.org/pypi/hca
.. image:: https://img.shields.io/pypi/l/hca.svg
        :target: https://pypi.python.org/pypi/hca
.. image:: https://readthedocs.org/projects/hca/badge/?version=latest
        :target: https://hca.readthedocs.io/
