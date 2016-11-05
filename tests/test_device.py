import pytest
import unittest.mock as mock
import weresync.device as device
from weresync.exception import DeviceError

def generateMockPopen(monkeypatch, return_value_output, return_value_error, return_code):
    mock_popen = mock.MagicMock()
    mock_popen.communicate.return_value = (return_value_output, return_value_error)
    mock_popen.returncode = return_code
    def popen_constructor(*args, **kargs):
        return mock_popen
    monkeypatch.setattr("subprocess.Popen", popen_constructor)  


def test_get_partitions_valid(monkeypatch):
    generateMockPopen(monkeypatch,
    b"""Model: Unknown (unknown)
Disk /dev/nbd0: 8590MB
Sector size (logical/physical): 512B/512B
Partition Table: gpt

Number  Start   End     Size    File system     Name  Flags
 4      1049kB  500MB   499MB                         bios_grub
 1      500MB   6000MB  5500MB  ext4
 2      6000MB  7400MB  1400MB  ext4
 3      7400MB  8589MB  1189MB  linux-swap(v1)\n """, None, 0) #standard return from sgdisk -p
    manager = device.DeviceManager("/dev/sdd")
    result = manager.get_partitions()
    assert result == [4, 1, 2, 3]

def test_get_partitions_none_zero_returncode(monkeypatch):
    generateMockPopen(monkeypatch, None, b"Error.", 1)
    manager = device.DeviceManager("/dev/sda") 
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partitions()

    assert "Error." in str(execinfo.value)

def test_get_partitions_no_partitions(monkeypatch):
    generateMockPopen(monkeypatch, b"Nope\nvery\nvery\nbad\ndata", None, 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_partitions()
    assert result == []

def test_mount_point_normal(monkeypatch):
    generateMockPopen(monkeypatch, b"""TARGET      SOURCE     FSTYPE  OPTIONS
/mnt /dev/sda11 fuseblk rw,nosuid,nodev,relatime,user_id=0,group_id=0,def
""", None, 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.mount_point(3)
    assert "/mnt" == result

def test_mount_point_non_zero_return_code(monkeypatch):
    generateMockPopen(monkeypatch, b"""TARGET      SOURCE     FSTYPE  OPTIONS\n
/mnt /dev/sda11 fuseblk rw,nosuid,nodev,relatime,user_id=0,group_id=0,def\n
""", b"Error.", 2)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        result = manager.mount_point(5)

    assert "Error." in str(execinfo.value)

def test_mount_point_no_mount_point(monkeypatch):
    generateMockPopen(monkeypatch, b"", None, 1) #findmnt returns 1 when there is no mount point
    manager = device.DeviceManager("/dev/sda")
    result = manager.mount_point(5)
    assert result == None

def test_mount_partition(monkeypatch):
    generateMockPopen(monkeypatch, b"", None, 0)
    manager = device.DeviceManager("/dev/sda")
    manager.mount_partition(3, "/mnt")
    
def test_mount_partition_non_zero_return_code(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.mount_partition(3, "/mnt")

    assert "Error." in str(execinfo.value)

def test_unmount_partition(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    manager.unmount_partition(5)

def test_unmount_partition_non_zero(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.unmount_partition(5)

    assert "Error." in str(execinfo.value)

def test_get_partition_table_type(monkeypatch):
    generateMockPopen(monkeypatch, b"""Model:  (file)
Disk /media/Data/Documents/Programming/testing-super/gpt.img: 524MB
Sector size (logical/physical): 512B/512B
Partition Table: gpt

Number  Start   End     Size    File system  Name   Flags
 1      17.4kB  50.0MB  50.0MB               test
 2      50.3MB  74.4MB  24.1MB               cool
 3      74.4MB  200MB   126MB                nice
 4      200MB   350MB   150MB                great
 5      350MB   500MB   150MB                sweet
 6      500MB   524MB   24.1MB""", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_partition_table_type()
    assert "gpt" == result

def test_get_partition_table_type_non_zero_return_code(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_table_type()

    assert "Error." in str(execinfo.value)

def test_get_drive_size(monkeypatch):
    generateMockPopen(monkeypatch, b"192", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_drive_size()
    assert 192 == result

def test_get_drive_size_non_zero_return_code(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_drive_size()

    assert "Error." in str(execinfo.value)

def test_get_drive_size_bytes(monkeypatch):
    generateMockPopen(monkeypatch, b"190", b"", 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_drive_size_bytes()

    assert 190 == result

def test_get_drive_size_bytes_non_zero_return_code(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_drive_size()

    assert "Error." in str(execinfo.value)

def test_get_partition_used(monkeypatch):
    generateMockPopen(monkeypatch, b"/dev/sda11     676276220 179697120 496579100  27% /media/Data",
                      b"", 0)
    manager = device.DeviceManager("/dev/sda")
    result = manager.get_partition_used(5)
    assert 179697120 == result

def test_get_partition_used_non_zero_return(monkeypatch):
    generateMockPopen(monkeypatch, b"  ", b"Error.", 1)
    manager = device.DeviceManager("/dev/sda")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_used(4)

    assert "Error." in str(execinfo.value) 

def test_get_drive_empty_space(monkeypatch):
    generateMockPopen(monkeypatch, b"""Disk gpt.img: 1024000 sectors, 500.0 MiB
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
                      """,
                      b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_empty_space()
    assert result == 34

def test_get_empty_space_non_zero_return(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 2)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_empty_space()

    assert "Error." in str(execinfo.value)

def test_get_partition_size(monkeypatch):
    generateMockPopen(monkeypatch, b"""Disk /dev/loop0: 1024000 sectors, 500.0 MiB
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
    monkeypatch.setattr("weresync.device.DeviceManager.get_partition_table_type", lambda x: "gpt")
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_size(5)
    assert 4062 == result

def test_get_partition_size_non_zero_return_code(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 2)
    monkeypatch.setattr("weresync.device.DeviceManager.get_partition_table_type", lambda x: "gpt")
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_size(1)

    assert "Error." in str(execinfo)

def test_get_sector_alignment_number(monkeypatch):
    generateMockPopen(monkeypatch, b"""Disk /dev/loop1: 512000 sectors, 250.0 MiB
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
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        result = manager.get_partition_alignment()

    assert "Error." in str(execinfo.value)

def test_get_sector_alignment_number_invalid_return(monkeypatch):
    generateMockPopen(monkeypatch, b"No alignment", b"", 0)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        result = manager.get_partition_alignment()

def test_get_partition_file_system(monkeypatch):
    generateMockPopen(monkeypatch, b"ext4", b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_file_system(4)
    assert result == "ext4"

def test_get_partition_file_system_empty_return(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_file_system(4)
    assert result == None

def test_get_partition_file_system_unsupported_type(monkeypatch):
    generateMockPopen(monkeypatch, b"completelyimpossiblefilesystemtype", b"", 0)
    manager = device.DeviceManager("gpt.img")
    result = manager.get_partition_file_system(4)
    assert result == None

def test_get_partition_file_system_non_zero_return(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.get_partition_file_system(3)

    assert "Error." in str(execinfo.value)

def test_set_partition_file_system_non_zero_return(monkeypatch):
    generateMockPopen(monkeypatch, b"", b"Error.", 1)
    manager = device.DeviceManager("gpt.img")
    with pytest.raises(DeviceError) as execinfo:
        manager.set_partition_file_system(3, "ext4")

    assert "new file system" in str(execinfo.value)
    assert "Error." in str(execinfo.value)

def test_partition_code(monkeypatch):
    generateMockPopen(monkeypatch, b"""Disk /dev/nbd0: 16777216 sectors, 8.0 GiB
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

def get_device_label(monkeypatch):
    generateMockPopen(monkeypatch, b"test_tabel")

#test not working because it involves multople popens
#def test_get_general_info_no_lines_found(monkeypatch):
#    generateMockPopen(monkeypatch, b"", b"", 1)
#    manager = device.DeviceManager("gpt.img")
#    with pytest.raises(DeviceError) as execinfo:
#        pytest.set_trace()
#        manager._get_general_info(1)
#
#    assert "No grep line read" in str(execinfo.value)
