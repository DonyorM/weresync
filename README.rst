########
WereSync
########

A lone hard drive stands atop a data heap, staring at the full moon. Suddenly, it
transforms...into a bootable clone of your drive, whirring hungrily at the digital
moon.

WereSync takes a Linux hard drive and effectively clones ti, but works incrementally
so you don't have to spend so long backing up each time. Additionally, WereSync
can clone to a smaller drive, if your data will fit on the smaller drive.

Installation
============

WereSync can be installed using the `setup.py` file.

.. code-block:: bash

   $ ./setup.py install

If you have `pip <https://pypi.python.org/pypi/pip/>`_ installed, you can easily install WereSync with the following command::

    $ pip install weresync

Documentation
=============

Documentation can be found on the Python Package Index (link coming).

Contributing and Bug Reports
============================

To contribute simply clone this repository, make your changes, and submit a pull
request. Bugs can be reported on the `issue tracker <https://github.com/donyorm/weresync/issues/>`_

Licensing
=========

This project is licensed under the `Apache 2.0 License <https://www.apache.org/licenses/LICENSE-2.0/>`_. Licensing is in the **LICENSE.txt** file in this directory.

Acknowledgments
===============

Huge thanks to the creators of:

* `rsync <https://rsync.samba.org/>`_, whose software allowed this project to be possible.
* `GNU Parted <https://www.gnu.org/software/parted/index.shtml/>`_
* And `GPT fdisk <http://www.rodsbooks.com/gdisk/>`_
  

