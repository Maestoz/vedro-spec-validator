.PHONY: install
install:
	pip3 install --quiet --upgrade pip
	pip3 install --quiet -r requirements.txt

.PHONE: install-dev
install-dev:
	pip3 install --upgrade pip
	pip3 install -r requirements-dev.txt

.PHONY: build
build:
	pip3 install --quiet --upgrade pip
	make install
	pip3 install --quiet --upgrade setuptools wheel twine
	python3 setup.py sdist bdist_wheel

.PHONY: fix-imports
fix-imports:
	@isort .
	@autoflake .

### Unit tests

.PHONY: run-unittest-units
run-unittest-units:
	python -m unittest discover -v -s tests/unittest

.PHONY: run-test-spec
run-test-spec:
	python -m unittest tests/unittest/jj_spec_validator/test_spec.py

.PHONY: check-coverage
check-coverage:
	coverage run --parallel-mode -m unittest discover -v -s tests/unittest
	coverage combine
	coverage html
	open htmlcov/index.html
