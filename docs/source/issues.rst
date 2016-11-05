.. Known Issues Page

Known Issues
============

* WereSync does not work with bootloaders other than Grub. It will always attempt to install Grub on a drive.
* WereSync can only copy GPT drives
* Due to the complexity of boot loader installations, bootloading may not always install correctly depending on the nature of your setup
* Occasionally, installing the boot loader can change the order of boot on the parent drive, especially for a dual-boot drive

If you have found anymore issues, please report them to the `issue tracker <https://github.com/donyorm/weresync/issues/>`_.
