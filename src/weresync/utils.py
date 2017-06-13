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

from weresync.exception import DeviceError
import subprocess


def run_proc(args, target="", error=None, valid_returncodes=[0],
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
    proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
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
