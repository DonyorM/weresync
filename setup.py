#! /usr/bin/env python3

import os
from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as file:
        return file.read()


setup(
    name="WereSync",
    version="1.0.2",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=["parse>=1.6.6", "yapsy>=1.11.223"],
    entry_points={
        'console_scripts': [
            "weresync = weresync.interface:main"
        ],
        'gui_scripts': [
            "weresync-gui = weresync.gui:start_gui"
        ]
    },
    include_package_data=True,
    package_data={
        "resources": ["*.svg", "*.png", "locale/*/LC_MESSAGES/*"]
    },
    # Metadata
    author="Daniel Manila",
    author_email="dmv@springwater7.org",
    description="Incrementally clones Linux drives",
    long_description=read("README.rst"),
    license="Apache 2.0",
    keywords="clone, linux, backup, smaller drive",
    url="https://github.com/DonyorM/weresync",
)
