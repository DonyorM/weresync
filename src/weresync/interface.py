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
"""This modules has easy, one function interfaces with the DeviceCopier and
DeviceManager."""

import weresync.device as device
from weresync.exception import (CopyError, DeviceError, InvalidVersionError,
                                UnsupportedDeviceError)
import weresync.utils as utils
import logging
import logging.handlers
import random
import os
import sys
import argparse
import subprocess
import gettext

LOGGER = logging.getLogger(__name__)

DEFAULT_LOG_LOCATION = "/var/log/weresync/weresync.log"
"""The default location for WereSync's log files."""
LANGUAGES = ["en"]
"""Currently translated languages. See `here <translation.html>`_ for more
information."""


def enable_localization():
    """Activates the `gettext` module to start internalization and enable
    translation."""
    LOGGER.debug("Enabling localization")
    lodir = sys.prefix + "/share/locale"
    es = gettext.translation("weresync", localedir=lodir,
                             languages=LANGUAGES)
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
            "it installs with Python3.".
            format(
                major=info[0], minor=info[1]))


def start_logging_handler(log_loc=DEFAULT_LOG_LOCATION,
                          stream_level=logging.WARNING,
                          file_level=logging.DEBUG):
    os.makedirs(os.path.dirname(log_loc), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(file_level if file_level < stream_level else stream_level)
    formatter = logging.Formatter("%(name)s - %(message)s")
    handler = logging.handlers.TimedRotatingFileHandler(
        log_loc, when="D", interval=1, backupCount=15)
    handler.setLevel(file_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(stream_level)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)


def mount_loop_device(image_file):
    """Mounts an image file as a loop device and returns the device name of
    the mounted loop. This mounts on first free loop device. This accepts
    relative paths.

    :params image_file: Path pointing to the image file to mount.
    :returns: A string containing device identifier (/dev/sda or such)"""

    image_file = os.path.abspath(os.path.expanduser(image_file))
    free_proc = subprocess.Popen(
        ["losetup", "-f"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    free_output, free_error = free_proc.communicate()
    if free_proc.returncode != 0:
        raise DeviceError(image_file, "Error finding free loop device.",
                          str(free_output, "utf-8"))

    device_name = str(free_output, "utf-8").strip()
    mount_proc = subprocess.Popen(
        ["losetup", device_name, image_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    mount_output, mount_error = mount_proc.communicate()
    if mount_proc.returncode != 0:
        raise DeviceError(image_file,
                          "Error mounting image on {0}".format(device_name),
                          str(mount_output, "utf-8"))
    subprocess.call(["partprobe", device_name])
    return device_name


def create_new_vg_if_not_exists(lvm, name, target):
    """Creates a new Logical Volume Group with the name ``lvm`` + "copy"
    and all of the partitions of the target with type "lvm" added to it.

    This is not a conclusive function and misses several uses of LVM drives,
    if your situation is not covered, please feel free to open a pull request
    fixing it.

    :param lvm: a string representing the name of the source lvm
    :param target: a :py:class:`~weresync.device.DeviceManager` representing
                   the device whose partitions to add to the LVM."""
    lvm_partitions = []
    for i in target.get_partitions():
        code = target.get_partition_code(i).lower()
        if code == "8e00" or code == "8e":
            # the two versions appear in gdisk and fdisk, respectively
            lvm_partitions.append(i)

    lvm_part_block = [target.part_mask.format(target.device, x)
                      for x in lvm_partitions]
    lvm_test = subprocess.Popen(["vgs", name], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    output, _ = lvm_test.communicate()
    if lvm_test.returncode == 5:
        # If the VG does not exist, the return code is 5
        utils.run_proc(["vgcreate", name] + lvm_part_block,
                       target.device, "Error creating logical volume group.")
    else:
        if name.startswith("/dev/"):
            name = name[5:]
        result = utils.run_proc(["pvs", "-S", "vg_name=" + name,
                                 "--noheadings", "-o", "pv_name"], name,
                                "Error finding physical volumes for LVM.")
        LOGGER.debug("PVs in LVM: " + result)
        results = [x.strip() for x in result.split("\n")]
        lvm_part_block = [x for x in lvm_part_block if x not in results]
        if len(lvm_part_block) > 0:
            utils.run_proc(["vgextend", name] + lvm_part_block, name,
                           "Error adding PVs to LVM")


def copy_partitions(copier, part_callback=None, lvm=False):
    """Checks if partitions are valid and copies if they aren't.

    :param copier: the :py:class:`~weresync.device.DeviceCopier` object to do
                   the copying with.
    :param part_callback: see the documentation for :py:func:`~.copy_drive`"""
    try:
        print(_("Checking partition validity."))
        copier.partitions_valid(lvm)
        if part_callback is not None:
            part_callback(1.0)
            LOGGER.info("Drives are compatible")
    except CopyError as ex:
        LOGGER.warning(ex.message)
        print(_("Partitions invalid!\nCopying drive partition table."))
        LOGGER.warning("Drives are incompatible.")
        if lvm:
            copier.transfer_lvm_partition(callback=part_callback)
        else:
            copier.transfer_partition_table(callback=part_callback)
    else:
        if part_callback is not None:
            part_callback(1.0)


def copy_drive(source,
               target,
               check_if_valid_and_copy=False,
               source_part_mask="{0}{1}",
               target_part_mask="{0}{1}",
               excluded_partitions=[],
               ignore_copy_failures=True,
               root_partition=None,
               boot_partition=None,
               efi_partition=None,
               mount_points=None,
               rsync_args=device.DEFAULT_RSYNC_ARGS,
               lvm_source=None,
               lvm_target=None,
               bootloader="uuid_copy",
               part_callback=None,
               copy_callback=None,
               boot_callback=None):
    """Uses a DeviceCopier to clone the source drive to the target drive.

    **Note:** if using LVM, any uses of "partition" in the documentation
    actually refer to logical volumes.

    It is recommended to set ``check_if_valid_and_copy`` to True if the the
    two drives are not the same size with the same partitions.

    If either source or target ends in ".img" copy_drives will assume it is an
    image file, and mount if accordingly.

    :param source: The drive identifier ("/dev/sda" or the like) of the source
                   drive.
    :param target: The drive identifier ("/dev/sda" or the like) of the target
                   drive.
    :param check_if_valid=False: If true, the function checks if the target
                                 drive is compatible to receive the source
                                 drive's data. If it is not, erase the target
                                 drive and make a proper partition table.
                                 Defaults to False.
    :param source_part_mask: A string to be passed to the "format" method that
                             expects to arguments, the drive name and the
                             partition number. Applied to the source drive.
                             Defaults to "{0}{1}".
    :param target_part_mask: Same as source_part_mask, but applied to target
                             drive. Defaults to "{0}{1}"
    :param excluded_partitions: Partitions to not copy or test for boot
                                capability.
    :param ignore_copy_failures: If True, errors during copying will be
                                 ignored and copying will continue. It is
                                 recommended that this be left to true,
                                 because errors frequently occur with swap
                                 partitions or other strange partitions.
    :param root_partition: If not None, this is an int that determines which
                           partition grub should be installed to. Defaults to
                           None.
    :param boot_partition: If not None, this is an int that represents the
                           partition to mount at /boot when installing grub.
    :param efi_partition: If not None, this is an int that represents the
                          partition to mount at /boot/efi when installing grub.
    :param mount_points: Expects a tuple containing two strings pointing to
                         the directories where partitions should be mounted in
                         case of testing. If None, the function will generate
                         two random directories in the /tmp folder. Defaults
                         to None.
    :param lvm: the Logical Volume Group to copy to the new drive.
    :param part_callback: a function that can be called to pass the progress
                          of the partition function. The function should
                          expect on float between 0 and 1, a negative value
                          denoting an error, or a boolean True to indicate the
                          progress is indeterminate.
    :param copy_callback: a function that can be called to pass the progress
                          of copying partitions. The function should expect
                          two arguments: an integer showing partition number
                          and a float showing progress between 0 and 1
    :param boot_callback: a function that can be called to pass the progress
                          of making the clone bootable. The function should
                          expect one argument: a boolean indicating whether or
                          not the process has finished.

    :raises DeviceError: If there is an error reading data from one device or
                         another.
    :raises CopyError: If there is an error copying the data between the two
                       devices.

    :returns: True on success and an error message or exception on failure.
    """
    try:
        source_loop = None
        target_loop = None
        if source.endswith(".img"):
            source_loop = mount_loop_device(source)
            source = source_loop
            source_part_mask = "{0}p{1}"

        if target.endswith(".img"):
            target_loop = mount_loop_device(target)
            target = target_loop
            target_part_mask = "{0}p{1}"
            LOGGER.warning(
                "Right now, WereSync does not properly install bootloaders on "
                "image files. You will have to handle that yourself if you "
                "want your image to be bootable."
            )

        source_manager = device.DeviceManager(source, source_part_mask)
        target_manager = device.DeviceManager(target, target_part_mask)

        try:
            target_manager.get_partition_table_type()
        except (DeviceError, UnsupportedDeviceError) as ex:
            # Since we're erasing the target drive anyway, we can just create
            # a new disk label
            proc = subprocess.Popen(["sgdisk", "-o", target_manager.device])
            proc.communicate()

        copier = device.DeviceCopier(source_manager, target_manager)
        partitions_remade = False
        if check_if_valid_and_copy:
            copy_partitions(copier, part_callback)
            partitions_remade = True

        if lvm_source is not None:
            create_new_vg_if_not_exists(lvm_source, lvm_source +
                                        "-copy", target_manager)
            lvm_source = device.LVMDeviceManager(lvm_source)
            lvm_target = device.LVMDeviceManager(lvm_source.device + "-copy")
            copier.lvm_source = lvm_source
            copier.lvm_target = lvm_target
            if partitions_remade and check_if_valid_and_copy:
                copy_partitions(copier, part_callback, lvm=True)

        if mount_points is None or len(mount_points) < 2 or mount_points[
                0] == mount_points[1]:
            source_dir = "/tmp/" + str(random.randint(0, 100000))
            target_dir = "/tmp/" + str(random.randint(-100000, -1))
            os.makedirs(source_dir, exist_ok=True)
            os.makedirs(target_dir, exist_ok=True)
            mount_points = (source_dir, target_dir)

        print(_("Beginning to copy files."))
        copier.copy_files(
            mount_points[0],
            mount_points[1],
            excluded_partitions,
            ignore_copy_failures,
            rsync_args,
            callback=copy_callback)
        print(_("Finished copying files."))

        print(_("Making bootable"))
        try:
            copier.make_bootable(bootloader, mount_points[0], mount_points[1],
                                 excluded_partitions, root_partition,
                                 boot_partition, efi_partition, boot_callback)
        except DeviceError as ex:
            print(_("Error making drive bootable. All files should be fine."))
            return ex
        print(_("All done, enjoy your drive!"))
        return True
    finally:

        def delete_loop(loop_name):
            subprocess.call(["losetup", "-d", loop_name])

        if source_loop is not None:
            delete_loop(source_loop)
        if target_loop is not None:
            delete_loop(target_loop)


def main():
    """The entry point for the command line function. This uses argparse to
    parse arguments to call call :py:func:`.copy_drive` with. For help use
    "weresync -h" in a commandline after installation."""
    enable_localization()

    try:
        check_python_version()
    except InvalidVersionError as ex:
        print(ex)
        sys.exit(1)

    try:
        import weresync.plugins as plugins
        manager = plugins.get_manager()
        manager.collectPlugins()
        default_part_mask = "{0}{1}"
        pluginNames = []
        for pluginInfo in manager.getAllPlugins():
            pluginNames.append(pluginInfo.plugin_object.name)
        epilog_string = (_("Bootloader plugins found: ")
                         + ", ".join(pluginNames))
        parser = argparse.ArgumentParser(epilog=epilog_string)
        parser.add_argument(
            "source",
            help=_("The drive to copy data from. This drive will not be"
                   " edited."))
        parser.add_argument(
            "target",
            help=_("The drive to copy data to. ALL DATA ON THIS DRIVE WILL BE "
                   "ERASED.")
        )
        parser.add_argument(
            "-C",
            "--check-and-partition",
            action="store_true",
            help=_("Check if partitions are valid and re-partition drive to "
                   "proper partitions if they are not.")
        )
        parser.add_argument(
            "-s",
            "--source-mask",
            help=_("A string of format '{0}{1}' where {0} represents drive "
                   "identifier and {1} represents partition number to point "
                   "to partition block files for the source drive.")
        )
        parser.add_argument(
            "-t",
            "--target-mask",
            help=_("A string of format '{0}{1}' where {0} represents drive "
                   "identifier and {1} represents partition number to point "
                   "to partition block files for the target drive."))
        parser.add_argument(
            "-e",
            "--excluded-partitions",
            help=_("A comment separated list of partitions of the source "
                   "drive to apply no actions on.perated list of partitions "
                   "of the source drive to apply no actions on.")
        )
        parser.add_argument(
            "-b",
            "--break-on-error",
            action="store_false",
            help=_("Causes program to break whenever a partition cannot be "
                   "copied, including uncopyable partitions such as swap"
                   " files. Not recommended.")
        )
        parser.add_argument(
            "-g",
            "--root-partition",
            type=int,
            help=_("The partition mounted on /."))
        parser.add_argument(
            "-B",
            "--boot-partition",
            type=int,
            help=_("Partition which should be mounted on /boot"))
        parser.add_argument(
            "-E",
            "--efi-partition",
            type=int,
            help=_("Partition which should be mounted on /boot/efi"))
        parser.add_argument(
            "-m",
            "--source-mount",
            help=_("Folder where partitions from the source drive should be "
                   "mounted.")
        )
        parser.add_argument(
            "-M",
            "--target-mount",
            help=_("Folder where partitions from source drive should be"
                   " mounted.")
        )
        parser.add_argument(
            "-r",
            "--rsync-args",
            help=_("List of arguments passed to rsync. Defaults to: ") +
            device.DEFAULT_RSYNC_ARGS,
            default=device.DEFAULT_RSYNC_ARGS)
        parser.add_argument(
            "-L",
            "--bootloader",
            help=_("Passed to decide what boootloader plugin to use. See "
                   "below for list of plugins. Defaults to simply changing "
                   "the UUIDs of files in /boot."),
            default="uuid_copy")
        parser.add_argument(
            "-l",
            "--lvm",
            help=_("The name of the source logical volume."),
            nargs="+")
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-v",
            "--verbose",
            help=_("Prints expanded output."),
            action="store_const",
            dest="loglevel",
            const=logging.INFO)
        group.add_argument(
            "-d",
            "--debug",
            help=_("Prints large output. Mainly helpful for developers."),
            action="store_const",
            dest="loglevel",
            const=logging.DEBUG)
        args = parser.parse_args()
        if (args.loglevel == logging.INFO or args.loglevel == logging.DEBUG):
            loglevel = args.loglevel
        else:
            loglevel = logging.WARNING
        start_logging_handler(stream_level=loglevel)
        mount_points = (args.source_mount, args.target_mount)
        if args.lvm is not None and len(args.lvm) > 2:
            LOGGER.warning(_("More than two lvm options added. Please give "
                           "either one or two options."))
            sys.exit(1)

        lvm_source = args.lvm[0] if args.lvm is not None else None
        lvm_target = args.lvm[1] if (args.lvm is not None
                                     and len(args.lvm) == 2) else None

        excluded_partitions = [
            int(x) for x in args.excluded_partitions.split(",")
        ] if args.excluded_partitions is not None else []
        source_mask = (args.source_mask if args.source_mask is not None else
                       default_part_mask)
        target_mask = (args.target_mask if args.target_mask else
                       default_part_mask)
        result = copy_drive(
            args.source,
            args.target,
            args.check_and_partition,
            source_mask,
            target_mask,
            excluded_partitions,
            args.break_on_error,
            args.root_partition,
            args.boot_partition,
            args.efi_partition,
            mount_points,
            args.rsync_args,
            lvm_source=lvm_source,
            lvm_target=lvm_target,
            bootloader=args.bootloader,)
        if result is not True:
            print(str(result))

    except (KeyboardInterrupt, EOFError):
        LOGGER.info("Exiting via user keyboard interrupt.")
        LOGGER.debug("Error:\n", exc_info=sys.exc_info())
        sys.exit(1)
