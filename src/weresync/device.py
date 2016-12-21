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
"""This module contains the classes used to modify block devices and copy data."""

import os.path as path
import shlex
import os
import subprocess
import random
import shutil
import weresync.exception
import random
import shlex
import math
import logging
import sys
import glob
import parse

MOUNT_POINT = "/mnt"

LOGGER = logging.getLogger(__name__)
SUPPORTED_FILESYSTEM_TYPES = ["swap", "ef"]
for word in glob.glob("/*/mkfs.*"):
    val = word.split(".")
    SUPPORTED_FILESYSTEM_TYPES += val

SUPPORTED_PARTITION_TABLE_TYPES = ["gpt", "msdos"]
"""The names, as reported by `parted` of the partition table types supported by this program."""
DEFAULT_RSYNC_ARGS = "-aAXxH --delete"
"""Default arguments passed to rsync. See rsync documentation for what they do."""

class DeviceManager:
    """A class that allows various operations on a device.

    Most methods in this class raise :py:class:`~weresync.exception.DeviceError`
    if the subprocess they initiate has an error.

    :param device: a string containing the device identifier (/dev/sda or the like)
    :param partition_mask: a string as the first parameter of a the expression: "partion_mask.format(device, partition)" resolving to a string. Defaults to "{0}{1}"."""

    def __init__(self, device, partition_mask="{0}{1}"):
        """Defines a device manager for the passed device.

        :param device: a string containing the device identifier (/dev/sda or the like)
        :param partition_mask: a string as the first parameter of a the expression: "partion_mask.format(device, partition)" resolving to a string. Defaults to "{0}{1}"."""
        self.device = device
        self.part_mask = partition_mask

    def get_partitions(self):
        """Returns a list with all the partitions in the drive. The partitions will be listed in **the order they appear on the disk**. So if partition 4 has a start sector of 500, it will appear before partition 1 that has a start sectro of 2000

        :returns: A list of integers representing the partition numbers"""
        partition_table_proc = subprocess.Popen(["parted", "-s", self.device, "p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error =  partition_table_proc.communicate()
        exit_code = partition_table_proc.returncode
        if exit_code != 0:
            raise weresync.exception.DeviceError(self.device, "Non-zero exit code", str(error, "utf-8"))
        partition_result = str(output, "utf-8").split("\n")
        partitions = []
        for i in partition_result:
            line = i.strip().split()
            if len(line) == 0:
                continue #It was an empty line
            num = None
            try:
                num = int(line[0])
            except ValueError:
                continue
            partitions.append(num)
        return partitions

    def mount_point(self, partition_num):
        """Returns an absolute path to the mountpoint of the specific partition.
        Returns None if no mountpoint found (probably because partion not mounted).

        :param partition_num: The partition of whose mount to find."""

        findprocess = subprocess.Popen(["findmnt", "-o", "TARGET", self.part_mask.format(self.device, partition_num)], stdout=subprocess.PIPE)
        output, error = findprocess.communicate()
        result = str(output, "utf-8").split("\n")
        exit_code = findprocess.returncode
        if exit_code != 0 and exit_code != 1: #if nothing is find, findmnt returns 1; this is valid code
            raise weresync.exception.DeviceError(self.device, "Non-zero exit code", str(error, "utf-8"))

        if len(result) >= 2:
            return result[1].strip().split()[0]
        else:
            return None

    def mount_partition(self, partition_num, mount_loc):
        """Mounts the specified partition at the specified location.

        :param partition_num: the number of the partition to mount
        :param mount_loc: the location at which to mount the drive
        :raises: :py:class:`~weresync.exception.DeviceError` if there is an error mounting the device.
        """

        mount_proc = subprocess.Popen(["mount", self.part_mask.format(self.device, partition_num), mount_loc], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = mount_proc.communicate()
        exit_code = mount_proc.returncode
        if exit_code != 0:
            raise weresync.exception.DeviceError(self.device, "Non-zero exit code. Partition Number: {0}".format(partition_num), str(error, "utf-8"))

        #if no error, mount succeeded

    def unmount_partition(self, partition_num):
        """Unmounts a device.

        :param partition_num: the number of the partition to unmount.
        :raises: :py:class:`~weresync.exception.DeviceError` if the partition is busy or the partition is not mounted.
        """


        unmount_proc = subprocess.Popen(["umount", self.part_mask.format(self.device, partition_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = unmount_proc.communicate()
        exit_code = unmount_proc.returncode
        if exit_code != 0:
            raise weresync.exception.DeviceError(self.device, str(err, "utf-8"))
        #If there are no errors, nothing needs be returned


    def get_partition_table_type(self):
        """Gets the type of partition table on the device. Usually "gpt" for GPT disks or "msdos" for MBR disks.

        :returns: A string containing the name of the partition table.
        :raises DeviceError: If the parted command has a non-zero return code.
        :raises UnsupportedDeviceError: If the device does not have a supported partition type."""

        process = subprocess.Popen(["parted", "-s", self.device, "print"], stdout=subprocess.PIPE)
        output, error = process.communicate()
        exit_code = process.returncode
        if exit_code != 0:
            raise weresync.exception.DeviceError(self.device, "Non-zero exit code", str(error, "utf-8"))
        result = str(output, "utf-8").split("\n")
        for line in result:
            line = line.split(":")
            if line[0] == "Partition Table":
                table_type = line[1].strip()
                break

        if not table_type in SUPPORTED_PARTITION_TABLE_TYPES:
            raise weresync.exception.UnsupportedDeviceError("Partition table type {0} not supported by WereSync.".format(table_type))
        else:
            return table_type

    def get_drive_size(self):
        """Returns the maximum size of the drive, in sectors."""

        query_proc = subprocess.Popen(["blockdev", "--getsz", self.device], stdout=subprocess.PIPE)
        output, error = query_proc.communicate()
        exit_code = query_proc.returncode
        if exit_code != 0:
            raise weresync.exception.DeviceError(self.device, "Non-zero exit code", str(error, "utf-8"))

        return int(output) #should always be valid

    def get_drive_size_bytes(self):
        """Returns the maximum size of the drive, in bytes."""

        query_proc = subprocess.Popen(["blockdev", "--getsize64", self.device], stdout=subprocess.PIPE)
        output, error = query_proc.communicate()
        exit_code = query_proc.returncode
        if exit_code != 0:
            raise weresync.exception.DeviceError(self.device, "Non-zero exit code", str(error, "utf-8"))

        return int(output)

    def _get_general_info(self, partition_num):
        """Gets general information for the passed partition number, to be investigated by other methods. It returns a list with the following information in order:
        Filesystem (/dev/sda or such), Size in 512B-blocks, Used, Available, Use%, and Mounted Location.
        Gleaned from Linux df command.

        :param partition_num: the partition for which to get the information"""

        mounted_here = False
        try:
            if self.mount_point(partition_num) is None:
                self.mount_partition(partition_num, MOUNT_POINT)
                mounted_here = True

            proc_formal = subprocess.Popen(["df", "--block-size=512"], stdout=subprocess.PIPE)
            proc = subprocess.Popen(["grep", self.part_mask.format(self.device, partition_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=proc_formal.stdout)
            output, error = proc.communicate()
            exit_code = proc.returncode
            if exit_code >= 2: #grep returns 2 if an error occurs
                raise weresync.exception.DeviceError(self.device, "Error running grep.", str(error, "utf-8") + str(exit_code))
            elif exit_code == 1:
                raise weresync.exception.DeviceError(self.device, "No grep line read", None)

            return [x for x in str(output, "utf-8").split() if x != ""]
            #Ouput has the following columns: Filesystem, Total-size, Used, Available, Use%, Mount Point

        finally:
            if mounted_here:
                self.unmount_partition(partition_num)

    def get_partition_used(self, partition_num):
        """Returns the space available in a drive in 512B blocks

        :param partition_num: the number of the partition to check"""

        return int(self._get_general_info(partition_num)[2])

    def get_partition_size(self, partition_num):
        """Gets the size of a partition in 512B sectors.

        :param partition_num: An int representing the partition whose size to get.

        :returns: An int representing the number of 512B blocks in the partition
        :raises DeviceError: if the commands getting the size of the partition fail.
        :raises ValueError: if the drive has an unsupported partition table type."""
        table_type = self.get_partition_table_type()
        if table_type == "gpt":
            proc = subprocess.Popen(["sgdisk", self.device, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if proc.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error getting device information", str(error, "utf-8"))

            for line in str(output, "utf-8").split("\n"):
                if line.strip().startswith(str(partition_num)):
                    words = [x for x in line.split(" ") if x != ""]
                    return int(words[2]) - int(words[1]) #start sector is the second element in this list, last sector is third element
        elif table_type == "msdos":
            proc = subprocess.Popen(["sfdisk", "-s", self.part_mask.format(self.device, partition_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if proc.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error getting partition size for partition {0}".format(partition_num), str(error, "utf-8"))
            return int(output)
        else:
            raise ValueError("Unsupported table type")


    def get_partition_code(self, partition_num):
        """For GPT disks: gets the partition code (as defined by sgdisk) for the passed partition number.
        For MBR disks: gets the partition code (as defined by sfdisk) for the passed partition number.

        :param partition_num: the number of the partition whose code to find.
        :raises DeviceError: If the command returns a non-zero return code.
        :raises ValueError: If an invalid partition number (one that doesn't exist) is passed.
        :returns: a string containing the partition code for the appropriate disk type."""
        table_type = self.get_partition_table_type()
        if table_type == "gpt":
            proc = subprocess.Popen(["sgdisk", self.device, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if proc.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error getting device information from sgdisk", str(error, "utf-8"))
            for line in str(output, "utf-8").split("\n"):
                if line.strip().startswith(str(partition_num)):
                    words = line.strip().split()
                    return words[5] #The code appears in the fifth column, but the size takes up two columns (one for value and one for unit), so the code appears in the sixth column.
        elif table_type == "msdos":
            proc = subprocess.Popen(["fdisk", self.device, "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if proc.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error getting device partition information.", str(error, "utf-8"))

            for line in str(output, "utf-8").split("\n"):
                if line.strip().startswith(self.part_mask.format(self.device, partition_num)):
                    words = line.split()
                    loc = 4 #the code is in the 5th column
                    if "*" in line:
                        loc += 1 #if the partition is bootable, then there is an extra column before the code

                    return words[loc]

            #No partition found
            raise ValueError("Invalid partition number, no partition found.")

    def get_partition_alignment(self):
        """Returns the number of sectors the drive must be aligned to. For GPT disk this is found using sgdisk's output.
        This function is only supported by GPT disks.

        :returns: An integer that represents the partition alignment of the device.
        :raises DeviceError: If the command returns a non-zero return code"""

        table_type = self.get_partition_table_type()
        if table_type == "gpt":
            process = subprocess.Popen(["sgdisk", self.device, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if process.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error finding partition alignment.", str(error, "utf-8"))
            words = [x for x in str(output, "utf-8").split("\n") if x != ""]
            for word in words:
                if word.startswith("Partitions will be aligned on"):
                    result = word.split("Partitions will be aligned on ")
                    #the first value of result will be "", the second value will be
                    #"{alignmentNum}-sector boundaries"
                    value = result[1].split("-")
                    return int(value[0])

            raise weresync.exception.DeviceError(self.device, "sgdisk returned abnormal output.")
        elif table_type == "msdos":
            process = subprocess.Popen(["fdisk", self.device, "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if process.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error getting partition alignment", str(error, "utf-8"))
            for line in str(output, "utf-8").split("\n"):
                if line.startswith("Sector size"):
                    parts = line.split("Sector size (logical/physical): ")[1].split(" / ")
                    #After the label there is minimum and optimal size seperated by a slash
                    #Optimal is second
                    logical = int(parts[0].strip().split()[0])
                    physical = int(parts[1].strip().split()[0])
                    return int(physical / logical)

#    def get_partition_size(self, partition_num, flag):
#        """Returns the total size of a drive in 512B blocks
#
#        :partition-num the number of the partition to check."""
#        proc = subprocess.Popen(["blockdev", "--getsz", self.part_mask.format(self.device, partition_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        output, error = proc.communicate()
#        exit_code = proc.returncode
#        if exit_code != 0:
#            raise weresync.exception.DeviceError(self.part_mask.format(self.device, partition_num), "Error getting device size.", error)
#
#        return int(output) #valid results will always be a number

    def get_empty_space(self):
        """Returns the amount of empty space *after* the last partition. This does not include space hidden between partitions.

        :returns: An integer representing the number of sectors free after the last partition.
        :raises DeviceError: If the command has a non-zero return code"""
        table_type = self.get_partition_table_type()
        if table_type == "gpt":
            proc = subprocess.Popen(["sgdisk", self.device, "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if proc.returncode != 0:
                raise weresync.exception.DeviceError(self.device, "Error getting device information.", str(error, "utf-8"))
            result = str(output, "utf-8").split("\n")
            total_sectors = 0
            for line in result:
                if line.startswith("Disk " + self.device):
                    words = line.split(" ")
                    for word in words:
                        try:
                            total_sectors = int(word)
                            break
                        except ValueError:
                            continue

            last_part_info = [x for x in result[-2].split(" ") if x != ""] #the information for the last partition is always the last line in the output. The very last line, however is empty. The last real line is 2 back
            last_sector = int(last_part_info[2]) #the third column is the "end" sector column
            return total_sectors - last_sector
        elif table_type == "msdos":
            #other possible table types with throw an UnsupportedDeviceError
            #in the get_partition_table_type() method
            proc = subprocess.Popen(["fdisk", self.device, "-l"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
            output, error = proc.communicate()
            lines = str(output, "utf-8").split("\n")
            for line in lines:
                if "sectors" in line:
                    words = line.split()
                    for word in reversed(words):
                        try:
                            total_sectors = int(word)
                            break
                        except ValueError:
                            continue

                    break

            last_sector = 0
            for val in reversed(lines):
                if val.strip() == "":
                    continue
                vals = val.split()
                loc = 2
                if "*" in val:
                    loc += 1

                try:
                    value = int(vals[loc])
                except ValueError:
                    break #When this trips, we should be past all the partition descriptions
                if value >= last_sector:
                    last_sector = value

            return total_sectors - value


    def get_partition_file_system(self, part_num):
        """Returns the file system (ext4, ntfs, etc.) of the partition. If a partition system that can't be created by this system is found, None is return.

        :param part_num: the partition number whose filesystem to get.

        :returns: A string containing the file system type if a type found, otherwise None. If this is a swap partition this returns 'swap'"""
        proc = subprocess.Popen(["blkid", "-o", "value", "-s", "TYPE", self.part_mask.format(self.device, part_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = proc.communicate()
        if proc.returncode != 0 and proc.returncode != 2:
            raise weresync.exception.DeviceError(self.part_mask.format(self.device, part_num), "Error getting partition file system type.", error)
        result = str(output, "utf-8").strip()
        return result if result in SUPPORTED_FILESYSTEM_TYPES else None

    def set_partition_file_system(self, part_num, system_type):
        """Creates a new file system on the passed partition number. This is essentially the same as formatting the partition.
        If the passed partition is currently mounted, this will unmount the system, and remount it when finished.

        :param part_num: the partition number to format
        :param system_type: a file system (ex. ntfs) supported by mkfs on the current system."""
        mnt_point = self.mount_point(part_num)
        try:
            if mnt_point != None:
                self.unmount_partition(part_num)
            if system_type == "swap":
                proc = subprocess.Popen(["mkswap", self.part_mask.format(self.device, part_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                proc = subprocess.Popen(["mkfs", "-t", system_type, self.part_mask.format(self.device, part_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if proc.returncode != 0:
                raise weresync.exception.DeviceError(self.part_mask.format(self.device, part_num), "Error creating new file system on partition.", str(error, "utf-8"))
        finally:
            if mnt_point != None:
                self.mount_partition(part_num, mnt_point)

class DeviceCopier:
    """DeviceCopiers transfer data from a source drive to a target drive.

    :param source: the drive identifier (/dev/sda or such) of the source drive.
    :param target: the drive identifier (/dev/sdb or such) of the target drive."""

    def __init__(self, source, target):
        """:source the drive identifier (/dev/sda or such) of the source drive
        :target the drive identifier (/dev/sdb or such) of the target drive
        """
        self.source = source if isinstance(source, DeviceManager) else DeviceManager(source)
        self.target = target if isinstance(target, DeviceManager) else DeviceManager(target)

    def _transfer_gpt(self, difference):
        """Transfers the gpt partition table from the larger source drive to the smaller target drive.

        This method is not intended to be called from any method but the transfer partition table method below.

        :param difference: the difference between the sizes of the two drives
        :param margin: the amount of margin to give shrunk partitions."""
        partitions = self.source.get_partitions()
        part_alignment = self.target.get_partition_alignment()
        add_args = []
        type_args = []
        difference -= (self.source.get_empty_space() - 34) #the empty space in the source does not count against the difference, but we leave the margin just in case
        #It also seems that gpt disks at least have 34 unusable sectors at the end of the empty space, so we remove those from the count
        for i in reversed(partitions):
            drive_size = self.source.get_partition_size(i)
            try:
                part_used = self.source.get_partition_used(i)
            except weresync.exception.DeviceError:
                part_used = drive_size
            space = int(part_alignment * math.floor((drive_size - part_used) / part_alignment))
            if space > 0 and difference > 0:
                part_size = None
                #if the amount of space on the drive is bigger than the difference between the drives
                if space > difference:
                    part_size = int(part_alignment * math.ceil((drive_size - difference) / part_alignment))
                    difference = 0
                else:
                    part_size = int(part_alignment * math.ceil(part_used / part_alignment))
                    difference -= space
            else:
                part_size = int(part_alignment * math.ceil(drive_size / part_alignment))
                difference += part_size - drive_size #this adds or subtracts to the difference based on whether or the aligning changed the size of the partition
            if (i != partitions[-1]):
                #delete_args += ["-d", str(i)]
                add_args = ["-n", "{0}:0:+{1}".format(i, part_size)] + add_args#part_size is in 512 byte chunks, but gdisk expects a 1 kB based unit if should_break: break
                #this also rounds down, in order to leave more space rather than less
            else: #if this is the last partition to be looped, let it occupy maximum space.
                add_args = ["-n", "{0}:0:0".format(i)] + add_args

            type_args += ["-t", "{0}:{1}".format(i, self.source.get_partition_code(i))]

        LOGGER.debug(["sgdisk", self.target.device, "-o"] + add_args + type_args)
        copy_process = subprocess.Popen(["sgdisk", self.target.device, "-o"] + add_args + type_args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        copy_out, copy_err = copy_process.communicate()
        if copy_process.returncode != 0:
            raise weresync.exception.DeviceError(self.target.device, "Error copying partition table to target.", str(copy_err, "utf-8"))

        final_proc = subprocess.Popen(["sgdisk", self.target.device, "-G"], stderr=subprocess.PIPE)
        final_out, final_err = final_proc.communicate()
        if final_proc.returncode != 0:
            raise weresync.exception.DeviceError(self.target.device, "Error randomizing GUIDs on target device", str(final_err, "utf-8"))


    def _transfer_msdos(self, difference, margin=5):
        """Copies the partition table from a msdos source drive to a target drive.
        :param margin: The percent of original size to leave as a margin in the size of each partition. Is ignored if partition size is 0."""
        for i in self.target.get_partitions():
            if self.target.mount_point(i) != None:
                self.target.unmount_partition(i)
        current_proc = subprocess.Popen(["sfdisk", "-d", self.source.device], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        partition_table, current_proc_error = current_proc.communicate()
        if current_proc.returncode != 0:
            raise weresync.exception.DeviceError(self.source.device, "Error getting partition table backup.", str(current_proc_errror, "utf-8"))
        partition_table = str(partition_table, "utf-8")
        partition_listings = [x.replace(" ", "") for x in partition_table.split("\n") if x.startswith(self.source.part_mask.format(self.source.device, ""))]
        count = 0
        for idx, val in enumerate(partition_listings):
            #Standard line of sfdisk -d output:
            #mbr.img1:start=2050,size=1893,Id=83, bootable
            #a new version would have "type" instead of "Id"
            listing = val.split(":")
            pairs = {"part" : int(parse.parse(self.source.part_mask.format
                                          (self.source.device, "{0}"),
                                          listing[0])[0])}
            for i in listing[1].split(","):
                pair = i.split("=")
                if len(pair) != 2:
                    pairs["bootable"] = True
                else:
                    pairs["bootable"] = False
                    if (pair[0] == "Id" or pair[0] == "type"):
                        #Newer versions of sfdisk use type instead of Id
                        #This test allows both versions to be supported
                        pairs["type"] = pair[1]
                        id_key = pair[0] #needed to create the right lines in the final product
                    else:
                        pairs[pair[0]] = int(pair[1])
            partition_listings[idx] = pairs

        partition_listings.sort(key=lambda x: x["start"])
        move_start_back_by = 0
        final_str = "unit: sectors\n\n"
        current_extended_partition = None
        extended_part_text = ""

        for i in partition_listings:
            i["start"] -= move_start_back_by
            if current_extended_partition != None and i["part"] <= 4: #Not a logical partition
                current_extended_partition = None

            if i["type"] == "5": #The partition is an extended partition
                current_extended_partition = i
                continue
            shrink = 0
            try:
                part_num = i["part"]
                drive_used = self.source.get_partition_used(part_num)
                space = math.floor((i["size"] - drive_used) * (1 - margin/100))
                if space > 0 and difference > 0:
                    if space >= difference:
                        shrink = difference
                    else:
                        shrink = space
                        difference -= shrink

                    move_start_back_by += shrink
                    i["size"] -= shrink
            except weresync.exception.DeviceError as ex:
                LOGGER.warning("Error reading device.")
                LOGGER.debug("Execption info:", exc_info=sys.exc_info())

            if current_extended_partition != None:
                current_extended_partition["size"] -= shrink

        partition_listings.sort(key=lambda x: x["part"])
        #We don't know what the name of the id key is, so we have to concaterate it in.
        final_str = "unit: sectors\n\n" + "".join(["{val} : start= {start}, size= {size}, {type_key}= {type}{boot}\n".format(
                val=self.target.part_mask.format(self.target.device, part_line["part"]),
                boot=", bootable" if part_line["bootable"] else "",
                type_key=id_key,
                **part_line) for part_line in partition_listings])

        LOGGER.debug("Proposed partition table:\n" + final_str)

        table_proc = subprocess.Popen(["fdisk", self.target.device], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, universal_newlines=True)
        output, error = table_proc.communicate(input="o\nw\nq")
        if table_proc.returncode != 0:
            raise weresync.exception.CopyError("Could not create new partition table on target device", output)
        transfer_proc = subprocess.Popen(["sfdisk", "--force", self.target.device], stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)
        output, error = transfer_proc.communicate(input=final_str)
        if transfer_proc.returncode != 0:
            raise weresync.exception.CopyError("Could not copy partition table to target device.", error)

    def format_partitions(self, ignore_errors=True, callback=None):
        """Goes through each partition in the source drive and formats the corresponding partition in the target drive to the same thing.

        :param ignore_errrors: whether or not errors (such as a file-system not recongized by mkfs) should be ignored. If True such errors will be logged. If false the exceptions will be propogated. Defaults to True.
        :param callback: If not None, this function should be a function that accepts a float between 0 and 1 to update the progress."""
        partitions = self.source.get_partitions()
        for i in partitions:
            try:
                part_type = self.source.get_partition_file_system(i)
                if callback != None:
                    drive_size = self.target.get_drive_size()
                    complete = 0.0
                if part_type != None:
                    self.target.set_partition_file_system(i, part_type)
                    if callback != None:
                        part_size = self.target.get_partition_size(i)
                        complete += part_size / drive_size
                        LOGGER.debug("Callback:\nDrive Size: {0}\n"
                                     "Part Size: {1}\n"
                                     "Complete: {2}".format(
                                         drive_size, part_size, complete))
                        callback(complete)
                else:
                    LOGGER.warning("Invalid filesystem type found. Partition {0} not formatted.".format(i))
            except weresync.exception.DeviceError as exe:
                if ignore_errors:
                    logging.getLogger("weresync.device").warning("Creating filesystem for {0} encountered errors. Partition type: {1}. Skipped.".format(self.target.part_mask.format(self.target.device, i), part_type), exc_info=sys.exc_info())
                    logging.getLogger("weresync.device").debug("Error making file system.", exc_info=sys.exc_info())
                else:
                    raise exe

    def transfer_partition_table(self, resize=True, callback=None):
        """Transfers the partition table from one drive to another. Afterwards, it formats the partitions on the target drive to be the same as those on the source drive.

        :param resize: if true (default) then the program will attempt to resize the partition tables to fit on a smaller drive. This will not expand partition tables at any time.
        :param callback: If not none, a function to update progress completed. See py:func:`~.format_partitions()`"""


        source_size = self.source.get_drive_size()
        target_size = self.target.get_drive_size()

        source_type = self.source.get_partition_table_type()
        if target_size < source_size and not resize:
                raise weresync.exception.CopyError("Target device smaller than source device and resize set to false.")
        elif source_type == "gpt":
            self._transfer_gpt(source_size - target_size)
        elif source_type == "msdos":
            self._transfer_msdos(source_size - target_size)

        for i in self.target.get_partitions():
            if self.target.mount_point(i) != None:
                self.target.unmount_partition(i)

        if callback != None:
            callback(0.3)

        #the block devices still won't be updated unless the following command is called.
        proc = subprocess.Popen(["partprobe", self.target.device], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        output, error = proc.communicate()
        if proc.returncode != 0:
            raise weresync.exception.DeviceError(self.target.device, "Error reloading partition mappings.", str(error, "utf-8"))

        #This weights the progress so 30% comes from creating partition and 70% from formatting.
        self.format_partitions(callback=lambda prog: callback(0.3 + prog * 0.7) if callback != None else None)
        #If it's done, it's done
        if callback != None:
            callback(1.0)

    def partitions_valid(self):
        """Tests if the partitions on the target drive can support copying files from the source drive.

        :returns: True if no errors found.
        :raises: a :py:class:`~weresync.exception.CopyError` if any part invalid."""
        source_parts = self.source.get_partitions()
        target_parts = self.target.get_partitions()
        if source_parts != target_parts:
            raise weresync.exception.CopyError("Partition count on two drives different. Invalid.")
        for i in source_parts:
            if self.source.get_partition_file_system(i) != self.target.get_partition_file_system(i):
                raise weresync.exception.CopyError("File system type for partition {0} does not match. Invalid.".format(i))
            try:
                if self.source.get_partition_used(i) > self.target.get_partition_size(i):
                    raise weresync.exception.CopyError("Information on partition {0} cannot fit on corresponding partition on target drive.".format(i))
            except weresync.exception.DeviceError as ex:
                if "mount" in str(ex) or "swapspace" in str(ex): #the partition couldn't be mounted because it isn't a mountable partition (maybe boot sector or swap)
                    LOGGER.debug("Partition {0} couldn't be mounted. Bad FS type".format(i), exc_info=sys.exc_info)
                else:
                    raise ex

        return True

    def _copy_fstab(self, mnt_source, mnt_target, excluded_partitions=[]):
        """Updates files in /etc/fstab to be bootable on the target drive.
        :param mnt_source: the directory where source partitions should be mounted.
        :param mnt_target: the directory where target partitions should be mounted.
        :param excluded_partitions: partitions not to search. Defaults to empty"""
        for i in self.source.get_partitions():
            source_mounted = False
            target_mounted = False
            try:
                if not i in excluded_partitions:
                    source_loc = self.source.mount_point(i)
                    if source_loc == None:
                        try:
                            self.source.mount_partition(i, mnt_source)
                            source_mounted = True
                            source_loc = mnt_source
                        except weresync.exception.DeviceError as ex:
                            if "mount" in str(ex):
                                LOGGER.debug("Failed to mount partition. Info:\n", exc_info=sys.exc_info())
                                continue
                            else:
                                raise ex
                    source_fstab_path = source_loc + ("/" if not source_loc.endswith("/") else "") + "etc/fstab"
                    if os.path.exists(source_fstab_path):
                        target_loc = self.target.mount_point(i)
                        if target_loc == None:
                            self.target.mount_partition(i, mnt_target)
                            target_mounted = True
                            target_loc = mnt_target
                        with open(source_fstab_path) as source_fstab, open(target_loc + ("/" if not target_loc.endswith("/") else "") + "etc/fstab", "w") as target_fstab:
                            target_fstab.write("#This file is generated by WereSync. All comments have been copied, but they have not been parsed.\n#Any reference to identifiers during installation may be inaccurate.\n\n")
                            for line in source_fstab.readlines():
                                stripLine = line.strip()
                                if stripLine == "" or stripLine.startswith("#"):
                                    target_fstab.write(line)
                                    continue

                                words = stripLine.split()

                                if words[0].startswith("UUID") or words[0].startswith("LABEL"):

                                    if words[0].startswith("UUID"):
                                        blkid_arg = "-U"
                                    elif words[0].startswith("LABEL"):
                                        blkid_arg = "-L"

                                    identifier = words[0].split("=")[1] #First argument of the space separated list is the identifier,
                                    #which is split by a equals sign, and the second value is the identifier
                                    proc = subprocess.Popen(["blkid", blkid_arg, identifier], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    output, error = proc.communicate()
                                    if proc.returncode == 2:
                                        raise weresync.exception.DeviceError(self.soruce.device, "Could not find block name of device with id: {0}".format(identifier), str(error, "utf-8"))
                                    elif proc.returncode != 0:
                                        raise weresync.exception.DeviceError(self.source.device, "Error finding device error for device with id: {0}".format(identifer), str(error, "utf-8"))
                                    #It figures out the value of a placeholder based on context. However, the part_masks rarely have enough context
                                    #So we format the part_mask so that the first placeholder is the partition number, and the device name is inserted
                                    #(comes out to something like "/dev/nbd0p{0}"). Then it can figure it out.
                                    result = parse.parse(self.source.part_mask.format(self.source.device, "{0}"), str(output, "utf-8"))[0] #the first element contains the number
                                    uuid_proc = subprocess.Popen(["blkid", self.source.part_mask.format(self.target.device, result)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    uuid_output, uuid_error = uuid_proc.communicate()
                                    if uuid_proc.returncode == 2:
                                        raise weresync.exception.DeviceError(self.target.device,
                                                                             "Could not find device {0}".format(self.target.part_mask.format(self.target.device, result)),
                                                                             str(uuid_error, "utf-8"))
                                    elif uuid_proc.returncode != 0:
                                        raise weresync.exception.DeviceError(self.target.device, "Error finding uuid for device {0}".format(
                                            self.target.part_mask.fomrat(self.target.device, result)),
                                                                             str(uuid_error, "utf-8"))
                                    ids = str(uuid_output, "utf-8").split()
                                    for val in ids:
                                        if val.startswith("UUID"):
                                            words[0] = val.replace('"', '') #Have to remove the double quotes from blkid's output.
                                            break
                                    target_fstab.write(" ".join(words) + "\n")
            finally:
                if source_mounted:
                    self.source.unmount_partition(i)
                if target_mounted:
                    self.source.unmount_partition(i)

    def copy_files(self, mnt_source, mnt_target, excluded_partitions=[], ignore_failures=True, rsync_args=DEFAULT_RSYNC_ARGS, callback=None):
        """Copies all files from source to target drive, doing one partition at a time. This assumes that the two drives have equivalent partition mappings, i.e. that the data on partition 1 of the source drive should be on partition 1 of the target drive.

        :param mnt_source: The directory to mount partitions from the source drive on.
        :param mnt_target: The directory to mount partitions from the target drive on.
        :param excluded_partitions: A list containing the partitions to not copy. Defaults to empty.
        :param ignore_failures: If True, errors encountered for a partition will not cause the function to exit, but we instead cause a warning to be logged. Defaults to true.
        :param callaback: If not None, a function with the signature ``callback(int, float)``, where the int represents partition number and float represents progress. If an error occurs, the float will be negative. If the float should pulse, it wil return True."""

        for i in self.source.get_partitions():
            source_mounted = False
            target_mounted = False
            try:

                if i in excluded_partitions:
                    continue

                source_loc = self.source.mount_point(i)
                if source_loc == None:
                    self.source.mount_partition(i, mnt_source)
                    source_mounted = True
                    source_loc = mnt_source
                target_loc = self.target.mount_point(i)
                if target_loc == None:
                    self.target.mount_partition(i, mnt_target)
                    target_mounted = True
                    target_loc = mnt_target

                LOGGER.info("Starting rsync process for partition {0}.".format(self.source.device))
#['--exclude="' + x + '"' for x in ["/dev/*", "/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found"]]
                command_args = ["rsync"] + shlex.split(rsync_args) + ['--exclude=' + x + '' for x in ["/dev/*", "/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found", "/home/*/.gvfs"]] + [source_loc + ("/" if not source_loc.endswith("/") else ""), target_loc]
                if callback != None:
                    command_args += ["--info=progress2"]
                print("Copying partition " + str(i))
                LOGGER.debug("Arguments = " + " ".join(command_args))
                def run_proc():
                   with subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                       buf = bytearray()
                       while True:
                           byt = proc.stdout.read(1);
                           if byt == b"":
                               break
                           elif byt == b"\r":
                               yield buf.decode()
                               buf = bytearray()
                           else:
                               buf += byt

                       LOGGER.debug("Errors for partition {0}:\n".format(i) + proc.stderr.read().decode())
                if callback != None:
                    for val in run_proc():
                        vals = val.split()
                        if len(vals) >= 2 and vals[1].endswith("%"):
                            try:
                                #chk = vals[5].split("=")
                                #counts = chk[1].split("/")
                                #if chk[0].strip() == "to-chk" and counts[0].strip() == "0":
                                #    float_val = True
                                #else:
                                float_val = float(vals[1].strip("%")) / 100
                            except ValueError:
                                continue
                            callback(i, float_val)

                    LOGGER.debug("Setting to finished")
                    callback(i, 1.0)
                else:
                    for val in run_proc():
                        #If you don't loop through the generator values, the rsync process doesn't run properly.
                        pass

            except weresync.exception.DeviceError as exe:
                if ignore_failures:
                    LOGGER.warning("Error copying data for partition {0} from device {1} to {2}.".format(i, self.source.device, self.target.device))
                    LOGGER.debug("Error info.", exc_info=sys.exc_info())
                    if callback != None:
                        callback(i, -1.0)
                else:
                    raise exe
            finally:
                if source_mounted:
                    self.source.unmount_partition(i)
                if target_mounted:
                    self.target.unmount_partition(i)
        print("Finished copying files.")

    def _install_grub(self, target_mnt, grub_partition=None, boot_partition=None, efi_partition=None):
        """Installs grub on the target drive so it will boot properly, and not rely on the same UUIDs as the source drive.

        This function will pick the first partition with a "boot" folder in the root space to be the partition to install grub on.
        :param target_mnt: location to mount target file while searching for and installing grub. Can be None is grub_partition is assigned.
        :param grub_partition: If not None, then it should be a int containing the partition number where grub should be installed. Defaults to None.
        :param boot_partition: The partition that should be mounted on /boot. If None no partition is mounted.
        :param efi_partition: The partition that should be mounted on /boot/efi. If None no partition mounted."""
        if grub_partition == None:
                for i in self.target.get_partitions():
                    try:
                        mount_point = self.target.mount_point(i)
                        if mount_point == None:
                            self.target.mount_partition(i, target_mnt)
                            mount_point = target_mnt
                        if os.path.exists(mount_point + ("/" if not mount_point.endswith("/") else "") + "boot/grub"):
                            grub_partition = i
                            break
                        else:
                            self.target.unmount_partition(i)
                    except weresync.exception.DeviceError as ex:
                        LOGGER.warning("Could not mount partition {0}. Assumed to not be the partition grub is on.".format(i))
                        LOGGER.debug("Error info:\n", exc_info=sys.exc_info())
                else: #No partition found
                    raise weresync.exception.CopyError("Could not find partition with 'boot/grub' folder on device {0}".format(self.target.device))

        mounted_here = False
        boot_mounted_here = False
        efi_mounted_here = False
        bound_dirs = ["dev", "proc", "sys", "dev/pts"]
        try:
            mount_loc = self.target.mount_point(grub_partition)
            if mount_loc == None:
                self.target.mount_partition(grub_partition, target_mnt)
                mounted_here = True
                mount_loc = target_mnt

            mount_loc += "/" if not mount_loc.endswith("/") else ""

            if boot_partition != None:
                self.target.mount_partition(boot_partition, mount_loc + "boot")
                boot_mounted_here = True

            if efi_partition != None:
                os.makedirs(mount_loc + "boot/efi", exist_ok=True)
                self.target.mount_partition(efi_partition, mount_loc + "boot/efi")
                efi_mounted_here = True

            for val in bound_dirs:
                proc = subprocess.Popen(["mount", "--bind", "/" + val, mount_loc + val], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, error = proc.communicate()
                if proc.returncode != 0:
                    raise weresync.exception.DeviceError(self.target.device, "Error mounting special partition {0}".format(val), str(error, "utf-8"))

            real_root = os.open("/", os.O_RDONLY)
            try:
                print("Updating Grub")
                os.chroot(mount_loc)
                grub_update = subprocess.Popen(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                update_output, update_error = grub_update.communicate()
                if grub_update.returncode != 0:
                    raise weresync.exception.DeviceError(self.target.device, "Error updating grub configuration", str(update_error, "utf-8"))

                print("Installing Grub")
                grub_command = ["grub-install", "--recheck", self.target.device]
                if efi_partition != None:
                    grub_command += ["--efi-directory=/boot/efi", "--target=x86_64-efi", "--bootloader-id=grub"]
                else:
                    grub_command += ["--target=i386-pc"]
                LOGGER.debug("Grub command: " + " ".join(grub_command))

                grub_install = subprocess.Popen(grub_command,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                install_output, install_error = grub_install.communicate()
                if grub_install.returncode != 0:
                    raise weresync.exception.DeviceError(self.target.device, "Error installing grub.", str(install_error, "utf-8"))

                print("Cleaning up.")
            finally:
                os.fchdir(real_root)
                os.chroot(".")
                os.close(real_root)
        finally:
            for val in reversed(bound_dirs): #this way if bound_dirs are mounted within each other, they will be unmounted in the proper order.
                subprocess.call(["umount", mount_loc + val])
            if efi_mounted_here:
                self.target.unmount_partition(efi_partition)
            if boot_mounted_here:
                self.target.unmount_partition(boot_partition)
            if mounted_here:
                self.target.unmount_partition(grub_partition)
        print("Finished!")

    def make_bootable(self, source_mnt, target_mnt, excluded_partitions=[], grub_partition=None, boot_partition=None, efi_partition=None, callback=None):
        """Updates the fstab and installs the grub boot loader on a drive so it is bootable.

        :param source_mnt: the directory to mount partitions from the source drive on.
        :param target_mnt: the directory to mount partitions from the target drive on.
        :param excluded_partitions: a list of integers which should not be searched while looking for fstab files or boot directories.
        :param grub_partition: the partition to install grub on. WereSync will attempt to find the right partition if this is None.
        :param boot_partition: If not None, this is an int representing the partition that should be mounted on /boot.
        :param efi_partition: If not None this is an int representing the partition that should be mounted on /boot/efi
        :param callback: A function that expects a boolean indicating whether or not the bootloader process has completed."""
        if callback != None:
            callback(False)
        try:
            self._copy_fstab(source_mnt, target_mnt, excluded_partitions)
        except weresync.exception.DeviceError as ex:
            LOGGER.warning("Error copying fstab. Continuing anyway.")
            LOGGER.debug("", exc_info=sys.exc_info())

        self._install_grub(target_mnt, grub_partition, boot_partition, efi_partition)

        if callback != None:
            callback(True)
