from setuptools import find_packages, setup

from vedro_spec_validator.__version__ import __version__


def find_required():
    with open("requirements.txt") as f:
        return f.read().splitlines()


setup(
    name="vedro-spec-validator",
    version=__version__,
    description="Vedro Spec Validator plugin",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sam Roz",
    author_email="rolez777@gmail.com",
    python_requires=">=3.10",
    url="https://github.com/Maestoz/vedro-spec-validator",
    license="Apache-2.0",
    packages=find_packages(),
    install_requires=find_required(),
    entry_points={
        'console_scripts': [
            'vedro-spec-cache=vedro_spec_validator.jj_spec_validator.cli:cache_specs',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ]
)
