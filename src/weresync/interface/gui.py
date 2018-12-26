# Copyright 2016 Daniel Manila
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module runs the GUI for WereSync."""

import weresync.plugins as plugins
import weresync.utils as utils
import weresync.daemon.device as device
from weresync.exception import InvalidVersionError
import subprocess
import gi
import sys
import os
import logging
import logging.handlers
import threading
gi.require_version("Gtk", '3.0')
from gi.repository import Gtk, GLib, GObject  # noqa

connected = False

try:
    import weresync.interface.dbus_client as dbus_client
    connected = True
except GLib.GError as ex:
    pass


LOGGER = logging.getLogger(__name__)

DEFAULT_HORIZONTAL_PADDING = 5
DEFAULT_VERTICAL_PADDING = 3


class NumberEntry(Gtk.Entry):
    def __init__(self, allowed="", *args, **kargs):
        """An entry that only allows numbers and certain other characters.

        :param allowed: The other characters allowed by this entry in an
                        unseperated string, ex. '., ' to allow periods, commas,
                        and spaces. Defaults to none."""
        Gtk.Entry.__init__(self, *args, **kargs)
        self.allowed = allowed
        self.connect('changed', self.on_changed)

    def on_changed(self, *args):
        text = self.get_text()
        self.set_text("".join(
            [i for i in text if i in "0123456789" + self.allowed]))


def set_margin(widget,
               right=DEFAULT_HORIZONTAL_PADDING,
               left=DEFAULT_HORIZONTAL_PADDING,
               top=DEFAULT_VERTICAL_PADDING,
               bottom=DEFAULT_VERTICAL_PADDING):
    widget.set_margin_right(right)
    widget.set_margin_left(left)
    widget.set_margin_top(top)
    widget.set_margin_bottom(bottom)


def create_help_box(parent, text, title=""):
    help = Gtk.Label(
        halign=Gtk.Align.START,
        xpad=DEFAULT_HORIZONTAL_PADDING,
        ypad=DEFAULT_VERTICAL_PADDING)
    help.set_markup(_("<a href=\"#\">What's this?</a>"))

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
    proc = subprocess.Popen(
        ["lsblk", "-dnoNAME"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output, _ = proc.communicate()
    if proc.returncode != 0:
        LOGGER.critical("Error reading block list.\n" + output)
    device_list = [
        "/dev/" + x.strip() for x in str(output, "utf-8").split("\n")
        if x.strip() != ""
    ]
    return device_list


def generate_vg_list():
    try:
        lvm_proc = subprocess.Popen(
            ["vgs", "-o", "name", "--noheadings"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        lvm_output, _ = lvm_proc.communicate()
        out = str(lvm_output, "utf-8").split("\n")
        if lvm_proc.returncode != 0:
            LOGGER.critical("Error reading volume group list.\n" +
                            " ".join(out))
        if "No volume groups found" in out:
            lvm_list = ["No volume groups found"]
        else:
            lvm_list = ["/dev/" + x.strip() for x in out if x.strip() != ""]
    except FileNotFoundError as ex:
        # Probably means LVM is not installed on the system, which is no big
        # deal. We'll just log the exception and move on
        LOGGER.debug("File not found info: ", exc_info=sys.exc_info())
        lvm_list = []  # This variable needs to be defined

    return lvm_list


def get_resource(resource):
    dir = os.path.dirname(__file__)
    rel_resource_path = os.path.join(dir, "../resources", resource)
    return os.path.abspath(rel_resource_path)


class WereSyncWindow(Gtk.Window):
    def __init__(self, title="WereSync"):
        super().__init__(title=title)
        # Find all the bootloader plugins available
        manager = plugins.get_manager()
        manager.collectPlugins()
        plugin_store = Gtk.ListStore(int, str, str)
        plugins_added = []
        uuid_index = 0
        for idx, pluginInfo in enumerate(manager.getAllPlugins()):
            manager.activatePluginByName(pluginInfo.name)
            obj = pluginInfo.plugin_object
            if pluginInfo.name not in plugins_added:
                plugin_store.append([idx, obj.prettyName, obj.name])
                plugins_added.append(pluginInfo.name)
                if obj.name == "uuid_copy":
                    uuid_index = idx
            else:
                LOGGER.debug("Not adding {name} at {path} because plugin"
                             "already added".format(
                                 name=pluginInfo.name, path=pluginInfo.path))

        self.set_icon_from_file(get_resource("weresync.svg"))
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.source_label = Gtk.Label(
            label=_("Source Drive: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        name_store = Gtk.ListStore(int, str)
        for idx, val in enumerate(generate_drive_list()):
            name_store.append([idx, val])
        self.source_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
        self.source_combo.set_hexpand(True)
        self.source_combo.set_entry_text_column(1)
        self.grid.attach(self.source_label, 1, 1, 1, 1)
        self.grid.attach_next_to(self.source_combo, self.source_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.target_label = Gtk.Label(
            label=_("Target Drive: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.target_combo = Gtk.ComboBox.new_with_model_and_entry(name_store)
        self.target_combo.set_hexpand(True)
        self.target_combo.set_entry_text_column(1)
        self.grid.attach_next_to(self.target_label, self.source_label,
                                 Gtk.PositionType.BOTTOM, 1, 1)
        self.grid.attach_next_to(self.target_combo, self.target_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        box = Gtk.Box()
        self.grid.attach_next_to(box, self.source_combo,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.lvm_source_label = Gtk.Label(
            label=_("Source VG: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        lvm_list = generate_vg_list()
        lvm_source_store = Gtk.ListStore(int, str)
        for idx, val in enumerate(lvm_list):
            lvm_source_store.append([idx, val])
        self.lvm_source_combo = Gtk.ComboBox.new_with_model_and_entry(
            lvm_source_store)
        self.lvm_source_combo.set_hexpand(True)
        self.lvm_source_combo.set_entry_text_column(1)
        self.lvm_source_combo.set_sensitive(False)
        self.grid.attach_next_to(self.lvm_source_label, box,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.grid.attach_next_to(self.lvm_source_combo, self.lvm_source_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.lvm_target_label = Gtk.Label(
            label=_("Target VG: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        lvm_target_store = Gtk.ListStore(int, str)
        lvm_target_store.append([1, _("Default")])
        for idx, val in enumerate(lvm_list):
            lvm_target_store.append([idx, val])
        self.lvm_target_combo = Gtk.ComboBox.new_with_model_and_entry(
            lvm_target_store)
        self.lvm_target_combo.set_hexpand(True)
        self.lvm_target_combo.set_entry_text_column(1)
        self.lvm_target_combo.set_active(0)
        self.lvm_target_combo.set_sensitive(False)
        self.grid.attach_next_to(self.lvm_target_label, self.lvm_source_label,
                                 Gtk.PositionType.BOTTOM, 1, 1)
        self.grid.attach_next_to(self.lvm_target_combo, self.lvm_target_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.copy_partitions_button = Gtk.CheckButton(
            label=_("Copy partitions if target partitions are invalid."))
        set_margin(self.copy_partitions_button)
        self.grid.attach_next_to(self.copy_partitions_button,
                                 self.target_label, Gtk.PositionType.BOTTOM, 2,
                                 1)
        self.lvm_button = Gtk.CheckButton(
            label=_("Copy Logical Volume Groups."))
        self.lvm_button.connect("toggled", self.lvm_button_toggled)
        self.grid.attach_next_to(self.lvm_button, self.lvm_target_label,
                                 Gtk.PositionType.BOTTOM, 2, 1)
        set_margin(self.lvm_button)
        self.bootloader_label = Gtk.Label(
            label=_("Bootloader Plugin: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.bootloader_combo = Gtk.ComboBox.new_with_model_and_entry(
            plugin_store)
        self.bootloader_combo.set_entry_text_column(1)
        self.bootloader_combo.set_active(uuid_index)
        self.bootloader_help = create_help_box(
            self,
            _("This is the plugin which will attempt to make your clone"
              " bootable. Select the plugin which corresponds to the "
              "bootloader"
              " you want to install. If you are unsure what to choose, pick"
              " 'UUID Copy'."), _("Bootloader Plugin"))
        self.grid.attach_next_to(self.bootloader_label,
                                 self.copy_partitions_button,
                                 Gtk.PositionType.BOTTOM, 1, 1)
        self.grid.attach_next_to(self.bootloader_combo, self.bootloader_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.grid.attach_next_to(self.bootloader_help, self.bootloader_combo,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.bootloader_partition_label = Gtk.Label(
            label=_("Root Partition Number: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.grid.attach_next_to(self.bootloader_partition_label,
                                 self.bootloader_label,
                                 Gtk.PositionType.BOTTOM, 1, 1)
        self.bootloader_partition_entry = NumberEntry()
        self.grid.attach_next_to(self.bootloader_partition_entry,
                                 self.bootloader_partition_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.bootloader_help = create_help_box(
            self,
            _("Enter the partition number of the partition"
              " to install the bootloader on. This is generally the partition "
              "mounted on /\n"
              "So if your root directory is /dev/sda2, enter 2."),
            _("Bootloader Partition"))
        self.grid.attach_next_to(self.bootloader_help,
                                 self.bootloader_partition_entry,
                                 Gtk.PositionType.RIGHT, 1, 1)
        # Start adding advanced options
        self.boot_part_label = Gtk.Label(
            label=_("Boot Partition: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.grid.attach_next_to(self.boot_part_label, self.lvm_button,
                                 Gtk.PositionType.BOTTOM, 1, 1)
        self.boot_part_entry = NumberEntry()
        self.grid.attach_next_to(self.boot_part_entry, self.boot_part_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.boot_help = create_help_box(
            self, _("The number of the partition mounted on /boot."),
            _("Boot Partition"))
        self.grid.attach_next_to(self.boot_help, self.boot_part_entry,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.expander = Gtk.Expander(label=_("Advanced Options"))
        self.efi_partition_label = Gtk.Label(
            label=_("EFI Partition Number: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.grid.attach_next_to(self.efi_partition_label,
                                 self.boot_part_label, Gtk.PositionType.BOTTOM,
                                 1, 1)
        self.efi_partition_entry = NumberEntry()
        self.efi_partition_entry.set_hexpand(True)
        self.grid.attach_next_to(self.efi_partition_entry,
                                 self.efi_partition_label,
                                 Gtk.PositionType.RIGHT, 1, 1)
        self.efi_help = create_help_box(
            self,
            _("Enter the partition number of your EFI partition.\n"
              "So if your efi partition is found on /dev/sda1,"
              " enter 1.\n"
              "If you are not running a UEFI system, leave this blank."),
            _("EFI Partition"))
        self.grid.attach_next_to(self.efi_help, self.efi_partition_entry,
                                 Gtk.PositionType.RIGHT, 1, 1)
        set_margin(self.expander)
        self.expander.set_resize_toplevel(True)
        self.expand_grid = Gtk.Grid()
        self.expander.add(self.expand_grid)
        self.expander.set_hexpand(True)
        self.ignore_errors = Gtk.CheckButton(
            label=_(
                "Ignore errors during copying. If off, common errors often "
                "stop the clone."))
        self.ignore_errors.set_active(True)
        set_margin(self.ignore_errors)
        self.expand_grid.attach(self.ignore_errors, 1, 1, 3, 1)

        self.source_part_mask_label = Gtk.Label(
            label=_("Source Partition Mask: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.source_part_mask_label,
                                        self.ignore_errors,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.source_part_mask_entry = Gtk.Entry()
        self.source_part_mask_entry.set_hexpand(True)
        self.source_part_mask_entry.set_text("{0}{1}")
        self.expand_grid.attach_next_to(self.source_part_mask_entry,
                                        self.source_part_mask_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.part_mask_help = create_help_box(
            self,
            _("A string that controls the how partitions are found on the  "
              "file system. It should have two placeholders: "
              "{0} for the device name and {1} for the partition number.\n"
              "So if you have /dev/loop0 and partition 1 is /dev/loop0p1, the "
              "part_mask should be '{0}p{1}'"), _("Partition Mask"))
        self.expand_grid.attach_next_to(self.part_mask_help,
                                        self.source_part_mask_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.target_part_mask_label = Gtk.Label(
            label=_("Target Partition Mask: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.target_part_mask_label,
                                        self.source_part_mask_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.target_part_mask_entry = Gtk.Entry()
        self.target_part_mask_entry.set_text("{0}{1}")
        self.target_part_mask_entry.set_hexpand(True)
        self.expand_grid.attach_next_to(self.target_part_mask_entry,
                                        self.target_part_mask_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.excluded_label = Gtk.Label(
            label=_("Excluded Partitions: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.excluded_label,
                                        self.target_part_mask_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.excluded_entry = NumberEntry(allowed=", ")
        self.excluded_entry.set_hexpand(True)
        self.expand_grid.attach_next_to(self.excluded_entry,
                                        self.excluded_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.excluded_help = create_help_box(
            self,
            _("A comma separated list of partition numbers that should not be "
              "copied or searched.\n"
              "If partitions partitions are copied, they will still be copied."
              ), _("Excluded Partitions"))
        self.expand_grid.attach_next_to(self.excluded_help,
                                        self.excluded_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)

        self.rsync_label = Gtk.Label(
            label=_("Rsync Arguments: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.rsync_label, self.part_mask_help,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.rsync_entry = Gtk.Entry(text=device.DEFAULT_RSYNC_ARGS)
        self.expand_grid.attach_next_to(self.rsync_entry, self.rsync_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.rsync_help = create_help_box(
            self,
            _("Enter the arguments to pass the rsync program. For more "
              "information see <a href=\"https://download.samba.org/pub/rsync/rsync.html# Options%20Summary\">the rsync website</a>."  # noqa
              ),  # noqa
            _("Rsync Arguments"))
        self.expand_grid.attach_next_to(self.rsync_help, self.rsync_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.source_mount_label = Gtk.Label(
            label=_("Source Drive Mount Point: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.expand_grid.attach_next_to(self.source_mount_label,
                                        self.rsync_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.source_mount_entry = Gtk.FileChooserButton(
            title=_("Source Drive Mount Folder"),
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        self.expand_grid.attach_next_to(self.source_mount_entry,
                                        self.source_mount_label,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.mount_help = create_help_box(
            self,
            _("These are the folders that the drives to be copied will be "
              "mounted in. If unset, WereSync will generate random folders in "
              "the /tmp directory. Generally this can be unset."),
            _("Drive Mount Point."))
        self.expand_grid.attach_next_to(self.mount_help,
                                        self.source_mount_entry,
                                        Gtk.PositionType.RIGHT, 1, 1)
        self.target_mount_label = Gtk.Label(
            label=_("Target Drive Mount Point: "))
        self.expand_grid.attach_next_to(self.target_mount_label,
                                        self.source_mount_label,
                                        Gtk.PositionType.BOTTOM, 1, 1)
        self.target_mount_entry = Gtk.FileChooserButton(
            title=_("Target Drive Mount Folder"),
            action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.expand_grid.attach_next_to(self.target_mount_entry,
                                        self.target_mount_label,
                                        Gtk.PositionType.RIGHT, 1, 1)

        # End advanced options
        self.grid.attach_next_to(self.expander,
                                 self.bootloader_partition_label,
                                 Gtk.PositionType.BOTTOM, 6, 1)
        self.start = Gtk.Button(label=_("Start Clone"))
        set_margin(self.start)
        self.start.set_hexpand(False)
        self.grid.attach(self.start, 6, 10, 1, 1)
        self.start.connect("clicked", self.start_pressed)

    def lvm_button_toggled(self, button):
        if self.lvm_button.get_active():
            self.lvm_source_combo.set_sensitive(True)
            self.lvm_target_combo.set_sensitive(True)
        else:
            self.lvm_source_combo.set_sensitive(False)
            self.lvm_target_combo.set_sensitive(False)

    def set_expander(self, val):
        self.expander.set_expanded(val)

    def get_selected_combo(self, combo):
        combo_iter = combo.get_active_iter()
        if combo_iter is not None:
            model = combo.get_model()
            row_id, val = model[combo_iter][:2]
            return val
        else:
            entry = combo.get_child()
            return entry.get_text()

    def start_pressed(self, *args):
        self.source = self.get_selected_combo(self.source_combo)
        self.target = self.get_selected_combo(self.target_combo)
        is_lvm = self.lvm_button.get_active()
        if is_lvm:
            self.lvm_source = self.get_selected_combo(self.lvm_source_combo)
            lvm_target = self.get_selected_combo(self.lvm_target_combo)
            if lvm_target == _("Default"):
                lvm_target = ""
        else:
            self.lvm_source = ""
            lvm_target = ""
        confirm_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION,
                                           Gtk.ButtonsType.OK_CANCEL, "")
        confirm_dialog.format_secondary_text(
            ("This action will DELETE "
             "everything on {drive} " + (" and {lvm}" if is_lvm else "") +
             ", and make it the "
             "same as the source drives. Is "
             "this what you want to do?").format(
                 drive=self.target, lvm=(lvm_target if is_lvm else "")))
        response = confirm_dialog.run()
        confirm_dialog.destroy()
        if response == Gtk.ResponseType.CANCEL:
            return
        # The user didn't cancel so we can continue running
        copy_if_invalid = self.copy_partitions_button.get_active()
        efi_part = int(self.efi_partition_entry.get_text(
        )) if self.efi_partition_entry.get_text().strip() != "" else -1
        bootloader_part = int(self.bootloader_partition_entry.get_text(
        )) if self.bootloader_partition_entry.get_text() != "" else -1
        ignore_errors = self.ignore_errors.get_active()
        self.source_part_mask = self.source_part_mask_entry.get_text()
        self.target_part_mask = self.target_part_mask_entry.get_text()
        exclude_text = self.excluded_entry.get_text().strip()
        if exclude_text == "":
            excluded_parts = []
        else:
            exclude_text.replace(" ", "")
            excluded_parts = [int(x) for x in exclude_text.split(",")]
        boot_part = int(self.boot_part_entry.get_text()
                        ) if self.boot_part_entry.get_text() != "" else -1
        rsync_args = self.rsync_entry.get_text()
        source_mount = self.source_mount_entry.get_filename()
        target_mount = self.target_mount_entry.get_filename()
        mount_points = (source_mount if source_mount is not None else "",
                        target_mount if target_mount is not None else "")
        boot_iter = self.bootloader_combo.get_active_iter()
        model = self.bootloader_combo.get_model()
        plugin_name = model[boot_iter][2]
        try:
            self._generate_progress_grid()
            self.remove(self.grid)
            self.add(self.progress_grid)

            dbus_client.subscribe_to_signals(
                lambda x: GLib.idle_add(self.part_callback, x),
                lambda num, prog: GLib.idle_add(self.copy_callback, num, prog),
                lambda done: GLib.idle_add(self.boot_callback, done))

            def copy(callback, error):
                try:
                    result = dbus_client.copy_drive(
                        self.source, self.target, copy_if_invalid,
                        self.source_part_mask, self.target_part_mask,
                        excluded_parts, ignore_errors, bootloader_part,
                        boot_part, efi_part, mount_points, rsync_args,
                        self.lvm_source, lvm_target, plugin_name)
                    callback(result)
                except Exception as ex:
                    LOGGER.debug(
                        "Full exception info:\n", exc_info=sys.exc_info())
                    error(ex)

            copy_thread = threading.Thread(
                target=copy,
                args=[
                    lambda result: GLib.idle_add(self._copy_finished, result),
                    lambda ex: GLib.idle_add(self._show_error, ex)
                ])
            copy_thread.start()
            self.show_all()
        except Exception as ex:
            LOGGER.debug("Full exception info:\n", exc_info=sys.exc_info())
            self._show_error(ex)
            return

    def _show_error(self, ex):
        """Displays an error in a message dialog."""
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.OK,
                                   _("Error starting clone."))
        dialog.format_secondary_text(str(ex))
        dialog.run()
        dialog.destroy()

        # Sets back to original screen to allow regenerating any misplace
        # parameters.
        self.remove(self.progress_grid)
        self.add(self.grid)

    def _copy_finished(self, result):
        """A callback function to be run when the the drive finishes
        copying."""
        text = _("Clone finished!")
        if result is not True:
            text += _("\nNon fatal error occurred: ") + str(result)

        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK, text)
        dialog.run()
        dialog.destroy()
        self.remove(self.progress_grid)
        self.add(self.grid)

    def _generate_progress_grid(self):
        """Generates the grid for the screen showing progress. Sets
        `self.progress_grid` as the grid.`"""

        self.progress_grid = Gtk.Grid()
        part_label = Gtk.Label(
            label=_("Checking partitions and copying: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.progress_grid.attach(part_label, 1, 1, 1, 1)
        self.part_progress = Gtk.ProgressBar()
        set_margin(self.part_progress)
        self.progress_grid.attach_next_to(self.part_progress, part_label,
                                          Gtk.PositionType.RIGHT, 1, 1)
        self.copy_progresses = {}

        def create_partitions(device, device_part_mask, start_label,
                              lvm=False):
            previous_label = start_label
            partitions = dbus_client.drive_copier.GetPartitions(
                device, device_part_mask, lvm)
            for val in partitions:
                copy_label = Gtk.Label(
                    label=_("Copying partition {0}: ").format(val),
                    halign=Gtk.Align.START,
                    xpad=DEFAULT_HORIZONTAL_PADDING,
                    ypad=DEFAULT_VERTICAL_PADDING)
                copy_progress = Gtk.ProgressBar()
                set_margin(copy_progress)
                self.progress_grid.attach_next_to(
                    copy_label, previous_label, Gtk.PositionType.BOTTOM, 1, 1)
                self.progress_grid.attach_next_to(copy_progress, copy_label,
                                                  Gtk.PositionType.RIGHT, 1, 1)
                self.copy_progresses[val] = copy_progress
                previous_label = copy_label

            return previous_label

        final_label = create_partitions(self.source, self.source_part_mask,
                                        part_label)
        if self.lvm_button.get_active():
            final_label = create_partitions(
                self.lvm_source, "", final_label, lvm=True)

        boot_label = Gtk.Label(
            label=_("Making bootable: "),
            halign=Gtk.Align.START,
            xpad=DEFAULT_HORIZONTAL_PADDING,
            ypad=DEFAULT_VERTICAL_PADDING)
        self.progress_grid.attach_next_to(boot_label, final_label,
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
        LOGGER.debug("part callback. Value: {0}".format(progress))
        self.part_progress.set_fraction(progress)

    def copy_callback(self, part, progress):
        part = str(int(part))
        if progress < 0:
            LOGGER.debug(
                "Error occurred copying partition {0}. Marking complete.".
                format(part))
            self.copy_progresses[part].set_fraction(1.0)
        elif progress is True and isinstance(progress, bool):
            self.copy_progresses[part].pulse()
        elif (progress >= self.copy_progresses[part].get_fraction()):
            self.copy_progresses[part].set_fraction(progress)

    def boot_callback(self, done):
        if not done:
            self.boot_progress.pulse()
        else:
            self.boot_progress.set_fraction(1.0)


def start_gui():

    utils.enable_localization()

    try:
        utils.check_python_version()
    except InvalidVersionError as ex:
        print(ex)
        # This might not work, if the user doesn't have a setup that support
        # PyGObject, but it's worth a shot.
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.OK,
                                   _("Error starting WereSync."))
        dialog.format_secondary_text(str(ex))
        dialog.run()
        dialog.destroy()
        sys.exit(1)

    utils.start_logging_handler(utils.DEFAULT_USER_LOG_LOCATION)

    if not connected:
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.OK,
                                   _("Error starting WereSync."))
        dialog.format_secondary_text(_("Weresync service not connected."))
        dialog.run()
        dialog.destroy()
        sys.exit(1)

    LOGGER.info(_("Starting gui."))
    GObject.threads_init()
    win = WereSyncWindow()
    win.connect("delete-event", Gtk.main_quit)
    # This is set to expanded so it will be centered as if advanced options
    # were opened
    win.set_expander(True)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.show_all()
    # Then advanced options are closed so as not to be distracting
    win.set_expander(False)
    win.show_all()
    Gtk.main()
