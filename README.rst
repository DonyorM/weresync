########
WereSync
########

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

First and foremost, most other cloning tools require confidence in one's
technical skill. `dd` will easily destroy your drive, gparted requires
knowing what flags and partition types to use, and CloneZilla is just
about the opposite of user friendly. WereSync primarily attempts to
help people who don't want to spend the time and effort to learn
how to safely use a cloning tool.

But WereSync also has some of its own features. It contains the ability to properly
copy a partition table to a new drive and format the new drive. It uses rsync to copy
so, unlike most other cloning tools, it will update incrementally – saving time. WereSync has
good default directory exclusions (such as /dev or /proc) so it won't copy parts of your system which should not be copied.
On top of this WereSync will create new UUIDs for the partitions on the cloned drive,
allowing the clone to be used alongside the original drive. But the clone will still
be bootable because WereSync updates the fstab and reinstalls the boot loader. Not to
mention it can complete the entire clone while leaving the original drive running ("hot cloning"),
unlike `dd` or CloneZilla.

All of this is accomplished with one button click.

Installation
============

WereSync can be installed using the `setup.py` file.

.. code-block:: bash

   $ ./setup.py install

If you have `pip <https://pypi.python.org/pypi/pip/>`_ installed, you can easily install WereSync with the following command::

    $ pip install weresync

For more in-depth instructions, see the `installation documentation <https://pythonhosted.org/WereSync/installation.rst>`_.

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
another, see the `Basic Usage <https://pythonhosted.org/WereSync/weresync.html>`_
documentation page.

Documentation
=============

Documentation can be found on the `Python Package Index <https://pythonhosted.org/WereSync/>`_.

Contributing and Bug Reports
============================

First, take a look at our `contribution guidelines <https://github.com/DonyorM/weresync/blob/master/CONTRIBUTING.rst>`_.

To contribute simply fork this repository, make your changes, and submit a pull
request. Bugs can be reported on the `issue tracker <https://github.com/donyorm/weresync/issues/>`_

Licensing
=========

This project is licensed under the `Apache 2.0 License <https://www.apache.org/licenses/LICENSE-2.0>`_. Licensing is in the **LICENSE.txt** file in this directory.

Acknowledgments
===============

Huge thanks to the creators of:

* `rsync <https://rsync.samba.org/>`_, whose software allowed this project to be possible.
* `GNU Parted <https://www.gnu.org/software/parted/>`_
* And `GPT fdisk <http://www.rodsbooks.com/gdisk/>`_
 
