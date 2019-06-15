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
"""Connects the interface applications (cli and gui) with the backend daemon.

See also :mod:`weresync.daemon.daemon`"""
from pydbus import SystemBus
from gi.repository import GLib
import threading
import gi.repository.GLib

try:
    bus = SystemBus()
    drive_copier = bus.get("net.manilas.weresync.DriveCopier")
    copy_drive = drive_copier.CopyDrive
    """A function which connects to :meth:`weresync.daemon.device.copy_drive`:.
    For arguments see that function's documentation. If False, WereSync failed
    to connect to dbus."""
    error = None
except gi.repository.GLib.Error as e:
    error = e
    """The error created by connecting to dbus. If no error, then None."""
    copy_drive = False


def _unthreaded_subscribe_to_signals(
        partition_status_callback, copy_status_callback, boot_status_callback):
    drive_copier.PartitionStatus.connect(partition_status_callback)
    drive_copier.CopyStatus.connect(copy_status_callback)
    drive_copier.BootStatus.connect(boot_status_callback)
    loop = GLib.MainLoop()
    loop.run()


def subscribe_to_signals(partition_status_callback, copy_status_callback,
                         boot_status_callback):
    """Subscribes to the weresync callbacks to get information from the daemon.

    :param partition_status_callback: A function which takes a float between 0
                                      and 1 which represents the progress on
                                      formatting partitions.
    :param copy_status_callback: A function which takes an integer representing
                                 the partition being copied and a float between
                                 0 and 1 representing the progress on the copy.
    :param boot_status_callback: A function which takes a boolean. If passed
                                 False the bootloader has not finished
                                 installing. If True it has."""
    thread = threading.Thread(
        target=_unthreaded_subscribe_to_signals,
        args=(partition_status_callback, copy_status_callback,
              boot_status_callback))
    thread.daemon = True
    thread.start()
