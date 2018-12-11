SHELL=/bin/bash

test: lint install integration unit

unit: lint install
	coverage run --source=hca -m unittest discover -v -t . -s test/unit

integration: lint install
    # https://github.com/HumanCellAtlas/dcp-cli/issues/127
	coverage run --source=hca -m unittest discover -v -t . -s test/integration/upload
	coverage run --source=hca -m unittest discover -v -t . -s test/integration/dss

lint:
	./setup.py flake8

version: hca/version.py

hca/version.py: setup.py
	echo "__version__ = '$$(python setup.py --version)'" > $@

build: version
	-rm -rf dist
	python setup.py bdist_wheel

install: clean build
	pip install --upgrade dist/*.whl

init_docs:
	cd docs; sphinx-quickstart

docs:
	$(MAKE) -C docs html

clean:
	-rm -rf build dist
	-rm -rf *.egg-info

.PHONY: test unit integration lint install release docs clean

include common.mk
