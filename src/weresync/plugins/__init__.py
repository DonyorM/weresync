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
import weresync.device as device


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
                    if (os.path.getsize(fpath))/1000000 > 200:
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
    "/usr/local/weresync/plugins", get_python_lib(), os.path.dirname(__file__)
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


def get_plugin_for_name(name):
    __manager.collectPlugins()
