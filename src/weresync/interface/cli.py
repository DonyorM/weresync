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
"""This modules has easy, one function interfaces with the DeviceCopier and
DeviceManager."""

import weresync.daemon.device as device
from weresync.exception import InvalidVersionError
import weresync.interface.dbus_client as dbus_client
import logging
import logging.handlers
import sys
import argparse
import weresync.utils as utils

LOGGER = logging.getLogger(__name__)

DEFAULT_LENGTH = 60

partition_copying_completed = False


def _print_progress_bar(iteration,
                        total,
                        prefix='',
                        suffix='',
                        decimals=1,
                        length=DEFAULT_LENGTH,
                        fill='█'):
    """
    Call in a loop to create terminal progress bar

    Thanks to Greentick from StackOverflow for this function
    https://stackoverflow.com/a/34325723/2719960
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    # the first part of the above tuple is the terminal width
    percent = ("{0:." + str(decimals) + "f}").format(
        100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def main():
    """The entry point for the command line function. This uses argparse to
    parse arguments to call call :py:func:`.copy_drive` with. For help use
    "weresync -h" in a commandline after installation."""

    if not dbus_client.copy_drive:
        LOGGER.error("Failed to connect to dbus service. Is it running?")
        LOGGER.log(logging.DEBUG, "DBus Connection error:",
                   dbus_client.error)
        return

    def part_callback(status):
        global partition_copying_completed
        if not partition_copying_completed:
            _print_progress_bar(
                int(status * 100), 100, prefix=_("Partition Table Copying:"))
        if status >= 1:
            partition_copying_completed = True

    def copy_callback(partition_num, status):
        _print_progress_bar(
            int(status * 100) if status >= 0 else 0,
            100,
            prefix=_("Copying Partition {0}:").format(partition_num))
        if status < 0:
            print()
            print(
                _("Some error copying partition {0}. "
                  "Probably fine, but see logs.").format(partition_num))

    def boot_callback(status):
        if status:
            print(_("Bootloader installed"))
        # Passes true when completed. CMD doesn't have display for
        # incomplete installation so only test if True

    utils.enable_localization()
    dbus_client.subscribe_to_signals(part_callback, copy_callback,
                                     boot_callback)

    try:
        utils.check_python_version()
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
        epilog_string = (
            _("Bootloader plugins found: ") + ", ".join(pluginNames))
        parser = argparse.ArgumentParser(epilog=epilog_string)
        parser.add_argument(
            "source",
            help=_("The drive to copy data from. This drive will not be"
                   " edited."))
        parser.add_argument(
            "target",
            help=_("The drive to copy data to. ALL DATA ON THIS DRIVE WILL BE "
                   "ERASED."))
        parser.add_argument(
            "-C",
            "--check-and-partition",
            action="store_true",
            help=_("Check if partitions are valid and re-partition drive to "
                   "proper partitions if they are not."))
        parser.add_argument(
            "-s",
            "--source-mask",
            help=_("A string of format '{0}{1}' where {0} represents drive "
                   "identifier and {1} represents partition number to point "
                   "to partition block files for the source drive."))
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
                   "of the source drive to apply no actions on."))
        parser.add_argument(
            "-b",
            "--break-on-error",
            action="store_false",
            help=_("Causes program to break whenever a partition cannot be "
                   "copied, including uncopyable partitions such as swap"
                   " files. Not recommended."))
        parser.add_argument(
            "-g",
            "--root-partition",
            type=int,
            help=_("The partition mounted on /."),
            default=-1)
        parser.add_argument(
            "-B",
            "--boot-partition",
            type=int,
            help=_("Partition which should be mounted on /boot"),
            default=-1)
        parser.add_argument(
            "-E",
            "--efi-partition",
            type=int,
            help=_("Partition which should be mounted on /boot/efi"),
            default=-1)
        parser.add_argument(
            "-m",
            "--source-mount",
            help=_("Folder where partitions from the source drive should be "
                   "mounted."),
            default="")
        parser.add_argument(
            "-M",
            "--target-mount",
            help=_("Folder where partitions from source drive should be"
                   " mounted."),
            default="")
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
        utils.start_logging_handler(
            utils.DEFAULT_USER_LOG_LOCATION, stream_level=loglevel)
        mount_points = (args.source_mount, args.target_mount)
        if args.lvm is not None and len(args.lvm) > 2:
            LOGGER.warning(
                _("More than two lvm options added. Please give "
                  "either one or two options."))
            sys.exit(1)

        lvm_source = args.lvm[0] if args.lvm is not None else ""
        lvm_target = args.lvm[1] if (args.lvm is not None
                                     and len(args.lvm) == 2) else ""

        excluded_partitions = [
            int(x) for x in args.excluded_partitions.split(",")
        ] if args.excluded_partitions is not None else []
        source_mask = (args.source_mask
                       if args.source_mask is not None else default_part_mask)
        target_mask = (args.target_mask
                       if args.target_mask else default_part_mask)
        result = dbus_client.copy_drive(
            args.source, args.target, args.check_and_partition,
            source_mask, target_mask, excluded_partitions,
            args.break_on_error, args.root_partition, args.boot_partition,
            args.efi_partition, mount_points, args.rsync_args, lvm_source,
            lvm_target, args.bootloader)
        if result == "True":
            print(_("All done, enjoy your drive!"))
        else:
            print(str(result))

    except (KeyboardInterrupt, EOFError):
        LOGGER.info("Exiting via user keyboard interrupt.")
        LOGGER.debug("Error:\n", exc_info=sys.exc_info())
        sys.exit(1)


if __name__ == "__main__":
    main()
