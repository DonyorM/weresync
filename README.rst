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
uses rsync to copy, it can copy a running drive,though certain parts of state may not be
preserved.

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
 
