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
"""This package contains code for bootloader plugins.

Bootloader plugin is any class extending
:py:class:`~weresync.plugins.IBootPlugin` inside a file name following the
regex pattern "^weresync_.*\.py$". These plugins can be installed to the
site-packages directory (for example, using pip) or to
/usr/local/weresync/plugins.

For an example plugin see the `GrubPlugin <https://github.com/DonyorM/weresync/blob/master/src/weresync/plugins/weresync_grub2.py>`_.""" # noqa

from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import (PluginFileAnalyzerMathingRegex,
                                     PluginFileLocator)
from yapsy.IPlugin import IPlugin
from distutils.sysconfig import get_python_lib
import os
import os.path
import weresync.daemon.device as device
from weresync.exception import DeviceError
import sys
import logging

LOGGER = logging.getLogger(__name__)


def translate_uuid(copier, partition, path, target_mnt):
    """Translates all uuids of the files in the given partition at path.
        This will not affect files which are not UTF-8 or ASCII, and it will
        not affect files which are greater than 200 MB.

        :param copier: the object with the DeviceManager instances.
        :param partition: the partition number of the partition to translate.
        :param path: the path of the file to change relative to the mount of
                     the partition. Should start with "/".
        :param target_mnt: the path to the folder where the partitions should
                           be mounted."""

    mounted_here = False
    try:
        mount_point = copier.target.mount_point(partition)
        if mount_point is None:
            copier.target.mount_partition(partition, target_mnt)
            mount_point = target_mnt
            mounted_here = True

        for dname, dirs, files in os.walk(mount_point + path):
            for fname in files:
                # This if block seeks to avoid opening huge files since
                # they are unlikely to be config files like we are looking
                # for.
                fpath = os.path.join(dname, fname)
                if (os.path.getsize(fpath)) / 1000000 > 200:
                    continue

                try:
                    with open(fpath) as file:
                        text = file.read()
                except UnicodeDecodeError as ex:
                    continue

                uuid_dict = copier.get_uuid_dict()
                text = device.multireplace(text, uuid_dict)
                with open(fpath, "w") as f:
                    f.write(text)
    finally:
        if mounted_here:
            copier.target.unmount_partition(partition)


def mount_partition(manager, lvm_manager, part, mount_point):
    """Mounts a partition and figures out whether or not the partition
        is in the LVM drive. It assumes a numerical partition is not a
        logical volume.

        :param manager: a :py:class:`~weresync.device.DeviceManager` object
                        representing a possible mount.
        :param lvm_manager: a :py:class:`~weresync.device.LVMDeviceManager`
                            object representing a possible host for the mount.
        :param part: the name or number of the partition to mount.
        :param mount_point: the location to mount the partition."""

    try:
        part_num = int(part)
        manager.mount_partition(part_num, mount_point)
        return
    except ValueError:
        pass

    lvm_manager.mount_partition(part, mount_point)


def search_for_boot_part(
        target_mnt,
        target_manager,
        search_folder,
        exlcuded_partitions=[],
):
    """Finds the partition that is the boot partition, by searching for
        a specific folder name. The first partition that contains this name
        or /boot/<name> will be returned.

        :param target_mnt: the folder to mount partitions
        :param target_manager: The :py:class:`~weresync.device.DeviceManager`
                               class representing the drive to search.
        :param search_folder: The name of the folder to search for
        :param excluded_partitions: A list containing a list of partitions
                                    which should not be searched."""
    for i in target_manager.get_partitions():
        if i in exlcuded_partitions:
            continue
        try:
            mounted_here = False
            mount_point = target_manager.mount_point(i)
            if mount_point is None:
                target_manager.mount_partition(i, target_mnt)
                mount_point = target_mnt
                mounted_here = True
            mount_point += "/" if not mount_point.endswith("/") else ""
            if (os.path.exists(mount_point + "boot/" + search_folder)
                    or os.path.exists(mount_point + search_folder)):
                return i
        except DeviceError as ex:
            LOGGER.warning("Could not mount partition {0}. "
                           "Assumed to not be the partition grub "
                           "is on.".format(i))
            LOGGER.debug("Error info:\n", exc_info=sys.exc_info())
        finally:
            try:
                if mounted_here:
                    target_manager.unmount_partition(i)
            except DeviceError as ex:
                LOGGER.warning("Error unmounting partition " + i)
                LOGGER.debug("Error info:\n", exc_info=sys.exc_info())
    else:  # No partition found
        return None


class IBootPlugin(IPlugin):
    """An interface class for bootloader plugins. Plugins implementing this class
    must implement the :py:func:`~.IBootPlugin.install_bootloader` method.

    The name of a plugin should simply be its filename, without the
    "weresync\_" prefix or a file extension. So "weresync_grub2.py"'s name
    would be "grub2".

    :param prettyName: a human readable name for display. Can contain any
                       character.
    :param name: A unique identifying name that should be easy to type on
                 a terminal. Used by users to tell WereSync which plugin
                 to use. See above for exact definition."""

    def __init__(self, name, prettyName=None):
        self.name = name
        if prettyName is None:
            self.prettyName = name
        else:
            self.prettyName = prettyName

    def activate(self):
        """Called at plugin activation,right before bootloader is installed.

        This will be called before /etc/fstab has been updated."""
        pass

    def deactivate(self):
        """Called at plugin deactivation, after bootloader has been
        installed."""
        pass

    def install_bootloader(self,
                           source_mnt,
                           target_mnt,
                           copier,
                           excluded_partitions=[],
                           boot_partition=None,
                           root_partition=None,
                           efi_partition=None):
        """Called to make the drive bootable.

        This will be called after /etc/fstab has been updated.

        :param source_mnt: a string representing the directory where
                           partitions from the source drive may be mounted.
        :param target_mnt: a string representing the directory where
                           partitions from the target drive may be mounted.
        :param copier: an instance of :py:class:`~weresync.device.DeviceCopier`
                       which represents the source and target drives.
        :param excluded_partitions: these partitions should not be searched or
                                    included in the boot installation.
        :param boot_partition: this is the partition that should be mounted on
                               /boot of the root_partition.
        :param root_partition: this is the root partition of the drive, where
                               the bootloader should be installed.
        :param efi_partition: this is the partition of the Efi System
                              Partition. Should be None if not a UEFI system.
        :raises DeviceError: if a bootloader installation command has an error.
        """
        pass

    def get_help(self):
        """Returns the help message for this plugin.

        It is optional to override this.

        :returns: a string representing the help message for this plugin."""
        return "Installs the {0} bootloader.".format(self.prettyName)


dirs = [
    "/usr/local/weresync/plugins",
    os.path.dirname(__file__),
    get_python_lib()
]

regex_analyzer = PluginFileAnalyzerMathingRegex("regex", "^weresync_.*\.py$")
locator = PluginFileLocator([regex_analyzer])

__manager = PluginManager(
    categories_filter={"bootloader": IBootPlugin},
    directories_list=dirs,
    plugin_locator=locator)


def get_manager():
    """Returns the PluginManager for this instance of WereSync"""
    return __manager
