from weresync.plugins import IBootPlugin
import weresync.plugins as plugins
from weresync.exception import CopyError, DeviceError
import subprocess


class SyslinuxPlugin(IBootPlugin):
    """Installs the syslinux bootloader. This bootloader plugin requires the
    "root partition" option to be defined.

    Setups using syslinux's altmbr setup are currently not supported.

    This plugin assumes that the boot folder is in /boot/syslinux. If this is
    not the case a symbolic link should be created.

    This plugin depends on Extlinux being installed."""

    def __init__(self):
        super().__init__("syslinux", "Syslinux")

    def get_help(self):
        return """Installs the BIOS syslinux installer. For EFI systems,
        this simply runs the UUID Copy plugin."""

    def install_bootloader(self, source_mnt, target_mnt, copier,
                           excluded_partitions=[],
                           boot_partition=None, root_partition=None,
                           efi_partition=None):
        if root_partition is None and boot_partition is None:
            boot_part = plugins.search_for_boot_part(target_mnt, copier.target,
                                                     "syslinux",
                                                     excluded_partitions)
            if boot_part is None and copier.lvm_source is not None:
                boot_part = plugins.search_for_boot_part(target_mnt,
                                                         copier.lvm_source,
                                                         "syslinux",
                                                         excluded_partitions)
            if boot_part is None:
                raise CopyError("Could not find partition with 'syslinux' "
                                "folder on device {0}.".format(copier.target.
                                                               device))
            boot_partition = boot_part
        elif boot_partition is None:
            boot_partition = root_partition

        plugins.translate_uuid(copier, boot_partition, "/boot", target_mnt)

        if efi_partition is not None:
            plugins.translate_uuid(copier, efi_partition, "/", target_mnt)
        else:
            if root_partition is None:
                raise CopyError("The syslinux bootloader plugin requires that"
                                " the root partition be defined. The UUIDs of"
                                " the /boot folder have been updated.")
            try:
                mounted_here = False
                mount_point = copier.target.mount_point(root_partition)
                if mount_point is None:
                    copier.target.mount_partition(root_partition, target_mnt)
                    mount_point = target_mnt
                    mounted_here = True
                mount_point += "/" if not target_mnt.endswith("/") else ""
                extlinux_proc = subprocess.Popen(["extlinux", "--install",
                                                  mount_point + "boot/syslinux"
                                                  ],
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)
                extlinux_output, _ = extlinux_proc.communicate()
                if extlinux_proc.returncode != 0:
                    raise CopyError("Error installing bootloader on target "
                                    "drive.",
                                    extlinux_output)
                table_type = copier.target.get_partition_table_type()
                if table_type == "msdos":
                    bios_proc = subprocess.Popen(["dd", "bs=440", "count=1",
                                                  "if={0}usr/lib/syslinux"
                                                  "/bios/mbr.bin".format(
                                                      mount_point),
                                                  "of=" + copier.target.device
                                                  ], stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)
                    output, error = bios_proc.communicate()
                    if bios_proc.returncode != 0:
                        raise DeviceError(copier.target.device,
                                          "Error installing bios to drive.",
                                          output)
                elif table_type == "gpt":
                    attribute_proc = subprocess.Popen(["sgdisk",
                                                       copier.target.device,
                                                       "--attributes=1:set:2"],
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.STDOUT)
                    output, error = attribute_proc.communicate()
                    if attribute_proc.returncode != 0:
                        raise DeviceError(copier.target.device,
                                          "Error enabling boot of partition.",
                                          output)
                    bios_proc = subprocess.Popen(["dd", "conv=notrunc",
                                                  "count=1", "if={0}usr/lib"
                                                  "/syslinux/bios/gptmbr.bin".
                                                  format(mount_point),
                                                  "of=" + copier.target.device
                                                  ], stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)
                    b_output, b_error = bios_proc.communicate()
                    if bios_proc.returncode != 0:
                        raise DeviceError(copier.target.device,
                                          "Error install MBR to drive.",
                                          b_output)
            finally:
                if mounted_here:
                    copier.target.unmount_partition(root_partition)
