# Copyright 2016 Daniel Manila
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module contains several functions common to all modules."""

from weresync.exception import DeviceError, InvalidVersionError
import subprocess
import logging
import logging.handlers
import os
import gettext
import sys

LOGGER = logging.getLogger(__name__)

LANGUAGES = ["en"]
"""Currently translated languages. See `here <translation.html>`_ for more
information."""

DEFAULT_USER_LOG_LOCATION = os.path.expanduser(
    "~/.local/log/weresync/weresync-user.log")
"""The default location for WereSync's user log files."""


def run_proc(args,
             target="",
             error=None,
             valid_returncodes=[0],
             throw_error=DeviceError):
    """Creates an runs a subprocess with the passed args. and throws an error
    if the valid returncodes do not exist.

    This expects either :py:class:`~weresync.exception.DeviceError` or an
    exception which takes 2 arguments, the first for a custom error message
    and the second for the output of the processs.

    :param args: the argument list to run. Passed to the first paramter of
                 `subprocess.Popen`
    :param error: the custom error code to display. Optional
    :param valid_returncodes: the list of return codes which should *not* throw
                              an error.
    :param throw_error: the error class to be thrown if there is an error.
                        Defaults to :py:class:`~weresync.exception.DeviceError`
    :returns: the output of the process
    """
    proc = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = proc.communicate()
    output = str(output, "utf-8")
    if proc.returncode not in valid_returncodes:
        if error is None:
            error = ""
        if throw_error == DeviceError:
            raise DeviceError(target, error, output)
        else:
            raise throw_error(error, output)
    return output


def start_logging_handler(log_loc,
                          stream_level=logging.WARNING,
                          file_level=logging.DEBUG):
    os.makedirs(os.path.dirname(log_loc), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(file_level if file_level < stream_level else stream_level)
    formatter = logging.Formatter(
        "%(levelname)s - %(asctime)s - %(name)s - %(message)s")

    def enableHandler(hand, level, formatter):
        hand.setLevel(level)
        hand.setFormatter(formatter)
        logger.addHandler(hand)

    handler = logging.handlers.TimedRotatingFileHandler(
        log_loc, when="D", interval=1, backupCount=15)
    enableHandler(handler, file_level, formatter)
    streamHandler = logging.StreamHandler()
    enableHandler(streamHandler, stream_level, formatter)
    logging.getLogger("yapsy").setLevel(logging.INFO)


def enable_localization():
    """Activates the `gettext` module to start internalization and enable
    translation."""
    LOGGER.debug("Enabling localization")
    lodir = os.path.dirname(os.path.realpath(__file__)) + "/resources/locale"
    es = gettext.translation("weresync", localedir=lodir, languages=LANGUAGES)
    es.install()


def check_python_version():
    """This method tests if the running version of python supports WereSync.
    If it does not, it raises a InvalidVersionException"""
    try:
        assert sys.version_info > (3, 0)
    except AssertionError:
        info = sys.version_info
        raise InvalidVersionError(
            "Python version {major}.{minor} not supported. WereSync requires "
            "at least Python 3.0\n"
            "Considering installing WereSync with the pip3 command to insure "
            "it installs with Python3.".format(major=info[0], minor=info[1]))
