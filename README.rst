HCA CLI
=======
This repository contains a command line interface (CLI) and Python library for interacting with the Data Coordination
Platform (DCP) of the Human Cell Atlas (HCA). Currently it allows interaction with the Upload Service and Data Storage
Service (DSS).

Installation
------------
:code:`pip install hca`.

Usage
-----
The hca package installs a command-line utility :code:`hca`.

To see the list of commands you can use, type :code:`hca --help`.  Commands are grouped into major categories that
roughly correspond to DCP system components, e.g. DSS, Staging Service.  To get detailed help for a particular
command group type, e.g. :code:`hca dss --help`.

When it is necessary to provide a list of things to a command put them in a single string separated with slashes, e.g.
:code:`True/Bob/3806d74a-6ab5-4a6d-ba00-667ea858c7b5/2017-06-30T19:33:38+00:00`.

Development
-----------
To develop on the CLI, first run `pip install -r requirements-dev.txt`.

To use the command line interface with a local or test DSS, open <directory_holding_hca_module>/hca/api_spec.json.
Change :code:`host` to the host you want (if you're running on a local DSS, this will likely be :code:`localhost:5000`)
and the first argument of :code:`schemes` should be the scheme you want (:code:`http` if running locally,
:code:`https` otherwise).

Code Generation
---------------
Some parts of the CLI are auto-generated from the OpenAPI (Swagger) Specifications (OAS).  The Python bindings have to
be regenerated to reflect any api changes. To regenerate these, run `make bindings`.  Only package maintainers should
run this command and publish new package versions.

Testing
-------
Before you run tests, do an `hca dss login`.  This will pop up a browser and get you to authenticate with Google.
Use an email from one of the whitelisted domains (in `DSS_SUBSCRIPTION_AUTHORIZED_DOMAINS_ARRAY` from `here <https://github.com/HumanCellAtlas/data-store/environment>`_).

Then :code:`make test`.

Bugs
~~~~
Please report bugs, issues, feature requests, etc. on `GitHub <https://github.com/HumanCellAtlas/dcp-cli/issues>`_.

License
-------
Licensed under the terms of the `MIT License <https://opensource.org/licenses/MIT>`_.

.. image:: https://img.shields.io/travis/HumanCellAtlas/dcp-cli.svg
        :target: https://travis-ci.org/HumanCellAtlas/dcp-cli
.. image:: https://codecov.io/github/HumanCellAtlas/dcp-cli/coverage.svg?branch=master
        :target: https://codecov.io/github/HumanCellAtlas/dcp-cli?branch=master
.. image:: https://img.shields.io/pypi/v/hca.svg
        :target: https://pypi.python.org/pypi/hca
.. image:: https://img.shields.io/pypi/l/hca.svg
        :target: https://pypi.python.org/pypi/hca
.. image:: https://readthedocs.org/projects/hca/badge/?version=latest
        :target: https://hca.readthedocs.io/
