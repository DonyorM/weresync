import weresync.daemon.device as device
import weresync.utils as utils
from weresync.exception import (CopyError, DeviceError, UnsupportedDeviceError)
import random
import os
import logging
import subprocess
from pydbus.generic import signal

LOGGER = logging.getLogger(__name__)


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

    lvm_part_block = [
        target.part_mask.format(target.device, x) for x in lvm_partitions
    ]
    lvm_test = subprocess.Popen(
        ["vgs", name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = lvm_test.communicate()
    if lvm_test.returncode == 5:
        # If the VG does not exist, the return code is 5
        utils.run_proc(["vgcreate", name] + lvm_part_block, target.device,
                       "Error creating logical volume group.")
    else:
        if name.startswith("/dev/"):
            name = name[5:]
        result = utils.run_proc(
            ["pvs", "-S", "vg_name=" + name, "--noheadings", "-o", "pv_name"],
            name, "Error finding physical volumes for LVM.")
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


class DriveCopier(object):
    """Object which is shared over dbus to allow interfaces to access the
    daemon."""

    def __init__(self):
        LOGGER.debug("making object")
        self._interface_name = "net.manilas.weresync.DriveCopier"

    dbus = """<node>
      <interface name='net.manilas.weresync.DriveCopier'>
        <method name='CopyDrive'>
          <arg type='s' name='source' direction='in' />
          <arg type='s' name='target' direction='in' />
          <arg type='b' name='check_if_valid_and_copy' direction='in' />
          <arg type='s' name='source_part_mask' direction='in' />
          <arg type='s' name='target_part_mask' direction='in' />
          <arg type='ai' name='excluded_partitions' direction='in' />
          <arg type='b' name='ignore_copy_failures' direction='in' />
          <arg type='i' name='root_partition' direction='in' />
          <arg type='i' name='boot_partition' direction='in' />
          <arg type='i' name='efi_partition' direction='in' />
          <arg type='(ss)' name='mount_points' direction='in' />
          <arg type='s' name='rsync_args' direction='in' />
          <arg type='s' name='lvm_source' direction='in' />
          <arg type='s' name='lvm_target' direction='in' />
          <arg type='s' name='bootloader' direction='in' />
          <arg type='s' name='return' direction='out' />
        </method>
        <method name='GetPartitions'>
          <arg type='s' name='device' direction='in' />
          <arg type='s' name='part_mask' direction='in' />
          <arg type='b' name='lvm' direction='in' />
          <arg type='as' name='partitions' direction='out' />
        </method>
        <signal name="PartitionStatus">
          <arg type='d' name='percent_complete' direction='out' />
        </signal>
        <signal name="CopyStatus">
          <arg type='d' name='percent_complete' direction='out' />
          <arg type='i' name='current_partition' direction='out' />
        </signal>
        <signal name="BootStatus">
          <arg type='b' name='completed' direction='out' />
        </signal>
      </interface>
    </node>"""

    PartitionStatus = signal()
    CopyStatus = signal()
    BootStatus = signal()

    def GetPartitions(self, device_name, part_mask, lvm):
        """Gets the partitions of the specified device. Note that this
        will always return a list of strings, however if this is not an LVM
        device, all of the strings will be valid numbers."""
        if lvm:
            source_manager = device.LVMDeviceManager(device_name)
        else:
            source_manager = device.DeviceManager(device_name, part_mask)
        parts = source_manager.get_partitions()
        for idx, val in enumerate(parts):
            if type(val) != str:
                parts[idx] = str(val)
        return parts

    def CopyDrive(self,
                  source,
                  target,
                  check_if_valid_and_copy=False,
                  source_part_mask="{0}{1}",
                  target_part_mask="{0}{1}",
                  excluded_partitions=[],
                  ignore_copy_failures=True,
                  root_partition=-1,
                  boot_partition=-1,
                  efi_partition=-1,
                  mount_points=("", ""),
                  rsync_args=device.DEFAULT_RSYNC_ARGS,
                  lvm_source="",
                  lvm_target="",
                  bootloader="uuid_copy"):
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

        :raises DeviceError: If there is an error reading data from one device or
                             another.
        :raises CopyError: If there is an error copying the data between the two
                           devices.

        :returns: True on success and an error message or exception on failure.
        """
        LOGGER.debug("Daemon starting clone.")

        def part_callback(status):
            self.PartitionStatus(status)

        def copy_callback(current, status):
            self.CopyStatus(current, status)

        def boot_callback(status):
            self.BootStatus(status)

        root_partition = root_partition if root_partition >= 0 else None
        boot_partition = boot_partition if boot_partition >= 0 else None
        efi_partition = efi_partition if efi_partition >= 0 else None

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
                    "want your image to be bootable.")

            source_manager = device.DeviceManager(source, source_part_mask)
            target_manager = device.DeviceManager(target, target_part_mask)

            try:
                target_manager.get_partition_table_type()
            except (DeviceError, UnsupportedDeviceError) as ex:
                # Since we're erasing the target drive anyway, we can just create
                # a new disk label
                proc = subprocess.Popen(
                    ["sgdisk", "-o", target_manager.device])
                proc.communicate()

            copier = device.DeviceCopier(source_manager, target_manager)
            partitions_remade = False
            if check_if_valid_and_copy:
                copy_partitions(copier, part_callback)
                partitions_remade = True

            if lvm_source is not "":
                create_new_vg_if_not_exists(lvm_source, lvm_source + "-copy",
                                            target_manager)
                lvm_source = device.LVMDeviceManager(lvm_source)
                lvm_target = device.LVMDeviceManager(lvm_source.device +
                                                     "-copy")
                copier.lvm_source = lvm_source
                copier.lvm_target = lvm_target
                if partitions_remade and check_if_valid_and_copy:
                    copy_partitions(copier, part_callback, lvm=True)

            if mount_points is ("", "") or len(
                    mount_points) < 2 or mount_points[0] == mount_points[1]:
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
                copier.make_bootable(bootloader, mount_points[0],
                                     mount_points[1], excluded_partitions,
                                     root_partition, boot_partition,
                                     efi_partition, boot_callback)
            except DeviceError as ex:
                print(
                    _("Error making drive bootable. All files should be fine.")
                )
                return ex
            print(_("All done, enjoy your drive!"))
            return "True"
        finally:

            def delete_loop(loop_name):
                subprocess.call(["losetup", "-d", loop_name])

            if source_loop is not None:
                delete_loop(source_loop)
            if target_loop is not None:
                delete_loop(target_loop)
