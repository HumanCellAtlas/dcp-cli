SHELL=/bin/bash

constants: hca/api_spec.json

lint:
	./setup.py flake8

hca/dss/api_spec.json:
	curl https://hca-dss.czi.technology/v1/swagger.json > hca/dss/api_spec.json

test: lint install
	coverage run --source=$$(python setup.py --name) -m unittest discover

init_docs:
	cd docs; sphinx-quickstart

bindings:
	git clean -df hca/dss
	python -m hca.dss.regenerate_api
	find hca/dss -name '*.pyc' -delete

docs:
	$(MAKE) -C docs html

install:
	-rm -rf dist
	python setup.py bdist_wheel
	pip install --upgrade dist/*.whl

.PHONY: test release docs

include common.mk
