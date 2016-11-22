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
        dialog = Gtk.Dialog(title, parent)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        info = Gtk.Label(text, halign=Gtk.Align.CENTER, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        dialog.get_content_area().pack_start(info, True, True, 0)
        dialog.set_modal(True)
        dialog.show_all()
        answer = dialog.run()
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
        self.boot_partition_label = Gtk.Label(label="Boot Partition Number: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
        self.grid.attach_next_to(self.boot_partition_label, self.efi_partition_label, Gtk.PositionType.BOTTOM,
                            1, 1)
        self.boot_partition_entry = NumberEntry()
        self.grid.attach_next_to(self.boot_partition_entry, self.boot_partition_label, Gtk.PositionType.RIGHT, 1, 1)
        self.boot_help = create_help_box(self, "Enter the partition number of the partition"
                                    " to install the bootloader on. This is generally the partition mounted on /\n"
                                    "So if your root directory is /dev/sda2, enter 2.",
                                    "Boot Partition")
        self.grid.attach_next_to(self.boot_help, self.boot_partition_entry, Gtk.PositionType.RIGHT, 1, 1)
        self.expander = Gtk.Expander(label="Advanced Options")
        set_margin(self.expander)
        self.expander.set_resize_toplevel(True)
        self.expand_grid = Gtk.Grid()
        self.expander.add(self.expand_grid)
        test = Gtk.Label(label="test")
        self.expand_grid.add(test)
        self.expander.set_hexpand(True)
        self.grid.attach_next_to(self.expander, self.boot_partition_label, Gtk.PositionType.BOTTOM, 1, 1)
        self.start = Gtk.Button(label="Start Clone")
        set_margin(self.start)
        self.start.set_hexpand(False)
        self.grid.attach(self.start, 3, 10, 1, 1)

def start_gui():
    win = WereSyncWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
