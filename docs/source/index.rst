.. WereSync documentation master file, created by
   sphinx-quickstart on Thu Nov  3 19:08:36 2016.
.. include:: global.rst.inc
  
========
WereSync
========

.. image:: img/weresync-logo.png
   :align: center

Making your backup drives into were-drives, transforming them into clones at will.

WereSync incrementally backups up hard drives using rsync. Backups can be run while
you use your computer. As icing on the cake, you can boot your clone just like your
normal computer.

Installation
------------
WereSync can easily be installed with pip. Simply use::

    $ pip install weresync

For more in depth information see the `installation guide <installation.html>`_.

Basic Usage
-----------

.. IMPORTANT::
   WereSync requires root permissions to run, because it has to access block devices. Standard linux permissions restrict access to block devices to ordinary users.

To start the gui use::

    $ sudo weresync-gui

For help on how the terminal command works, run::

    $ weresync -h

For a basic setup, you could use a version of the following command::
 
    $ sudo weresync -C --efi-partition <partition_number> /dev/sda /dev/sdb

=========
Contents:
=========

.. toctree::
   :maxdepth: 2

   installation
   gui
   weresync
   api
   bootloader
   translation
   issues

============
Contributing
============

First, take a look at our `contribution guidelines <https://github.com/DonyorM/weresync/blob/master/CONTRIBUTING.rst/>`_.

Then, if you would like to submit a new feature or fix a bug, please submit a Pull Request at the `project repository <https://github.com/donyorm/weresync/>`_.
You can submit a bug report on the `issue tracker <https://github.com/donyorm/weresync/issues/>`_.

==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

