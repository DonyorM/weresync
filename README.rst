########
WereSync
########

`Installation <#installation>`__ | `Basic Usage <#basic-usage>`__ | `Documentation <https://weresync.readthedocs.io/en/master/>`__ | `Contributing <#contributing-and-bug-reports>`__ 

.. image:: https://github.com/DonyorM/weresync/raw/master/docs/source/img/weresync-logo.png
   :align: center 
   :alt: WereSync Logo

A lone hard drive stands atop a data heap, staring at the full moon. Suddenly, it
transforms...into a bootable clone of your drive, whirring hungrily at the digital
moon.

WereSync takes a Linux hard drive and effectively clones it, but works incrementally
so you don't have to spend so long backing up each time. Additionally, WereSync
can clone to a smaller drive, if your data will fit on the smaller drive. Because WereSync
uses rsync to copy, it can copy a running drive, though certain parts of state may not be
preserved.

Why Use WereSync?
=================

Hopefully, you think this project looks amazing and you want to try it right away.
However, you may be skeptical about the usefulness of WereSync. You may be
thinking, I can do this exact same thing using gparted or ddrescue. Hear me out!
There are a few reasons to use WereSync over the other tools.

- **WereSync is accessible to less-technical users.** It comes with a simple
  interface and clone a drive with a single command while your computer is
  running. No booting to a live disk or pushing through a long initiation
  process. Unlike `dd` or CloneZilla, WereSync requires a low level of
  technical skill and has an easy learning curve
- WereSync can run while the your main drive is being used, instead of blocking your computer up for hours at a time
- WereSync will incrementally update clones, making subsequent clones much faster.
- WereSync works quickly, a single command copies your entire drive, no booting to live CDs or managing MBRs.
- WereSync can copy to a smaller drive, provided your drive's data will fit.
- WereSync creates new UUIDs for the new partitions, allowing you to use the old and new drives alongside each other.

Full documentation may be found `here <https://weresync.readthedocs.io/en/master/>`__.

Installation
============

WereSync can be installed using the `setup.py` file.

.. code-block:: bash

   $ ./setup.py install

If you have `pip <https://pypi.python.org/pypi/pip/>`__ installed, you can easily install WereSync with the following command::

    $ pip install weresync

For more in-depth instructions, see the `installation documentation <https://weresync.readthedocs.io/en/master/installation.html>`__.

Basic Usage
===========

**Note:** WereSync requires root capabilities to run because it has to access block devices.

The gui can be launched with the command::

    $ sudo weresync-gui

Which generates the following GUI, though generally the advanced options are unneeded:

.. image:: https://github.com/DonyorM/weresync/raw/master/docs/source/img/gui-example.png
   :align: left 
   :alt: Picture of WereSync GUI

To see the options for the terminal command use::

    $ weresync -h

To copy from /dev/sda to /dev/sdb (the two drives must have the same partition scheme) use::

    $ sudo weresync /dev/sda /dev/sdb

For more information, including how to copy the partition table from drive to
another, see the `Basic Usage <https://weresync.readthedocs.io/en/master/weresync.html>`__
documentation page.

Documentation
=============

Documentation can be found on the `Read the Docs <https://weresync.readthedocs.io/en/master/>`__.

Contributing and Bug Reports
============================

First, take a look at our `contribution guidelines <https://github.com/DonyorM/weresync/blob/master/CONTRIBUTING.rst>`__.

To contribute simply fork this repository, make your changes, and submit a pull
request. Bugs can be reported on the `issue tracker <https://github.com/donyorm/weresync/issues/>`__

WereSync currently has huge need of people testing the program on complex drive setups. In order to do this please:



1. Install WereSync from pip::

    pip install weresync

#. Run it on your system::

    sudo weresync -C source_drive target_drive

#. Report any errors to the `issue tracker <https://github.com/DonyorM/weresync/issues>`__. Please be sure to post the contents of ``/var/log/weresync/weresync.log`` and ``fdisk -l``.

All contributions will be greatly appreciated!

Distributions Capability for Drive Copying
------------------------------------------

|ubuntu| |debian| |arch| |centos| |fedora| |opensuse|

.. |ubuntu| image:: https://img.shields.io/badge/ubuntu-stable-brightgreen.svg
.. |arch| image:: https://img.shields.io/badge/Arch%20Linux-stable-brightgreen.svg
.. |centos| image:: https://img.shields.io/badge/CentOS-not%20tested-red.svg
.. |fedora| image:: https://img.shields.io/badge/Fedora-not%20tested-red.svg
.. |opensuse| image:: https://img.shields.io/badge/openSUSE-not%20tested-red.svg
.. |debian| image:: https://img.shields.io/badge/Debian-stable-brightgreen.svg

If you are able to test any of these systems, please report your exprience at the `issue tracker <https://github.com/DonyorM/weresync/issues>`__. Any help will be much appreciated.

Licensing
=========

This project is licensed under the `Apache 2.0 License <https://www.apache.org/licenses/LICENSE-2.0>`__. Licensing is in the **LICENSE.txt** file in this directory.

Acknowledgments
===============

Huge thanks to the creators of:

* `rsync <https://rsync.samba.org/>`__, whose software allowed this project to be possible.
* `GNU Parted <https://www.gnu.org/software/parted/>`__
* And `GPT fdisk <http://www.rodsbooks.com/gdisk/>`__
 
