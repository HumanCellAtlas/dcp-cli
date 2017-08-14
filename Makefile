SHELL=/bin/bash

constants: hca/api_spec.json

lint:
	pip install flake8
	./setup.py flake8

hca/api_spec.json:
	curl https://hca-dss.czi.technology/v1/swagger.json > hca/api_spec.json

test: lint bindings
	pip install six coverage
	coverage run --source=$$(python setup.py --name) ./test/test.py

init_docs:
	cd docs; sphinx-quickstart

bindings:
	python -m hca.regenerate_api
	find hca -name "*.pyc" -delete

docs: bindings
	$(MAKE) -C docs html

install_helper:
	-rm -rf dist
	python setup.py bdist_wheel
	pip install --upgrade dist/*.whl

install: install_helper bindings

.PHONY: test release docs

include common.mk
