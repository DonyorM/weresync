.. Manpage documentation for WereSync. This should be converted to the groff format using rst2man.py

========
weresync
========

--------------------------------
clone linux drives incrementally
--------------------------------

:Author: Daniel Manila <dmv@springwater7.org>
:Date: June 30th, 2017
:Version: 1.0
:Manual Section: 1
:Manual group: admin

weresync-gui - GUI interface for the weresync program.

SYNOPSIS
--------

weresync [ options ] [**-g** *ROOT_PARTITION*] [**-B** *BOOT_PARTITION*]
         [**-E** *EFI_PARTITION*] [**-L** *BOOTLOADER*]
         [**-l** *LVM_SOURCE* [*LVM_TARGET*]]
         source target

**weresync-gui**

DESCRIPTION
-----------

WereSync clones linux drives incrementally producing a bootable clone. Clones produced by WereSync will have different UUIDs than the original drive, but WereSync will update the fstab and bootloader to allow the clone to properly boot. Clones can be created with one command or one button click, using *weresync* or *weresync-gui* respectively.

OPTIONS
-------

The *weresync-gui* command takes no arguments. These arguments apply to the *weresync* command.

--h, --help
     Displays help message.

-C, --check-and-partition
     Checks if all partitions are large enough and formatted correctly to allow drive to be copied. If the partitions are not valid, the target drive will be re-partitioned and reformatted. If unset, no checking occurs.
     
-s, --source-mask *MASK*
     A string to be passed to format() that will produce a partition identifier (/dev/sda1 or such) of the source drive when passed two arguments: the identifier ("/dev/sda") and a partition number in that order. Defaults to "{0}{1}"

-t, --target-mask *MASK*
    A string to be passed to format() that will produce a partition identifier (/dev/sda1 or such) of the source drive when passed two arguments: the identifier ("/dev/sda") and a partition number in that order. Defaults to "{0}{1}".

-e, --excluded-partitions *LIST*
    A list of comma separated partition numbers that should not be searched or copied at any time. These partitions will still be formatted if -C is passed. Defaults to empty.

-b, --break-on-error
    If passed the program will halt if there are any errors copying. This flag is not recommended because it will halt even if encountering a normal issue, like a swap partition.

-g, --root-partition *PART_NUM*
    The partition mounted on /. It is recommended to pass this always, but WereSync will attempt to find the main partition even if it is not passed.

-B, --boot-partition *PART_NUM*
    The partition that should be mounted on /boot of the grub_partition. If you have a separate boot partition, you must use this flag.

-E, --efi-partition *PART_NUM*
    The partition that should be mounted on /boot/efi of the grub_partition. If passed this will create the /boot/efi folder if it does not exist and pass it to grub. Required if you have an EFI partition.

-m, --source-mount *DIR*
    The directory to mount partitions from the source drive on. Cannot be the same as --target-mount. If unset, WereSync generates a randomly named directory in the /tmp dir.

-M, --target-mount *DIR*
    The directory to mount partitions from the target drive on. Cannot be the same as --source-mount. If unset, WereSync generates a randomly named directory in the /tmp dir. 

-r, --rsync-args *RSYNC_ARGS*
    The arguments to be passed to the rsync instance used to copy files. Defaults to "-aAXxH --delete"

-l, --lvm *SOURCE* [*TARGET*]
    This argument expects either one or two arguments specifying the logical volume groups to copy from and to, respectively. If no target VG is passed, WereSync will use the VG SOURCE-copy. If the target does not exist, WereSync will create it.

-L, --bootloader *BOOTLOADER*
    The plugin to use to install the bootloader. Such plugins can be found
    at the bottom of the help message. Defaults to using the "uuid_copy"
    plugin.

-v, --verbose
    Makes WereSync increase output and include more minor details.

-d, --debug
    Causes a huge amount of output, useful for debugging the program. Usually not needed for casual use.

COPYRIGHT
---------

Copyright 2016 Daniel Manila

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

|
|    `<http://www.apache.org/licenses/LICENSE-2.0>`_
|

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


SEE ALSO
--------

Full documentation can be found at WereSync's documentation on Read The Docs:
`<https://weresync.readthedocs.io/en/master/>`_
