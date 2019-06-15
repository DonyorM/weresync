#! /usr/bin/env python3
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
"""Runs the daemon and exposes the necessary methods to the interface
functions.

See also :mod:`weresync.interface.dbus_client`:"""

from weresync.daemon.copier import DriveCopier
from gi.repository import GLib
from pydbus import SystemBus
import weresync.utils as utils
import logging

DEFAULT_DAEMON_LOG_LOCATION = "/var/log/weresync/weresync.log"

LOGGER = logging.getLogger(__name__)


def run():
    """Function which starts the daemon and publishes the
    :class:`~weresync.daemon.copier.DriveCopier` over dbus."""
    utils.start_logging_handler(DEFAULT_DAEMON_LOG_LOCATION)
    utils.enable_localization()
    with SystemBus() as bus:
        with bus.publish("net.manilas.weresync.DriveCopier", DriveCopier()):
            GLib.idle_add(lambda: LOGGER.debug("Starting GLib loop"))
            loop = GLib.MainLoop()
            loop.run()


if __name__ == "__main__":
    run()
