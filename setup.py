#! /usr/bin/env python3

import os
from setuptools import setup, find_packages
import subprocess
import shutil


class InvalidSetupError(Exception):
    pass


def create_mo_files():
    # Avoids this code running on read the docs, since gettext is not installed
    # there
    if os.environ.get("READTHEDOCS") == "True":
        return []
    if shutil.which("msgfmt") is None:
        # If gettext isn't installed, skip this
        raise InvalidSetupError("gettext not installed but is required.")

    data_files = []
    localedir = 'locale'
    po_dirs = [localedir + '/' + l + '/LC_MESSAGES/'
               for l in next(os.walk(localedir))[1]]
    for d in po_dirs:
        mo_files = []
        po_files = [f
                    for f in next(os.walk(d))[2]
                    if os.path.splitext(f)[1] == '.po']
        for po_file in po_files:
            filename, extension = os.path.splitext(po_file)
            mo_file = filename + '.mo'
            msgfmt_cmd = 'msgfmt {} -o {}'.format(d + po_file, d + mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo_files.append(d + mo_file)
        data_files.append(("share/" + d, mo_files))
    return data_files


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as file:
        return file.read()


setup(
    name="WereSync",
    version="1.0.6",
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
        "resources": ["*.svg", "*.png"]
    },
    data_files=[
        ("share/icons/hicolor/scalable/apps",
         ["src/weresync/resources/weresync.svg"])
    ] + create_mo_files(),
    # Metadata
    author="Daniel Manila",
    author_email="dmv@springwater7.org",
    description="Incrementally clones Linux drives",
    long_description=read("README.rst"),
    license="Apache 2.0",
    keywords="clone, linux, backup, smaller drive",
    url="https://github.com/DonyorM/weresync",
)
