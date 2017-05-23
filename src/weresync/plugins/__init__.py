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

For an example plugin see the `py:class:~weresync.plugins.GrubPlugin`."""
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import (PluginFileAnalyzerMathingRegex,
                                     PluginFileLocator)
from yapsy.IPlugin import IPlugin
from distutils.sysconfig import get_python_lib
import os.path as path


class IBootPlugin(IPlugin):
    """An interface class for bootloader plugins. Plugins implementing this class
    must implement the install_bootloader method.

    The name of a plugin should simply be its filename, without the "weresync_"
    prefix or a suffix. So "weresync_grub2.py"'s name would be "grub2".

    :param prettyName: a human readable name for display. Can contain any
                       character.
    :param filename: A unique identifying name that should be easy to type on
                     a terminal. Used by users to tell WereSync which plugin
                     to use. See above for exact definition."""

    def __init__(self, name, prettyName=None):
        self.name = name
        if prettyName is None:
            self.prettyName = name
        else:
            self.prettyName = prettyName

    def activate(self):
        """Called at plugin activation,right before bootloader is installed."""
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

        :param source_mnt: a string representing the directory where
                           partitions from the source drive may be mounted.
        :param target_mnt: a string representing the directory where partitions from the target drive may be mounted.
        :param copier: an instance of :py:class:`~weresync.device.DeviceCopier` which represents the source and target drives.
        :param excluded_partitions: these partitions should not be searched or included in the boot installation.
        :param boot_partition: this is the partition that should be mounted on /boot of the root_partition.
        :param root_partition: this is the root partition of the drive, where the bootloader should be installed.
        :param efi_partition: this is the partition of the Efi System Partition. Should be None if not a UEFI system.
        :raises DeviceError: if a bootloader installation command has an error."""
        pass

    def get_help(self):
        """Returns the help message for this plugin.

        It is optional to override this.

        :returns: a string representing the help message for this plugin."""
        return "Installs the {0} bootloader.".format(self.prettyName)


dirs = [
    "/usr/local/weresync/plugins", get_python_lib(), path.dirname(__file__)
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
