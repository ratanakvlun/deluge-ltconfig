#
# gtkui.py
#
# Copyright (C) 2015 Ratanak Lun <ratanakvlun@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Linking this software with other modules is making a combined work
# based on this software. Thus, the terms and conditions of the GNU
# General Public License cover the whole combination.
#
# As a special exception, the copyright holders of this software give
# you permission to link this software with independent modules to
# produce a combined work, regardless of the license terms of these
# independent modules, and to copy and distribute the resulting work
# under terms of your choice, provided that you also meet, for each
# linked module in the combined work, the terms and conditions of the
# license of that module. An independent module is a module which is
# not derived from or based on this software. If you modify this
# software, you may extend this exception to your version of the
# software, but you are not obligated to do so. If you do not wish to
# do so, delete this exception statement from your version.
#


import logging


from gi.repository import GObject as gobject
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk

from twisted.internet import reactor


from deluge.ui.client import client
from deluge.plugins.pluginbase import Gtk3PluginBase
import deluge.component as component


from .common.plugin import (
  PLUGIN_NAME, DISPLAY_NAME,
  LOG_HANDLER, get_resource,
)

from .common.util import (
  dict_equals,
)



log = logging.getLogger(__name__)
log.addHandler(LOG_HANDLER)



class GtkUI(Gtk3PluginBase):


  def __init__(self, plugin_name):

    super(GtkUI, self).__init__(plugin_name)
    self._initialized = False


  def enable(self):

    log.debug("Enabling GtkUI...")

    self._ui = gtk.Builder.new_from_file(get_resource("wnd_preferences.ui"))

    self._blk_prefs = self._ui.get_object("blk_preferences")
    self._lbl_ver = self._ui.get_object("lbl_version")
    self._chk_apply_on_start = self._ui.get_object("chk_apply_on_start")
    self._blk_view = self._ui.get_object("blk_view")

    self._presets = self._ui.get_object("presets")
    self._presets.set_active(0)
    self._load_preset = self._ui.get_object("load_preset")
    self._load_preset.connect("clicked", self._do_load_preset)

    self._view = self._build_view()
    window = gtk.ScrolledWindow()
    window.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
    window.set_shadow_type(gtk.ShadowType.IN)
    window.add(self._view)
    self._blk_view.add(window)

    self._blk_prefs.show_all()

    client.core.get_libtorrent_version().addCallback(self._do_update_version)
    client.ltconfig.get_original_settings().addCallback(self._do_complete_init)


  def _do_complete_init(self, settings):

    self._initial_settings = settings
    self._prefs = {}

    self._row_map = {}
    self._build_model(self._initial_settings)

    component.get("Preferences").add_page(DISPLAY_NAME, self._blk_prefs)
    component.get("PluginManager").register_hook(
        "on_apply_prefs", self._do_save_preferences)
    component.get("PluginManager").register_hook(
        "on_show_prefs", self._do_load_preferences)

    self._initialized = True

    self._do_load_preferences()

    log.debug("GtkUI enabled")


  def disable(self):

    log.debug("Disabling GtkUI...")

    self._initialized = False

    component.get("Preferences").remove_page(DISPLAY_NAME)
    component.get("PluginManager").deregister_hook(
        "on_apply_prefs", self._do_save_preferences)
    component.get("PluginManager").deregister_hook(
        "on_show_prefs", self._do_load_preferences)

    log.debug("GtkUI disabled")


  def _build_view(self):

    model = gtk.ListStore(bool, str,
      gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
    view = gtk.TreeView(model)


    def on_button_pressed(widget, event):

      if event.button != gdk.BUTTON_PRIMARY or event.type != gdk.EventType.BUTTON_PRESS:
        return False

      x, y = event.get_coords()
      path_info = widget.get_path_at_pos(int(x), int(y))
      if not path_info:
        return False

      path = path_info[0]
      column = path_info[1]

      if widget.get_model()[path][0] and column is widget.get_column(2):
        widget.set_cursor(path, column, start_editing=True)
        return True


    view.connect("button-press-event", on_button_pressed)
    view.get_selection().set_mode(gtk.SelectionMode.NONE)
    view.set_search_column(1)

    col = gtk.TreeViewColumn()
    view.append_column(col)

    cr = gtk.CellRendererToggle()
    cr.set_property("xpad", 4)
    cr.connect("toggled", self._do_enable_toggled, model, 0)
    col.pack_start(cr, False)
    col.set_cell_data_func(cr, self._render_cell, "toggle")

    col = gtk.TreeViewColumn(_("Name"), gtk.CellRendererText(), \
      text=1, sensitive=0)
    col.set_resizable(True)
    view.append_column(col)

    col = gtk.TreeViewColumn(_("Setting"))
    col.set_resizable(True)
    view.append_column(col)

    cr = gtk.CellRendererText()
    cr.set_property("xalign", 0.0)
    cr.connect("edited", self._do_edited, model, 2)
    col.pack_start(cr, False)
    col.set_attributes(cr, editable=0, sensitive=0)
    col.set_cell_data_func(cr, self._render_cell, "text")

    cr = gtk.CellRendererToggle()
    cr.set_property("xalign", 0.0)
    cr.connect("toggled", self._do_toggled, model, 2)
    col.pack_start(cr, False)
    col.set_attributes(cr, activatable=0, sensitive=0)
    col.set_cell_data_func(cr, self._render_cell, "toggle")

    col = gtk.TreeViewColumn(_("Actual"))
    col.set_resizable(True)
    view.append_column(col)

    cr = gtk.CellRendererText()
    cr.set_property("sensitive", False)
    cr.set_property("xalign", 0.0)
    col.pack_start(cr, False)
    col.set_cell_data_func(cr, self._render_cell, "text")

    cr = gtk.CellRendererToggle()
    cr.set_property("sensitive", False)
    cr.set_property("xalign", 0.0)
    col.pack_start(cr, False)
    col.set_cell_data_func(cr, self._render_cell, "toggle")

    return view


  def _build_model(self, settings):

    model = self._view.get_model()
    model.clear()
    map = {}

    for k in sorted(settings):
      map[k] = model.append((False, k, settings[k], settings[k]))

    self._row_map = map


  def _do_edited(self, cell, path, text, model, column):

    value = model[path][column]
    val_type = type(value)

    model[path][column] = val_type(text)


  def _do_toggled(self, cell, path, model, column):

    model[path][column] = not model[path][column]


  def _do_enable_toggled(self, cell, path, model, column):

    name = model[path][1]

    if model[path][column]:
      model[path][2] = self._initial_settings[name]

    model[path][column] = not model[path][column]


  def _render_cell(self, col, cell, model, iter, cell_type):

    for i, column in enumerate(col.get_tree_view().get_columns()):
      if col == column: break

    value = model[iter][i]
    val_type = type(value)
    visible = True

    if cell_type == "text":
      if val_type == bool:
        visible = False
      elif val_type == float:
        cell.set_property("text", "%f" % value)
      else:
        cell.set_property("text", "%s" % value)

    elif cell_type == "toggle":
      if val_type != bool:
        visible = False
      else:
        cell.set_property("active", value)

    else:
      visible = False

    cell.set_property("visible", visible)


  def _do_update_version(self, version):

    parts = version.split('.')
    if int(parts[0]) < 1 and int(parts[1]) < 16:
      model = self._presets.get_model()
      del model[2]
      del model[1]

    self._lbl_ver.set_label(version)


  def _do_load_preset(self, button):

    log.debug("Loading preset...")

    index = self._presets.get_active()
    if index > -1:
        log.debug("Option=%d", index)
        client.ltconfig.get_preset(index).addCallback(self._load_settings)
    else:
        log.debug("No preset selected...")


  def _do_save_preferences(self):

    log.debug("Save preferences")

    if not self._initialized:
      log.debug("Not initialized")
      return

    settings = {}
    apply_ = False

    for row in self._view.get_model():
      if row[0]:
        settings[row[1]] = row[2]
        apply_ |= row[2] != row[3]

    preferences = {
      "settings": settings,
      "apply_on_start": self._chk_apply_on_start.get_active(),
    }

    apply_ |= not dict_equals(preferences, self._prefs)

    if apply_:
      client.ltconfig.set_preferences(preferences)
    else:
      log.debug("No settings were changed")


  def _do_load_preferences(self):

    log.debug("Load preferences")

    if not self._initialized:
      log.debug("Not initialized")
      return

    client.ltconfig.get_preferences().addCallback(self._update_preferences)


  def _update_preferences(self, preferences):

    self._prefs = preferences

    self._chk_apply_on_start.set_active(preferences["apply_on_start"])
    self._load_settings(preferences["settings"])

    client.ltconfig.get_settings().addCallback(self._update_actual_values)


  def _load_settings(self, settings):

    model = self._view.get_model()

    for key in self._initial_settings:
      if key in settings:
        model.set(self._row_map[key], 0, True, 2, settings[key])
        continue

      model.set(self._row_map[key], 0, False, 2, self._initial_settings[key])


  def _update_actual_values(self, settings):

    model = self._view.get_model()

    for key in settings:
      model.set(self._row_map[key], 3, settings[key])
