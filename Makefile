.PHONY: install
install:
	pip3 install --quiet --upgrade pip
	pip3 install --quiet -r requirements.txt -r

.PHONY: build
build:
	pip3 install --quiet --upgrade pip
	make install
	pip3 install --quiet --upgrade setuptools wheel twine
	python3 setup.py sdist bdist_wheel