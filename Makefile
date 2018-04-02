SHELL=/bin/bash

test: lint install
	coverage run --source=$$(python setup.py --name) -m unittest discover -v

lint:
	./setup.py flake8

install:
	-rm -rf dist
	python setup.py bdist_wheel
	pip install --upgrade dist/*.whl

init_docs:
	cd docs; sphinx-quickstart

docs:
	$(MAKE) -C docs html


.PHONY: test release docs

include common.mk
