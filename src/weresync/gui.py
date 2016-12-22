import weresync.device as device
import weresync.interface as interface
import subprocess
import gi
import sys
import os
import logging
import logging.handlers
import threading
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk, GLib, GObject

LOGGER = logging.getLogger(__name__)

DEFAULT_HORIZONTAL_PADDING = 5
DEFAULT_VERTICAL_PADDING = 3

class NumberEntry(Gtk.Entry):
    def __init__(self, allowed="", *args, **kargs):
        """An entry that only allows numbers and certain other characters.

        :param allowed: The other characters allowed by this entry in an unseperated string, ex. '., ' to allow periods, commas, and spaces. Defaults to none."""
        Gtk.Entry.__init__(self, *args, **kargs)
        self.allowed = allowed
        self.connect('changed', self.on_changed)

    def on_changed(self, *args):
        text = self.get_text()
        self.set_text("".join([i for i in text if i in "0123456789" + self.allowed]))

def set_margin(widget, right=DEFAULT_HORIZONTAL_PADDING,
               left=DEFAULT_HORIZONTAL_PADDING,
               top=DEFAULT_VERTICAL_PADDING,
               bottom=DEFAULT_VERTICAL_PADDING):
    widget.set_margin_right(right)
    widget.set_margin_left(left)
    widget.set_margin_top(top)
    widget.set_margin_bottom(bottom)

def create_help_box(parent, text, title=""):
    help = Gtk.Label(halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
    help.set_markup("<a href=\"#\">What's this?</a>")
    def help_click(*args):
        dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK, title)
        dialog.format_secondary_text(text)
        dialog.set_default_size(parent.get_size()[0], -1)
        dialog.run()
        dialog.destroy()
        return True

    help.connect("activate-link", help_click)
    return help

def generate_drive_list():
    proc = subprocess.Popen(["lsblk", "-dnoNAME"], stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    if proc.returncode != 0:
        #TODO issue error
        pass
    return ["/dev/" + x.strip() for x in str(output, "utf-8").split("\n") if x.strip() != ""]

def get_resource(resource):
    dir = os.path.dirname(__file__)
    rel_resource_path = os.path.join(dir, "..", "resources", resource)
    return os.path.abspath(rel_resource_path)

class WereSyncWindow(Gtk.Window):
    def __init__(self, title="WereSync"):
        super().__init__(title=title)
        self.set_icon_from_file(get_resource("weresync.svg"))
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.source_label = Gtk.Label(label="Source Drive: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.source_label.set_hexpand(False)
        #TODO add actually drive names
        name_store = Gtk.ListStore(int, str)
        for idx, val in enumerate(generate_drive_list()):
            name_store.append([idx, val])
        self.source_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
        self.source_combo.set_hexpand(True)
        self.source_combo.set_entry_text_column(1)
        self.grid.attach(self.source_label, 1, 1, 1, 1)
        self.grid.attach_next_to(self.source_combo, self.source_label, Gtk.PositionType.RIGHT, 1, 1)
        self.target_label = Gtk.Label(label="Target Drive: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.target_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
        self.target_combo.set_hexpand(True)
        self.target_combo.set_entry_text_column(1)
        self.grid.attach_next_to(self.target_label, self.source_label, Gtk.PositionType.BOTTOM, 1, 1)
        self.grid.attach_next_to(self.target_combo, self.target_label, Gtk.PositionType.RIGHT, 1, 1)
        self.copy_partitions_button = Gtk.CheckButton(label="Copy partitions if target partitions are invalid.")
        set_margin(self.copy_partitions_button)
        self.grid.attach_next_to(self.copy_partitions_button, self.target_label, Gtk.PositionType.BOTTOM, 2, 1)
        self.efi_partition_label = Gtk.Label(label="EFI Partition Number: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.grid.attach_next_to(self.efi_partition_label, self.copy_partitions_button,
                            Gtk.PositionType.BOTTOM, 1, 1)
        self.efi_partition_entry = NumberEntry()
        self.efi_partition_entry.set_hexpand(True)
        self.grid.attach_next_to(self.efi_partition_entry, self.efi_partition_label, Gtk.PositionType.RIGHT, 1, 1)
        self.efi_help = create_help_box(self, "Enter the partition number of your EFI partition.\n"
                                   "So if your efi partition is found on /dev/sda1,"
                                   " enter 1.\n"
                                    "If you are not running a UEFI system, leave this blank.",
                                   "EFI Partition")
        self.grid.attach_next_to(self.efi_help, self.efi_partition_entry, Gtk.PositionType.RIGHT, 1, 1)
        self.bootloader_partition_label = Gtk.Label(label="Bootloader Partition Number: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.grid.attach_next_to(self.bootloader_partition_label, self.efi_partition_label, Gtk.PositionType.BOTTOM,
                            1, 1)
        self.bootloader_partition_entry = NumberEntry()
        self.grid.attach_next_to(self.bootloader_partition_entry, self.bootloader_partition_label, Gtk.PositionType.RIGHT, 1, 1)
        self.bootloader_help = create_help_box(self, "Enter the partition number of the partition"
                                    " to install the bootloader on. This is generally the partition mounted on /\n"
                                    "So if your root directory is /dev/sda2, enter 2.",
                                    "Bootloader Partition")
        self.grid.attach_next_to(self.bootloader_help, self.bootloader_partition_entry, Gtk.PositionType.RIGHT, 1, 1)
        #Start adding advanced options
        self.expander = Gtk.Expander(label="Advanced Options")
        set_margin(self.expander)
        self.expander.set_resize_toplevel(True)
        self.expand_grid = Gtk.Grid()
        self.expander.add(self.expand_grid)
        self.expander.set_hexpand(True)
        self.ignore_errors = Gtk.CheckButton(label="Ignore errors during copying. If off, common errors often stop the clone.")
        self.ignore_errors.set_active(True)
        set_margin(self.ignore_errors)
        self.expand_grid.attach(self.ignore_errors, 1, 1, 3, 1)

        self.source_part_mask_label = Gtk.Label(label="Source Partition Mask: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.source_part_mask_label, self.ignore_errors,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.source_part_mask_entry = Gtk.Entry()
        self.source_part_mask_entry.set_hexpand(True)
        self.source_part_mask_entry.set_text("{0}{1}")
        self.expand_grid.attach_next_to(self.source_part_mask_entry,
                                        self.source_part_mask_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.part_mask_help = create_help_box(self, "A string that controls the how partitions are found on the file system. It should have two placeholders: "
                                              "{0} for the device name and {1} for the partition number.\n"
                                              "So if you have /dev/loop0 and partition 1 is /dev/loop0p1, the part_mask should be '{0}p{1}'",
        "Partition Mask")
        self.expand_grid.attach_next_to(self.part_mask_help, self.source_part_mask_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.target_part_mask_label = Gtk.Label(label="Target Partition Mask: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.target_part_mask_label,
                                        self.source_part_mask_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.target_part_mask_entry = Gtk.Entry()
        self.target_part_mask_entry.set_text("{0}{1}")
        self.target_part_mask_entry.set_hexpand(True)
        self.expand_grid.attach_next_to(self.target_part_mask_entry,
                                        self.target_part_mask_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.excluded_label = Gtk.Label(label="Excluded Partitions: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.excluded_label, self.target_part_mask_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.excluded_entry = NumberEntry(allowed=", ")
        self.excluded_entry.set_hexpand(True)
        self.expand_grid.attach_next_to(self.excluded_entry, self.excluded_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.excluded_help = create_help_box(self, "A comma separated list of partition numbers that should not be copied or searched.\n"
                                             "If partitions partitions are copied, they will still be copied.",
        "Excluded Partitions")
        self.expand_grid.attach_next_to(self.excluded_help, self.excluded_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)

        self.boot_part_label = Gtk.Label(label="Boot Partition: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.boot_part_label, self.excluded_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.boot_part_entry = NumberEntry()
        self.expand_grid.attach_next_to(self.boot_part_entry, self.boot_part_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.boot_help = create_help_box(self, "The number of the partition mounted on /boot.",
                                         "Boot Partition")
        self.expand_grid.attach_next_to(self.boot_help, self.boot_part_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.rsync_label = Gtk.Label(label="Rsync Arguments: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.rsync_label, self.boot_part_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.rsync_entry = Gtk.Entry(text=device.DEFAULT_RSYNC_ARGS)
        self.expand_grid.attach_next_to(self.rsync_entry, self.rsync_label, Gtk.PositionType.RIGHT, 1, 1)
        self.rsync_help = create_help_box(self, "Enter the arguments to pass the rsync program. For more information see <a href=\"https://download.samba.org/pub/rsync/rsync.html#Options%20Summary\">the rsync website</a>.",
                                          "Rsync Arguments")
        self.expand_grid.attach_next_to(self.rsync_help, self.rsync_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.source_mount_label = Gtk.Label(label="Source Drive Mount Point: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.source_mount_label, self.rsync_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.source_mount_entry = Gtk.FileChooserButton(title="Source Drive Mount Folder",
                                       action=Gtk.FileChooserAction.SELECT_FOLDER,)
        self.expand_grid.attach_next_to(self.source_mount_entry, self.source_mount_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.mount_help = create_help_box(self, "These are the folders that the drives to be copied will be mounted in. If unset, WereSync will generate random folders in the /tmp directory. Generally this can be unset.", "Drive Mount Point.")
        self.expand_grid.attach_next_to(self.mount_help, self.source_mount_entry, Gtk.PositionType.RIGHT, 1, 1)
        self.target_mount_label = Gtk.Label(label="Target Drive Mount Point: ")
        self.expand_grid.attach_next_to(self.target_mount_label, self.source_mount_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.target_mount_entry = Gtk.FileChooserButton(title="Target Drive Mount Folder", action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.expand_grid.attach_next_to(self.target_mount_entry, self.target_mount_label,
                                        Gtk.PositionType.RIGHT, 1, 1)

        #End advanced options
        self.grid.attach_next_to(self.expander, self.bootloader_partition_label, Gtk.PositionType.BOTTOM, 3, 1)
        self.start = Gtk.Button(label="Start Clone")
        set_margin(self.start)
        self.start.set_hexpand(False)
        self.grid.attach(self.start, 3, 10, 1, 1)
        self.start.connect("clicked", self.start_pressed)

    def set_expander(self, val):
        self.expander.set_expanded(val)

    def get_selected_combo(self, combo):
        combo_iter = combo.get_active_iter()
        if combo_iter != None:
            model = combo.get_model()
            row_id, val = model[combo_iter][:2]
            return val
        else:
            entry = combo.get_child()
            return entry.get_text()

    def start_pressed(self, *args):
        self.source = self.get_selected_combo(self.source_combo)
        self.target = self.get_selected_combo(self.target_combo)
        copy_if_invalid = self.copy_partitions_button.get_active()
        efi_part = int(self.efi_partition_entry.get_text()) if self.efi_partition_entry.get_text().strip() != "" else None
        bootloader_part = int(self.bootloader_partition_entry.get_text()) if self.bootloader_partition_entry.get_text() != "" else None
        ignore_errors = self.ignore_errors.get_active()
        self.source_part_mask = self.source_part_mask_entry.get_text()
        self.target_part_mask = self.target_part_mask_entry.get_text()
        exclude_text = self.excluded_entry.get_text().strip()
        if exclude_text == "":
            excluded_parts = []
        else:
            exclude_text.replace(" ", "")
            excluded_parts = [int(x) for x in exclude_text.split(",")]
        boot_part = int(self.boot_part_entry.get_text()) if self.boot_part_entry.get_text() != "" else None
        rsync_args = self.rsync_entry.get_text()
        mount_points = (self.source_mount_entry.get_filename(),
                        self.target_mount_entry.get_filename())
        try:
            self._generate_progress_grid()
            self.remove(self.grid)
            self.add(self.progress_grid)
            def copy(callback, error):
                try:
                    result = interface.copy_drive(self.source, self.target, copy_if_invalid,
                                         self.source_part_mask, self.target_part_mask,
                                         excluded_parts, ignore_errors, bootloader_part,
                                         boot_part, efi_part, mount_points, rsync_args,
                                         lambda x: GLib.idle_add(self.part_callback, x),
                                         lambda num, prog: GLib.idle_add(self.copy_callback, num, prog),
                                         lambda done: GLib.idle_add(self.boot_callback, done))
                    callback(result)
                except Exception as ex:
                    LOGGER.debug("Full exception info:\n", exc_info=sys.exc_info())
                    error(ex)

            copy_thread = threading.Thread(target=copy,
                                           args=[lambda result: GLib.idle_add(self._copy_finished, result),
                                                 lambda ex: GLib.idle_add(self._show_error, ex)])
            copy_thread.start()
            self.show_all()
        except Exception as ex:
            LOGGER.debug("Full exception info:\n", exc_info=sys.exc_info())
            self._show_error(ex)
            return

    def _show_error(self, ex):
        """Displays an error in a message dialog."""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.OK, "Error starting clone.")
        dialog.format_secondary_text(str(ex))
        dialog.run()
        dialog.destroy()

        #Sets back to original screen to allow regenerating any misplace parameters.
        self.remove(self.progress_grid)
        self.add(self.grid)

    def _copy_finished(self, result):
        """A callback function to be run when the the drive finishes copying."""
        text = "Clone finished!"
        if result != True:
            text += "\nNon fatal error occurred: " + str(result)

        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK, text)
        dialog.run()
        dialog.destroy()
        self.remove(self.progress_grid)
        self.add(self.grid)

    def _generate_progress_grid(self):
        """Generates the grid for the screen showing progress. Sets `self.progress_grid` as the grid.`"""

        self.progress_grid = Gtk.Grid()
        part_label = Gtk.Label(label="Checking partitions and copying: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.progress_grid.attach(part_label, 1, 1, 1, 1)
        self.part_progress = Gtk.ProgressBar()
        set_margin(self.part_progress)
        self.progress_grid.attach_next_to(self.part_progress, part_label, Gtk.PositionType.RIGHT,
                            1, 1)
        source_manager = device.DeviceManager(self.source, self.source_part_mask)
        self.copy_progresses = {}
        partitions = source_manager.get_partitions()
        previous_label = part_label
        for val in partitions:
            copy_label = Gtk.Label(label="Copying partition {0}: ".format(val), halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
            copy_progress = Gtk.ProgressBar()
            set_margin(copy_progress)
            self.progress_grid.attach_next_to(copy_label, previous_label, Gtk.PositionType.BOTTOM,
                                1, 1)
            self.progress_grid.attach_next_to(copy_progress, copy_label, Gtk.PositionType.RIGHT,
                                1, 1)
            self.copy_progresses[val] = copy_progress
            previous_label = copy_label
        boot_label = Gtk.Label(label="Making bootable: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.progress_grid.attach_next_to(boot_label, previous_label,
                                          Gtk.PositionType.BOTTOM, 1, 1)
        self.boot_progress = Gtk.ProgressBar()
        set_margin(self.boot_progress)
        self.progress_grid.attach_next_to(self.boot_progress, boot_label,
                                          Gtk.PositionType.RIGHT, 1, 1)
        self.cancel_btn = Gtk.Button(label="Cancel")
        set_margin(self.cancel_btn)
        self.progress_grid.attach_next_to(self.cancel_btn, self.boot_progress,
                                          Gtk.PositionType.BOTTOM, 1, 1)

    def part_callback(self, progress):
        LOGGER.debug("part callback. Value: {0}".format(progress) )
        self.part_progress.set_fraction(progress)

    def copy_callback(self, part, progress):
        #LOGGER.debug("copy callback value: {0}, part {1}".format(progress, part))
        if progress < 0:
            LOGGER.debug("Error occurred copying partition {0}. Marking complete.".format(part))
            self.copy_progresses[part].set_fraction(1.0)
        elif progress == True and isinstance(progress, bool):
            self.copy_progresses[part].pulse()
        elif (progress >= self.copy_progresses[part].get_fraction()):
            self.copy_progresses[part].set_fraction(progress)

    def boot_callback(self, done):
        if not done:
            self.boot_progress.pulse()
        else:
            self.boot_progress.set_fraction(1.0)

def start_gui():
    #interface.start_logging_handler(LOGGER)
    interface.start_logging_handler()
    #logging.basicConfig(level=logging.INFO)
    LOGGER.info("Starting gui.")
    GObject.threads_init()
    win = WereSyncWindow()
    win.connect("delete-event", Gtk.main_quit)
    #This is set to expanded so it will be centered as if advanced options wer e opened
    win.set_expander(True)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.show_all()
    #Then advanced options are closed so as not to be distracting
    win.set_expander(False)
    win.show_all()
    Gtk.main()
