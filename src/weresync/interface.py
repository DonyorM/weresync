#Copyright 2016 Daniel Manila
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
"""This modules has easy, one function interfaces with the DeviceCopier and DeviceManager."""

import weresync.device as device
from weresync.exception import CopyError
import logging
import random
import os
import argparse

LOGGER = logging.getLogger(__name__)

def copy_drive(source, target,
               check_if_valid_and_copy=False,
               source_part_mask="{0}{1}",
               target_part_mask="{0}{1}",
               excluded_partitions=[],
               ignore_copy_failures=True,
               grub_partition=None,
               boot_partition=None,
               efi_partition=None,
               mount_points=None):
    """Uses a DeviceCopier to clone the source drive to the target drive.

    It is recommended to set check_if_valid_and_copy to True if the the two drives are not the same size with the same partitions.

    :param source: The drive identifier ("/dev/sda" or the like) of the source drive.
    :param target: The drive identifier ("/dev/sda" or the like) of the target drive.
    :param check_if_valid=False: If true, the function checks if the target drive is compatible to receive the source drive's data. If it is not, erase the target drive and make a proper partition table. Defaults to False.
    :param source_part_mask: A string to be passed to the "format" method that expects to arguments, the drive name and the partition number. Applied to the source drive. Defaults to "{0}{1}".
    :param target_part_mask: Same as source_part_mask, but applied to target drive. Defaults to "{0}{1}"
    :param excluded_partitions: Partitions to not copy or test for boot capability.
    :param ignore_copy_failures: If True, errors during copying will be ignored and copying will continue. It is recommended that this be left to true, because errors frequently occur with swap partitions or other strange partitions.
    :param grub_partition: If not None, this is an int that determines which partition grub should be installed to. Defaults to None.
    :param boot_partition: If not None, this is an int that represents the partition to mount at /boot when installing grub.
    :param efi_partition: If not None, this is an int that represents the partition to mount at /boot/efi when installing grub.
    :param mount_points: Expects a tuple containing two strings pointing to the directories where partitions should be mounted in case of testing. If None, the function will generate two random directories in the /tmp folder. Defaults to None.

    :returns: True on success and an error message or exception on failure.
    """
    source_manager = device.DeviceManager(source, source_part_mask)
    target_manager = device.DeviceManager(target, target_part_mask)
    copier = device.DeviceCopier(source_manager, target_manager)
    if check_if_valid_and_copy:
        try:
            print("Checking partition validity.")
            copier.partitions_valid()
            LOGGER.info("Drives are compatible")
        except CopyError as ex:
            LOGGER.warning(ex.message)
            print("Partitions invalid!\nCopying drive partition table.")
            LOGGER.warning("Drives are incompatible.")
            copier.transfer_partition_table()

    if mount_points == None or len(mount_points) < 2 or mount_points[0] == mount_points[1]:
        source_dir = "/tmp/" + str(random.randint(0, 100000))
        target_dir = "/tmp/" + str(random.randint(-100000, -1))
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)
        mount_points = (source_dir, target_dir)

    print("Beginning to copy files.")
    copier.copy_files(mount_points[0], mount_points[1], excluded_partitions, ignore_copy_failures)
    print("Finished copying files.")
    print("Making bootable")
    copier.make_bootable(mount_points[0], mount_points[1], excluded_partitions, grub_partition, boot_partition, efi_partition)
    print("All done, enjoy your drive!")
    return True

def main():
    """The entry point for the command line function. This uses argparse to parse arguments to call call :py:func:`.copy_drive` with. For help use "weresync -h" in a commandline after installation."""
    default_part_mask="{0}{1}"
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="The drive to copy data from. This drive will not be edited.")
    parser.add_argument("target", help="The drive to copy data to. ALL DATA ON THIS DRIVE WILL BE ERASED.")
    parser.add_argument("-C", "--check-and-partition", action="store_true",
                        help="Check if partitions are valid and re-partition drive to proper partitions if they are not.")
    parser.add_argument("-s", "--source-mask",
                        help="A string of format '{0}{1}' where {0} represents drive identifier and {1} represents partition number to point to partition block files for the source drive.")
    parser.add_argument("-t", "--target-mask",
                        help="A string of format '{0}{1}' where {0} represents drive identifier and {1} represents partition number to point to partition block files for the target drive.")
    parser.add_argument("-e", "--excluded-partitions",
                        help="A comment separated list of partitions of the source drive to apply no actions on.perated list of partitions of the source drive to apply no actions on.")
    parser.add_argument("-b", "--break-on-error", action="store_false",
                        help="Causes program to break whenever a partition cannot be copied, including uncopyable partitions such as swap files. Not recommended.")
    parser.add_argument("-g", "--grub-partition", type=int,
                        help="Partition where grub should be installed.")
    parser.add_argument("-B", "--boot-partition", type=int,
                        help="Partition which should be mounted on /boot")
    parser.add_argument("-E", "--efi-partition", type=int,
                        help="Partition which should be mounted on /boot/efi")
    parser.add_argument("-m", "--source-mount",
                        help="Folder where partitions from the source drive should be mounted.")
    parser.add_argument("-M", "--target-mount",
                        help="Folder where partitions from source drive should be mounted.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="Prints expanded output.",
                       action="store_const", dest="loglevel", const=logging.INFO)
    group.add_argument("-d", "--debug", help="Prints large output. Mainly helpful for developers.",
                       action="store_const", dest="loglevel", const=logging.DEBUG)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    mount_points = (args.source_mount, args.target_mount)
    excluded_partitions = [int(x) for x in args.excluded_partitions.split(",")] if args.excluded_partitions != None else []
    source_mask = args.source_mask if args.source_mask != None else default_part_mask
    target_mask = args.target_mask if args.target_mask else default_part_mask
    copy_drive(args.source, args.target, args.check_and_partition,
               source_mask, target_mask, excluded_partitions,
               args.break_on_error, args.grub_partition,
               args.boot_partition, args.efi_partition,
               mount_points)
