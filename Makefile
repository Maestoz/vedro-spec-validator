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

.PHONY: run-vedro-fn-units
run-vedro-fn-units:
	python3 -m vedro run tests/units_vedro_fn/scenarios/

.PHONY: run-unittest-units
run-unittest-units:
	python -m unittest discover -v

.PHONE: check-coverage
check-coverage:
	coverage run --parallel-mode -m vedro run tests/units_vedro_fn/scenarios/
	coverage run --parallel-mode -m unittest discover -v
	coverage combine
	coverage html
	open htmlcov/index.html
