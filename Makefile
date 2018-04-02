SHELL=/bin/bash

test: lint install
	coverage run --source=$$(python setup.py --name) -m unittest discover -v

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
