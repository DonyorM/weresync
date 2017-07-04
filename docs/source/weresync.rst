.. WereSync command documentation.

######################
Command Line Interface
######################

For help using the weresync command when you are on the command line, use the
help flag on the weresync command::

    $ weresync -h

Basic Usage
===========

Requirements
------------

.. IMPORTANT::
   WereSync requires root permissions to run, because it has to access block devices. Standard linux permissions restrict access to block devices to ordinary users.

WereSync will copy GPT, MBR, and LVM drives. The source drive
must have a valid disk label (such a disk label can be created with the gdisk or 
fdisk command). All `dependencies <installation.html#dependencies>`_ must be installed.

Commands
--------

WereSync always requires a source drive and a target drive. The source drive comes
first. WereSync requires root permissions in order to access hard drive data. So to copy from /dev/sda to /dev/sdb, use this command::

    $ sudo weresync /dev/sda /dev/sdb

This will simply copy data from one partition to the another, and if the partitions
are different, you will encounter an error. To have WereSync fix your target drives
partitions, use the ``-C`` flag::

    $ sudo weresync -C /dev/sda /dev/sdb

On subsequent backups, you may not want to include the -C flag, since this can
sometimes trigger unnecessary repartitioning.

LVM
+++

WereSync supports the copying of LVM drives with the `-l` flag::


    $ sudo weresync -C -l -B 1 volume-group /dev/sda /dev/sdb

It is highly recommended to pass which partition of the drive your boot
partition is stored on, if you have a boot partition seperate from the VG.
If you have your /boot folder inside the VG, your bootloader installation
mileage may vary.

Bootloader Installation
-----------------------

WereSync will attempt to update the target drive's system to it will boot up
properly. By default this simply changes the UUIDs in the files of the /boot
folder and EFI system partition, but specific bootloader installation plugins
can also be specified.

For this to work, it is highly recommended that you pass the root partition
with the ``-g`` flag::

    $ sudo weresync -g 1 /dev/sda /dev/sdb

If this is not passed, WereSync will attempt to discover the root filesystem on
its own, but this is unreliable.

In order for a drive on an EFI system to be made bootable, the partition number
of the EFI system partition
to be passed to WereSync with the ``-E`` flag. In this case, the root
filesystem should be installed on (``-g`` flag) should also be passed,
especially if the efi partition comes before the grub partition on the
partition list, as the efi partition can trigger the mechanisms used to find
the grub partition.

.. code-block:: bash

    $ sudo weresync -E 2 -g 3 /dev/sda /dev/sdb

If you have your boot folder on a seperate partition, be sure to let WereSync know which partition that folder is on with the ``-B`` flag::

    $ sudo weresync -E 1 -g 2 -B 3 /dev/sda /dev/sdb
        
Obviously replace the numbers with the proper values for your system.

Bootloader Plugins
++++++++++++++++++

Some bootloaders, especially those for MBR booting, require a more specific
process. Bootloader plugins allow such a process to occur. All plugins
available will be displayed at the end of the help message displayed with the
``-h`` flag. The specific plugin to use may be passed with the ``-L`` flag::

    $ sudo weresync -L grub2 -E 1 -g 2 /dev/sda /dev/sdb

For more information on installing and creating bootloader plugins see the
`bootloader plugin page <bootloader.html>`_

Image Files
-----------

WereSync supports image files normally. If either the target or the source ends in
".img" WereSync will automatically consider it an image file and mount it as such.
Currently there is no way to mark files not ending in .img as image files.

To create an image file on linux, use::

    $ dd if=/dev/zero of=my_image.img bs=1M count=<size in MB>
    $ sgdisk my_image.img -o

The second command creates a partition table on the command, which is currently
needed by WereSync to start analyzing a drive.

In-Depth Parameter Definitions
============================== 

Usage::

     weresync [-h] [-C] [-s SOURCE_MASK] [-t TARGET_MASK]
                [-e EXCLUDED_PARTITIONS] [-b] [-g ROOT_PARTITION]
                [-B BOOT_PARTITION] [-E EFI_PARTITION] [-m SOURCE_MOUNT]
                [-M TARGET_MOUNT] [-r RSYNC_ARGS] [-l] [-L BOOTLOADER]
                [-v] [-d] source target

.. list-table:: Parameters
   :widths: 15 10 30 10
   :header-rows: 1

   * - Long Option
     - Short Option
     - Description
     - Default 
   * - --help
     - -h
     - Displays the help message
     - N/A
   * - --check-and-partition
     - -C
     - Checks if all partitions are large enough and formatted correctly to allow
       drive to be copied. If the partitions are not valid, the target drive will
       be re-partitioned and reformatted.
     - If unset, no checking occurs.
   * - --source-mask MASK
     - -s MASK
     - A string to be passed to :py:func:`format` that will produce a partition
       identifier (/dev/sda1 or such) of the source drive when passed two
       arguments: the identifier ("/dev/sda") and a partition number in that order.
     - "{0}{1}"
   * - --target-mask MASK
     - -t MASK
     - Same as --source-mask, but applied to the target drive.
     - "{0}{1}"
   * - --excluded-partitions LIST
     - -e LIST
     - A list of comma separated partition numbers that should not be searched or
       copied at any time. These partitions will still be formatted if `-C` is
       passed.
     - []
   * - --break-on-error
     - -b
     - If passed the program will halt if there are any errors copying. This
       flag is not recommended because it will halt even if encountering a normal
       issue, like a swap partition.
     - False
   * - --root-partition PART_NUM
     - -g PART_NUM
     - The partition mounted on /. It is recommended to
       pass this always, but WereSync will attempt to find the main partition
       even if it is not passed.
     - None, WereSync searches for the partition.
   * - --boot-partition PART_NUM
     - -B PART_NUM
     - The partition that should be mounted on /boot of the grub_partition. If you
       have a separate boot partition, you must use this flag.
     - None, no partition mounted.
   * - --efi-partition PART_NUM
     - -E PART_NUM
     - The partition that should be mounted on /boot/efi of the grub_partition.       If passed this will create the /boot/efi folder if it does not exist and pass
       it to grub. Required if you have an EFI partition.
     - None
   * - --source-mount DIR
     - -m DIR
     - The directory to mount partitions from the source drive on. Cannot be the
       same as --target-mount.
     - None, randomly generated directory in the /tmp folder.
   * - --target-mount DIR
     - -M DIR
     - The directory to mount partitions from the target drive on. Cannot be the
       same as --source-mount.
     - None, randomly generated directory in the /tmp folder.
   * - --rsync-args RSYNC_ARGS
     - -r RSYNC_ARGS
     - The arguments to be passed to the rsync instance used to copy files.
     - -aAXxvH --delete
   * - --lvm SOURCE [TARGET]
     - -l
     - This argument expects either one or two arguments specifying the
       logical volume groups to copy from and to, respectively. If no target
       VG is passed, WereSync will use the VG SOURCE-copy. If the target does
       not exist, WereSync will create it.
     - No Volume Groups are copied 
   * - --bootloader BOOTLOADER
     - -L BOOTLOADER
     - The plugin to use to install the bootloader. Such plugins can be found
       at the bottom of the help message.
     - The "uuid_copy" plugin.
   * - --verbose
     - -v
     - Makes WereSync increase output and include more minor details.
     - Only Warnings, more serious issues, and basic info are printed.
   * - --debug
     - -d
     - Causes a huge amount of output, useful for debugging the program. Usually
       not needed for casual use.
     - Only Warnings, more serious issues, and basic info are printed.

       
