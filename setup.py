#! /usr/bin/env python3

import os

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as file:
        return file.read()

from setuptools import setup, find_packages
setup(
    name="WereSync",
    version="0.1",
    package_dir={"" : "src"},
    packages=find_packages("src"),
    install_requires=["parse>=1.6.6"],
    entry_points={
        'console_scripts': [
            "weresync = weresync.interface:main"
        ]
    },

    #Metadata
    author="Daniel Manila",
    description="Incrementally clones Linux drives",
    long_description=read("README.rst"),
    license="Apache 2.0",
    keywords="clone, linux, backup, smaller drive",
)
