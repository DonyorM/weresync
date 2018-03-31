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

# flake8: noqa

import sys
import os

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + "/../src/")

import pytest
import unittest.mock as mock
import weresync.device as device
from weresync.exception import DeviceError, UnsupportedDeviceError


def generateStandardMock(monkeypatch,
                         return_value_output,
                         return_value_error,
                         return_code,
                         type="gpt"):
    """Generates a mock for the Popen class that allows easy testing of device methods that use Popen."""
    mock_popen = mock.MagicMock()
    if return_value_error != None:
        return_value_output += return_value_error  # Simulates combining the stdout and stderr
    mock_popen.communicate.return_value = (return_value_output, None)
    mock_popen.returncode = return_code

    def popen_constructor(*args, **kargs):
        return mock_popen

    def mock_table_type(*args, **kargs):
        return type

    monkeypatch.setattr("subprocess.Popen", popen_constructor)
    if type != None:
        monkeypatch.setattr(
            "weresync.device.DeviceManager.get_partition_table_type",
            mock_table_type)


def test_get_partitions_valid(monkeypatch):
    generateStandardMock(monkeypatch, b"""Model: Unknown (unknown)
Disk /dev/nbd0: 8590MB
Sector size (logical/physical): 512B/512B
Partition Table: gpt

Number  Start   End     Size    File system     Name  Flags
 4      1049kB  500MB   499MB                         bios_grub
 1      500MB   6000MB  5500MB  ext4
 2      6000MB  7400MB  1400MB  ext4
 3      7400MB  8589MB  1189MB  linux-swap(v1)\n """, None,
                         0)  # standard return from sgdisk -p
    manager = device.DeviceManager("/dev/sdd")
    result = manager.get_partitions()
    assert result == [4, 1, 2, 3]


def test_get_partitions_none_zero_returncode(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partitions()

    assert "Error." in str(execinfo.value)


def test_get_partitions_no_partitions(monkeypatch):
    generateStandardMock(monkeypatch, b"Nope\nvery\nvery\nbad\ndata", None, 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_partitions()
    assert result == []


def test_mount_point_normal(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""TARGET      SOURCE     FSTYPE  OPTIONS
/mnt /dev/sda11 fuseblk rw,nosuid,nodev,relatime,user_id=0,group_id=0,def
""", None, 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.mount_point(3)
    assert "/mnt" == result


def test_mount_point_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""TARGET      SOURCE     FSTYPE  OPTIONS\n
/mnt /dev/sda11 fuseblk rw,nosuid,nodev,relatime,user_id=0,group_id=0,def\n
""", b"Error.", 2)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        result = manager.mount_point(5)

    assert "Error." in str(execinfo.value)


def test_mount_point_no_mount_point(monkeypatch):
    generateStandardMock(monkeypatch, b"", None,
                         1)  # findmnt returns 1 when there is no mount point
    manager = device.DeviceManager("/dev/sda")
    result = manager.mount_point(5)
    assert result == None


def test_mount_partition(monkeypatch):
    generateStandardMock(monkeypatch, b"", None, 0)
    manager = device.DeviceManager("/dev/sda")
    manager.mount_partition(3, "/mnt")


def test_mount_partition_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.mount_partition(3, "/mnt")

    assert "Error." in str(execinfo.value)


def test_unmount_partition(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    manager.unmount_partition(5)


def test_unmount_partition_non_zero(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.unmount_partition(5)

    assert "Error." in str(execinfo.value)


def test_get_partition_table_type_gpt(monkeypatch):
    generateStandardMock(monkeypatch, b"""/dev/sda: gpt partitions 1 2 3 4 5 11 8 9 10 6 7""", b"", 0, None)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_partition_table_type()
    assert "gpt" == result

def test_get_partition_table_type_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1, None)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_table_type()

    assert "Error." in str(execinfo.value)

def test_get_partition_table_type_mbr(monkeypatch):
    generateStandardMock(monkeypatch, b"""/dev/sda: msdos partitions 1 2 3 4 5 11 8 9 10 6 7""", b"", 0, None)
    manager = device.DeviceManager("mbr.img")
    result = manager.get_partition_table_type()

    assert result == "msdos"

def test_get_partition_table_type_unsupported(monkeypatch):
    generateStandardMock(monkeypatch, b""" dddd   """, b"", 0, None)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(UnsupportedDeviceError) as execinfo:
        manager.get_partition_table_type()

    assert "Partition table type of /dev/sda not supported" in str(execinfo)


def test_get_drive_size(monkeypatch):
    generateStandardMock(monkeypatch, b"192", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_drive_size()
    assert 192 == result


def test_get_drive_size_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_drive_size()

    assert "Error." in str(execinfo.value)


def test_get_drive_size_bytes(monkeypatch):
    generateStandardMock(monkeypatch, b"190", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_drive_size_bytes()

    assert 190 == result


def test_get_drive_size_bytes_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_drive_size()

    assert "Error." in str(execinfo.value)


def test_get_partition_used(monkeypatch):
    generateStandardMock(
        monkeypatch,
        b"/dev/sda11     676276220 179697120 496579100  27% /media/Data", b"",
        0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_partition_used(5)
    assert 179697120 == result


def test_get_partition_used_non_zero_return(monkeypatch):
    generateStandardMock(monkeypatch, b"  ", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_used(4)

    assert "Error." in str(execinfo.value)


def test_get_drive_empty_space(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk gpt.img: 1024000 sectors, 500.0 MiB
Logical sector size: 512 bytes
Disk identifier (GUID): 6FCE9962-D7B0-4BF3-B7BC-5E5CE8A5B0B0
Partition table holds up to 128 entries
First usable sector is 34, last usable sector is 1023966
Partitions will be aligned on 2-sector boundaries
Total free space is 647 sectors (323.5 KiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1              34           97656   47.7 MiB    8300  test
   2           98304          145407   23.0 MiB    8300  cool
   3          145408          391167   120.0 MiB   8300  nice
   4          391168          684031   143.0 MiB   8300  great
   5          684032          976895   143.0 MiB   8300  sweet
   6          976896         1023966   23.0 MiB    8300
                      """, b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_empty_space()
    assert result == 34


def test_get_empty_space_non_zero_return(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 2)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_empty_space()

    assert "Error." in str(execinfo.value)


def test_get_empty_space_mbr(monkeypatch):
    generateStandardMock(monkeypatch, b"""Disk mbr.img: 524 MB, 524288000 bytes
63 heads, 37 sectors/track, 439 cylinders, total 1024000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xd9e3a78c

  Device Boot      Start         End      Blocks   Id  System
mbr.img1            2050        3942         946+  83  Linux
    """, b"", 0, "msdos")
    manager = device.DeviceManager("mbr.img")
    result = manager.get_empty_space()
    assert result == 1020058


def test_get_empty_space_mbr_boot(monkeypatch):
    generateStandardMock(monkeypatch, b"""Disk mbr.img: 524 MB, 524288000 bytes
63 heads, 37 sectors/track, 439 cylinders, total 1024000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xd9e3a78c

  Device Boot      Start         End      Blocks   Id  System
mbr.img1            2050        3942         946+  83  Linux
 Disk mbr.img: 524 MB, 524288000 bytes
255 heads, 63 sectors/track, 63 cylinders, total 1024000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xd9e3a78c

  Device Boot      Start         End      Blocks   Id  System
mbr.img1            2050        3942         946+  83  Linux
mbr.img2            2048        2049           1   83  Linux
mbr.img3            3943      255846      125952    5  Extended
mbr.img5            5991      104244       49127   83  Linux
mbr.img6 *        106293      255846       74777   83  Linux
   """, b"", 0, "msdos")
    manager = device.DeviceManager("mbr.img")
    result = manager.get_empty_space()


def test_get_partition_size(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/loop0: 1024000 sectors, 500.0 MiB
Logical sector size: 512 bytes
Disk identifier (GUID): 4EB07926-DFE2-4D18-A2F4-75FB23616F71
Partition table holds up to 128 entries
First usable sector is 34, last usable sector is 1023966
Partitions will be aligned on 2048-sector boundaries
Total free space is 2014 sectors (1007.0 KiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048          309247   150.0 MiB   8300  Linux filesystem
   2          309248          821247   250.0 MiB   8300  Linux filesystem
   3          821248          972799   74.0 MiB    8300  Linux filesystem
   4          972800         1019903   23.0 MiB    8300  Linux filesystem
   5         1019904         1023966   2.0 MiB     8300  Linux filesystem
""", None, 0)
    monkeypatch.setattr(
        "weresync.device.DeviceManager.get_partition_table_type",
        lambda x: "gpt")
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_size(5)
    assert 4062 == result


def test_get_partition_size_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 2)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_size(1)

    assert "Error." in str(execinfo)


def test_get_partition_size_mbr_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 2, "msdos")
    manager = device.DeviceManager("mbr.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_size(3)

    assert "Error." in str(execinfo)


def test_get_partition_size_mbr(monkeypatch):
    generateStandardMock(monkeypatch, b"204800", b"", 0, "msdos")
    manager = device.DeviceManager("mbr.img")
    result = manager.get_partition_size(4)
    assert result == 204800


def test_get_partition_size_unknown_table_type(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"", 0, "blah")
    manager = device.DeviceManager("blah.img")
    with pytest.raises(ValueError) as execinfo:
        manager.get_partition_size(5)

    assert "Unsupported" in str(execinfo)


def test_get_sector_alignment_number(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/loop1: 512000 sectors, 250.0 MiB
Logical sector size: 512 bytes
Disk identifier (GUID): 4EB07926-DFE2-4D18-A2F4-75FB23616F71
Partition table holds up to 128 entries
First usable sector is 34, last usable sector is 511966
Partitions will be aligned on 2048-sector boundaries
Total free space is 5558 sectors (2.7 MiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048          309247   150.0 MiB   8300  Linux filesystem
   2          309248          508422   97.3 MiB    8300  Linux filesystem
                      """, b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_alignment()
    assert result == 2048


def test_get_sector_alignment_number_non_zero_return(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        result = manager.get_partition_alignment()

    assert "Error." in str(execinfo.value)


def test_get_sector_alignment_number_invalid_return(monkeypatch):
    generateStandardMock(monkeypatch, b"No alignment", b"", 0)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        result = manager.get_partition_alignment()


def test_get_partition_alignment_msdos(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/loop0: 7516 MB, 7516192768 bytes
255 heads, 63 sectors/track, 913 cylinders, total 14680064 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x524f0bf8

      Device Boot      Start         End      Blocks   Id  System
    """, b"", 0, "msdos")
    manager = device.DeviceManager("msdos.img")
    result = manager.get_partition_alignment()
    # Basically, this is testing if the physical partition is different then the logical partition. If so, then sectors will need to be aligned properly. That isn't the case here.
    assert result == 1


def test_get_partition_alignment_msdos_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error msdos", 1, "msdos")
    manager = device.DeviceManager("msdos.img")
    with pytest.raises(DeviceError) as exceinfo:
        result = manager.get_partition_alignment()


def test_get_partition_file_system(monkeypatch):
    generateStandardMock(monkeypatch, b"ext4", b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_file_system(4)
    assert result == "ext4"


def test_get_partition_file_system_empty_return(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_file_system(4)
    assert result == None


def test_get_partition_file_system_unsupported_type(monkeypatch):
    generateStandardMock(monkeypatch, b"completelyimpossiblefilesystemtype",
                         b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_file_system(4)
    assert result == None


def test_get_partition_file_system_non_zero_return(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_file_system(3)

    assert "Error." in str(execinfo.value)


def test_set_partition_file_system_non_zero_return(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.set_partition_file_system(3, "ext4")

    assert "new file system" in str(execinfo.value)
    assert "Error." in str(execinfo.value)


def test_partition_code(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/nbd0: 16777216 sectors, 8.0 GiB
Logical sector size: 512 bytes
Disk identifier (GUID): 13E1C95B-5AC6-412B-930B-8F119760B86E
Partition table holds up to 128 entries
First usable sector is 34, last usable sector is 16777182
Partitions will be aligned on 2048-sector boundaries
Total free space is 4029 sectors (2.0 MiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1          976896        11718655   5.1 GiB     8300
   2        11718656        14452735   1.3 GiB     8300
   3        14452736        16775167   1.1 GiB     8200
   4            2048          976895   476.0 MiB   EF02
                      """, b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_code(3)
    assert "8200" == result


def test_get_partition_code_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Error.", 2, "gpt")
    with pytest.raises(DeviceError) as execinfo:
        manager = device.DeviceManager("gpt.img")
        manager.get_partition_code(3)

    assert "Error." in str(execinfo)

def test_get_partition_code_newer_format(monkeypatch):
    generateStandardMock(monkeypatch, b"""Disk /dev/sdb: 5 GiB, 5368709120 bytes, 10485760 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x0ee18f9a

Device     Boot  Start      End  Sectors  Size Id Type
/dev/sdb1  *      2048   350300   348253  170M 83 Linux
/dev/sdb2       352347 10485759 10133413  4,9G  5 Extended
/dev/sdb5       352349 10485759 10133411  4,9G 8e Linux LVM""",
                         b"", 0, "msdos")
    manager = device.DeviceManager("/dev/sdb")
    result = manager.get_partition_code(5)
    assert "8e" == result

def test_get_partition_code_mbr(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/loop0: 524 MB, 524288000 bytes
255 heads, 63 sectors/track, 63 cylinders, total 1024000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x01517e72

      Device Boot      Start         End      Blocks   Id  System
/dev/loop0p1  *          2048      411647      204800   83  Linux
/dev/loop0p2          411648      718847      153600   83  Linux
/dev/loop0p3  *       718848      819199       50176   83  Linux
/dev/loop0p4          819200     1023999      102400   83  Linux
""", b"", 0, "msdos")
    manager = device.DeviceManager("/dev/loop0", partition_mask="{0}p{1}")
    result = manager.get_partition_code(2)

    assert result == "83"


def test_get_partition_code_mbr_bootable(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/loop0: 524 MB, 524288000 bytes
255 heads, 63 sectors/track, 63 cylinders, total 1024000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x01517e72

      Device Boot      Start         End      Blocks   Id  System
/dev/loop0p1 *          2048      411647      204800   83  Linux
/dev/loop0p2          411648      718847      153600   83  Linux
/dev/loop0p3 *        718848      819199       50176   83  Linux
/dev/loop0p4          819200     1023999      102400   83  Linux
""", b"", 0, "msdos")
    manager = device.DeviceManager("/dev/loop0", partition_mask="{0}p{1}")
    result = manager.get_partition_code(3)

    assert result == "83"


def test_get_partition_code_mbr_invalid_value_passed(monkeypatch):
    generateStandardMock(monkeypatch,
                         b"""Disk /dev/loop0: 524 MB, 524288000 bytes
255 heads, 63 sectors/track, 63 cylinders, total 1024000 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x01517e72

      Device Boot      Start         End      Blocks   Id  System
/dev/loop0p1 *          2048      411647      204800   83  Linux
/dev/loop0p2          411648      718847      153600   83  Linux
/dev/loop0p3 *        718848      819199       50176   83  Linux
/dev/loop0p4          819200     1023999      102400   83  Linux
    """, b"", 0, "msdos")
    with pytest.raises(ValueError) as execinfo:
        manager = device.DeviceManager("/dev/loop0", "{0}p{1}")
        manager.get_partition_code(5)


def test_get_partition_code_mbr_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"", b"Test error.", 2, "msdos")
    manager = device.DeviceManager("mbr.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_code(4)

    assert "Test error." in str(execinfo)


def test_lvm_get_partitions_standard(monkeypatch):
    generateStandardMock(
        monkeypatch,
        b"""LV:VG:Attr:LSize:Pool:Origin:Data%:Meta%:Move:Log:Cpy%Sync:Convert
  backup:fileserver:-wi-a-----:5,00g::::::::
  media:fileserver:-wi-a-----:1,00g::::::::
  share:fileserver:-wi-a-----:50,00g::::::::
  root:ubuntu-vg:-wi-ao----:6,52g::::::::
  swap_1:ubuntu-vg:-wi-ao----:1,00g::::::::
    """, b"", 0, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    parts = manager.get_partitions()
    assert ["backup", "media", "share"] == parts


def test_lvm_get_partitions_bad_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"Test error.", b"", 1, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partitions()

    assert "Test error." in str(execinfo)


def test_lvm_get_drive_size_standard(monkeypatch):
    generateStandardMock(monkeypatch, b"  12566528S", b"", 0, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    result = manager.get_drive_size()
    assert 12566528 == result


def test_lvm_get_drive_size_bytes_standard(monkeypatch):
    generateStandardMock(monkeypatch, b"  6434062336B", b"", 0, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    result = manager.get_drive_size_bytes()
    assert 6434062336 == result


def test_lvm_get_drive_size_bytes_bad_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"Test error", b"", 1, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_drive_size_bytes()

    assert "Test error" in str(execinfo)


def test_lvm_get_partition_size(monkeypatch):
    generateStandardMock(
        monkeypatch,
        b"/dev/fileserver/media:fileserver:3:1:-1:0:2097152:256:-1:0:-1:252:3",
        b"", 0, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    result = manager.get_partition_size("media")
    assert result == 2097152


def test_lvm_get_partition_size_bad_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"Didn't work.", b"", 1, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_size("media")

    assert "Didn't work." in str(execinfo)


def test_lvm_get_partition_code_unsupported():
    manager = device.LVMDeviceManager("/dev/fileserver")
    with pytest.raises(UnsupportedDeviceError) as execinfo:
        manager.get_partition_code("media")


def test_lvm_get_partition_alignment_unssported():
    manager = device.LVMDeviceManager("/dev/fileserver")
    with pytest.raises(UnsupportedDeviceError) as execinfo:
        manager.get_partition_alignment()


def test_get_empty_space(monkeypatch):
    generateStandardMock(monkeypatch, b"  70921486336B", b"", 0, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    result = manager.get_empty_space()
    assert result == 70921486336


def test_get_empty_space_non_zero_return_code(monkeypatch):
    generateStandardMock(monkeypatch, b"Error.", b"", 1, "lvm")
    manager = device.LVMDeviceManager("/dev/fileserver")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_empty_space()

    assert "Error." in str(execinfo)
