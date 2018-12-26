from pydbus import SystemBus
from gi.repository import GLib
import threading
import gi.repository.GLib

try:
    bus = SystemBus()
    drive_copier = bus.get("net.manilas.weresync.DriveCopier")
    copy_drive = drive_copier.CopyDrive
    error = None
except gi.repository.GLib.Error as e:
    error = e
    copy_drive = False


def _unthreaded_subscribe_to_signals(
        partition_status_callback, copy_status_callback, boot_status_callback):
    drive_copier.PartitionStatus.connect(partition_status_callback)
    drive_copier.CopyStatus.connect(copy_status_callback)
    drive_copier.BootStatus.connect(boot_status_callback)
    loop = GLib.MainLoop()
    loop.run()


def subscribe_to_signals(partition_status_callback, copy_status_callback,
                         boot_status_callback):
    thread = threading.Thread(
        target=_unthreaded_subscribe_to_signals,
        args=(partition_status_callback, copy_status_callback,
              boot_status_callback))
    thread.daemon = True
    thread.start()
