SHELL=/bin/bash

test: lint install integrationtests unittests
	coverage combine
	rm -f .coverage.*


unittests:
	coverage run -p --source=hca -m unittest discover -v -t . -s test/unit

unit: lint install unittests
	coverage combine
	rm -f .coverage.*

integrationtests:
    # https://github.com/HumanCellAtlas/dcp-cli/issues/127
	coverage run -p --source=hca -m unittest discover -v -t . -s test/integration/upload
	coverage run -p --source=hca -m unittest discover -v -t . -s test/integration/dss

integration: lint install integrationtests
	coverage combine
	rm -f .coverage.*

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

clean-win:
	rmdir /s /q build
	rmdir /s /q dist
	for %f in (*.egg-info) do rmdir /s /q %f

install-win: clean-win
	for %f in (dist\*.whl) do pip install --upgrade %f

test-win: install-win integrationtests unittests

.PHONY: test unit integration lint install release docs clean

include common.mk

