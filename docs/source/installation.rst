.. Installation Instructions

############
Installation
############

Dependencies
============

WereSync requires different programs for different systems. Generally these programs will be installed by default on many standard distributions (such as Ubuntu) and do not need to be manually installed.

- `rsync <https://rsync.samba.org/>`_; required for all systems
- `parted <https://www.gnu.org/software/parted/>`_; required for all systems
- fdisk; required for working with msdos/MBR partitioned drives
- `GPT fdisk <http://www.rodsbooks.com/gdisk/>`_; required for working with GPT partitioned drives
- `gettext <https://www.gnu.org/software/gettext/>`_; required for all systems

Bootloaders
-----------

WereSync will attempt to update the /boot directory of the target drive in
order to make it bootable.

However, some bootloaders, particularly MBR based ones, require a more
bootloader-specific process.

GRUB
++++

As of now, WereSync only supports installing
`Grub <https://www.gnu.org/software/grub/>`_ in this way.
As of now, WereSync only needs to have the grub package installed if you
have an MBR drive. If you have an efi system, you do not need to install
any packages.

You can tell whether or not you have efi by following the instructions on
`this post <http://askubuntu.com/a/162896/375032>`_.

If you do not have efi, you need the grub-pc package, which can be installed with the following command::

    $ sudo apt-get install grub-pc

WereSync Installation
=====================

PIP
---

WereSync can easily be installed with pip::

    $ pip install weresync

Code Repository
---------------

.. code::

    $ git clone https://github.com/DonyorM/weresync.git
    $ cd weresync
    $ python3 setup.py install
