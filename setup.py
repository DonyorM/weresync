#! /usr/bin/env python3

import os
from setuptools import setup, find_packages
import subprocess
import shutil


class InvalidSetupError(Exception):
    pass


def create_mo_files():
    """Converts .po templates to readble .mo files using msgfmt."""
    # Avoids this code running on read the docs, since gettext is not installed
    # there
    if os.environ.get("READTHEDOCS") == "True":
        return []
    if shutil.which("msgfmt") is None:
        # If gettext isn't installed, skip this
        raise InvalidSetupError("gettext not installed but is required.")

    localedir = 'src/weresync/resources/locale'
    po_dirs = []
    langs = next(os.walk(localedir))[1]
    po_dirs = [localedir + '/' + l + '/LC_MESSAGES/' for l in langs]
    for d in po_dirs:
        po_files = [
            f for f in next(os.walk(d))[2] if os.path.splitext(f)[1] == '.po'
        ]
        for po_file in po_files:
            filename, extension = os.path.splitext(po_file)
            mo_file = filename + '.mo'
            msgfmt_cmd = 'msgfmt {} -o {}'.format(d + po_file, d + mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
    return ["locale/" + l + "/LC_MESSAGES/*.mo" for l in langs]


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as file:
        return file.read()


target_icon_loc = "share/icons/hicolor/scalable/apps"
if os.getuid() == 0:  # Install is running as root
    target_icon_loc = "/usr/" + target_icon_loc

if __name__ == "__main__":
    setup(
        name="WereSync",
        version="1.1.2",
        package_dir={"": "src"},
        packages=find_packages("src"),
        install_requires=["parse==1.6.6", "yapsy==1.11.223", "pydbus==0.6.0"],
        entry_points={
            'console_scripts': [
                "weresync = weresync.interface.cli:main",
                "weresync-daemon = weresync.daemon.daemon:run"
            ],
            'gui_scripts': ["weresync-gui = weresync.interface.gui:start_gui"]
        },
        package_data={
            "weresync.resources": ["*.svg", "*.png"] + create_mo_files()
        },
        data_files=[(target_icon_loc,
                     ["src/weresync/resources/weresync.svg"])],
        # Metadata
        author="Daniel Manila",
        author_email="dmv@springwater7.org",
        description="Incrementally clones Linux drives",
        long_description=read("README.rst"),
        license="Apache 2.0",
        keywords="clone, linux, backup, smaller drive",
        url="https://github.com/DonyorM/weresync",
    )
