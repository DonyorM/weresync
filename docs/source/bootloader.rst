.. Documentaion on bootloader plugins
.. include:: global.rst.inc

==================
Bootloader Plugins
==================

Bootloader plugins allow WereSync to have special process to install specific
bootloaders, allowing support for a wider variety of bootloaders.

The default bootloader plugin, UUID Copy, simply changes the UUIDs in each
file in the /boot folder. UUIDs in /etc/fstab are always updated, regardless
of boot plugin.

Installing
----------

Bootloader plugins can be installed to two different locations:
``/usr/local/weresync/plugins`` and the python site-packages directory. This
means that plugins can be installed as pip packages or installed manually.

Creating Bootloader Plugins
---------------------------

Bootloader plugins are very simple files. They must be a single python file
that fits the form "weresync_<plugin name>.py". Inside this file, a class
must extend :py:class:`~weresync.plugins.IBootPlugin` and at least implement
the method :py:func:`~weresync.plugins.IBootPlugin.install_bootloader`.

No other files are necessary, but other files may be packaged with a plugin
for it to call within its process.

For an example plugin see the `Grub2 Plugin <https://github.com/DonyorM/weresync/blob/master/src/weresync/plugins/weresync_grub2.py>`_.

Method Implementations
++++++++++++++++++++++

All plugins should extend :py:func:`~weresync.plugins.IBootPlugin`, as
mentioned above (signature: ``class MyPlugin(IBootPlugin)``). They should all
call ``super().__init__(name, prettyName)`` where ``name`` is the portion
of the file name after the "weresync\_" prefix but before the ".py" extension
(weresync_<this part>.py). ``prettyName`` can be anything, but should be human
readable. Currently this is only displayed by the GUI.

For any given bootloader plugin, the following methods are called in this
order:

* :py:func:`~weresync.plugins.IBootPlugin.activate` is called before bootloader
  installation. All files will be exactly the same as the source drive at this
  point. Implementing this method is not required.
* :py:func:`~weresync.plugins.IBootPlugin.install_bootloader` is called to
  install the bootloader. This should do the majority of the work. Implementing
  this method is required.
* :py:func:`~weresync.plugins.IBootPlugin.deactivate` is called after
  bootloader installation is complete. Implementing this method is not
  required.

:py:class:`~weresync.plugins.IBootPlugin` contains one more method,
:py:func:`~weresync.plugins.IBootPlugin.get_help`, this is an optional method
that should return a string describing what the plugin accomplishes (i.e. what
bootloader it installs).

Helpful Functions
+++++++++++++++++

Several important methods are available to plugin developers. The ``copier``
parameter of :py:func:`~weresync.plugins.IBootPlugin.install_bootloader`
provides access to a
:py:class:`~weresync.device.DeviceCopier` instance. This instance then provides
access to :py:class:`~weresync.device.DeviceManager` instances through the
``copier.source`` and ``copier.target`` fields. These instances allow a plugin
to mount and umnount partitions and get information about the drives in
question.

The method :py:func:`~weresync.device.DeviceCopier.get_uuid_dict`  of the
``copier`` parameter returns a dictionary
relating the UUIDs of the source drive with those of the target drive.
This can be used in conjunction with :py:func:`weresync.device.multireplace`
to update the UUIDs of any given string, for example one from a file.

The function :py:func:`weresync.plugins.translate_uuid` makes use of the
above two functions to step recursively through the passed folder and update
the UUIDs of every text file.

LVM
+++

Your bootloader will be expected to support LVM systems as well. One can test
if Logical Volume Groups are being copied by testing if the ``lvm_source`` field
of the ``copier`` object is not ``None``::

    if copier.lvm_source is not None:
        # Handle copying VG

The ``lvm_source`` and ``lvm_target`` fields will be
:py:class:`~weresync.device.LVMDeviceManager` objects, but can generally be
treated like ordinary DeviceManager objects.

Builtin Bootloaders
-------------------

UUID Copy
+++++++++

.. automodule:: weresync.plugins.weresync_uuid_copy

Grub2
+++++

.. automodule:: weresync.plugins.weresync_grub2

Syslinux
++++++++

.. automodule:: weresync.plugins.weresync_syslinux

