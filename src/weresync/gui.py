import weresync.device as device
import gi
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk


DEFAULT_HORIZONTAL_PADDING = 5
DEFAULT_VERTICAL_PADDING = 3

class NumberEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed)

    def on_changed(self, *args):
        text = self.get_text()
        self.set_text("".join([i for i in text if i in "0123456789"]))

class FolderSelectEntry(Gtk.Box):

    def __init__(self, parent=None, *args, **kargs):
        super().__init__(*args, **kargs)
        self.entry = Gtk.Entry()
        self.browse = Gtk.Button(label="Browse")
        self.parent = parent

        self.pack_start(self.entry, True, True, 0)
        self.pack_start(self.browse, True, True, 0)

    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a folder.", self.parent,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                       "Select", Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.entry.set_text

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

class WereSyncWindow(Gtk.Window):
    def __init__(self, title="WereSync"):
        super().__init__(title=title)
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.source_label = Gtk.Label(label="Source Drive: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.source_label.set_hexpand(False)
        #TODO add actually drive names
        name_store = Gtk.ListStore(int, str)
        name_store.append([1, "/dev/sda"])
        name_store.append([2, "/dev/sdb"])
        self.source_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
        self.source_combo.set_hexpand(True)
        self.grid.attach(self.source_label, 1, 1, 1, 1)
        self.grid.attach_next_to(self.source_combo, self.source_label, Gtk.PositionType.RIGHT, 1, 1)
        self.target_label = Gtk.Label(label="Target Drive: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.target_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
        self.target_combo.set_hexpand(True)
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
                                   " enter 1.",
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
        self.excluded_entry = Gtk.Entry()
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

def start_gui():
    win = WereSyncWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
