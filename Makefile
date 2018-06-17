SHELL=/bin/bash

test: lint install
	# https://github.com/HumanCellAtlas/dcp-cli/issues/127
	coverage run --source=hca -m unittest discover -v -t . -s test/upload
	coverage run --source=hca -m unittest discover -v -t . -s test -p test_dss_*.py

lint:
	./setup.py flake8

version: hca/version.py

hca/version.py: setup.py
	echo "__version__ = '$$(python setup.py --version)'" > $@

install: clean version
	-rm -rf dist
	python setup.py bdist_wheel
	pip install --upgrade dist/*.whl

init_docs:
	cd docs; sphinx-quickstart

docs:
	$(MAKE) -C docs html

clean:
	-rm -rf build dist
	-rm -rf *.egg-info

.PHONY: test lint install release docs clean

include common.mk
