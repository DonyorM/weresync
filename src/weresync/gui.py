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

def start_gui():
    win = Gtk.Window(title="WereSync")
    win.connect("delete-event", Gtk.main_quit)
    grid = Gtk.Grid()
    win.add(grid)
    source_label = Gtk.Label(label="Source Drive: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
    source_label.set_hexpand(False)
    #TODO add actually drive names
    name_store = Gtk.ListStore(int, str)
    name_store.append([1, "/dev/sda"])
    name_store.append([2, "/dev/sdb"])
    source_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
    source_combo.set_hexpand(True)
    grid.attach(source_label, 1, 1, 1, 1)
    grid.attach_next_to(source_combo, source_label, Gtk.PositionType.RIGHT, 1, 1)
    target_label = Gtk.Label(label="Target Drive: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
    target_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
    target_combo.set_hexpand(True)
    grid.attach_next_to(target_label, source_label, Gtk.PositionType.BOTTOM, 1, 1)
    grid.attach_next_to(target_combo, target_label, Gtk.PositionType.RIGHT, 1, 1)
    copy_partitions_button = Gtk.CheckButton(label="Copy partitions if target partitions are invalid.")
    set_margin(copy_partitions_button)
    grid.attach_next_to(copy_partitions_button, target_label, Gtk.PositionType.BOTTOM, 2, 1)
    efi_partition_label = Gtk.Label(label="EFI Partition Number: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
    grid.attach_next_to(efi_partition_label, copy_partitions_button,
                        Gtk.PositionType.BOTTOM, 1, 1)
    efi_partition_entry = NumberEntry()
    efi_partition_entry.set_hexpand(True)
    grid.attach_next_to(efi_partition_entry, efi_partition_label, Gtk.PositionType.RIGHT, 1, 1)
    efi_help = create_help_box(win, "Enter the partition number of your EFI partition.\n"
                               "So if your efi partition is found on /dev/sda1,"
                               " enter 1.",
                               "EFI Partition")
    grid.attach_next_to(efi_help, efi_partition_entry, Gtk.PositionType.RIGHT, 1, 1)
    boot_partition_label = Gtk.Label(label="Boot Partition Number: ", halign=Gtk.Align.START, xpad=DEFAULT_HORIZONTAL_PADDING, ypad=DEFAULT_VERTICAL_PADDING)
    grid.attach_next_to(boot_partition_label, efi_partition_label, Gtk.PositionType.BOTTOM,
                        1, 1)
    boot_partition_entry = NumberEntry()
    grid.attach_next_to(boot_partition_entry, boot_partition_label, Gtk.PositionType.RIGHT, 1, 1)
    boot_help = create_help_box(win, "Enter the partition number of the partition"
                                " to install the bootloader on. This is generally the partition mounted on /\n"
                                "So if your root directory is /dev/sda2, enter 2.",
                                "Boot Partition")
    grid.attach_next_to(boot_help, boot_partition_entry, Gtk.PositionType.RIGHT, 1, 1)
    expander = Gtk.Expander(label="Advanced Options")
    set_margin(expander)
    expander.set_resize_toplevel(True)
    expand_grid = Gtk.Grid()
    expander.add(expand_grid)
    test = Gtk.Label(label="test")
    expand_grid.add(test)
    expander.set_hexpand(True)
    grid.attach_next_to(expander, boot_partition_label, Gtk.PositionType.BOTTOM, 1, 1)
    start = Gtk.Button(label="Start Clone")
    set_margin(start)
    start.set_hexpand(False)
    grid.attach(start, 3, 10, 1, 1)
    win.show_all()
    Gtk.main()
