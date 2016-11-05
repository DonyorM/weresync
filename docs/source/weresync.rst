.. WereSync command documentation.

######################
Command Line Interface
######################

For help using the weresync command when you are on the command line, use the
help flag on the weresync command::

    $ weresync -h

.. warning::

    WereSync does not currently support MBR drives. It only functions with GPT
    drives. Any contribution to adding MBR capability would be appreciated.

Basic Usage
===========

WereSync always requires a source drive and a target drive. The source drive comes
first. So to copy from /dev/sda to /dev/sdb, use this command::

    $ weresync /dev/sda /dev/sdb

This will simply copy data from one partition to the another, and if the partitions
are different, you will encounter an error. To have WereSync fix your target drives
partitions, use the ``-C`` flag::

    $ weresync -C /dev/sda /dev/sdb.

On subsequent backups, you may not want to include the -C flag, since this can
sometimes trigger unnecessary repartitioning.

In order for a drive on an EFI system to be made bootable, the efi partition number
(``-E`` flag) needs to be passed to WereSync. In this case, the partition grub
should be installed on (``-g`` flag) should also be passed, especially if the efi
partition comes before the grub partition on the partition list, as the efi
partition can trigger the mechanisms used to find the grub partition. 

.. code-block:: bash

    $ weresync -C -E 2 -g 3 /dev/sda /dev/sdb

Obviously replace the numbers with the proper values for your system. Usually the
grub partition will be the one mounted on /

In-Depth Parameter Definitions
============================== 

Usage::

     weresync [-h] [-C] [-s SOURCE_MASK] [-t TARGET_MASK]
                [-e EXCLUDED_PARTITIONS] [-b] [-g GRUB_PARTITION]
                [-B BOOT_PARTITION] [-E EFI_PARTITION] [-m SOURCE_MOUNT]
                [-M TARGET_MOUNT] [-v] [-d]
                source target

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
   * - --grub-partition PART_NUM
     - -g PART_NUM
     - The partition number that grub should be installed on. It is recommended to
       pass this always, but it WereSync will attempt to find the main partition
       even if it is not passed.
     - None, WereSync searches for the partition.
   * - --boot-partition PART_NUM
     - -B PART_NUM
     - The partition that should be mounted on /boot of the grub_partition. If you
       have a separate boot partition, you must use this flag.
     - None, no partition mounted.
   * - --efi-partition PART_NUM
     - -E PART_NUM
     - The partition that should be mounted on /boot/efi of the grub_partition. If
       passed this will create the /boot/efi folder if it does not exist and pass
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
   * - --verbose
     - -v
     - Makes WereSync increase output and include more minor details.
     - Only Warnings, more serious issues, and basic info are printed.
   * - --debug
     - -d
     - Causes a huge amount of output, useful for debugging the program. Usually
       not needed for casual use.
     - Only Warnings, more serious issues, and basic info are printed.

       
