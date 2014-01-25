#
# gtkui.py
#
# Copyright (C) 2014 Ratanak Lun <ratanakvlun@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#



import logging


import gobject
import gtk
import gtk.glade


from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component


from common import PLUGIN_NAME
from common import DISPLAY_NAME
from common import get_resource
from common import prefix_filter



log = logging.getLogger(__name__)
log.addFilter(prefix_filter)



class GtkUI(GtkPluginBase):


  def __init__(self, plugin_name):

    super(GtkUI, self).__init__(plugin_name)
    self._initialized = False


  def enable(self):

    log.debug("Enabling GtkUI...")

    self._ui = gtk.glade.XML(get_resource("wnd_preferences.glade"))

    self._blk_prefs = self._ui.get_widget("blk_preferences")
    self._lbl_ver = self._ui.get_widget("lbl_version")
    self._chk_apply_on_start = self._ui.get_widget("chk_apply_on_start")
    self._blk_view = self._ui.get_widget("blk_view")

    self._view = self._build_view()
    window = gtk.ScrolledWindow()
    window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    window.add(self._view)
    self._blk_view.add(window)

    self._blk_prefs.show_all()

    client.core.get_libtorrent_version().addCallback(self._do_update_version)
    client.ltconfig.get_original_settings().addCallback(self._do_complete_init)


  def _do_complete_init(self, settings):

    self._initial_settings = settings

    self._row_map = {}
    self._build_model(self._initial_settings)

    component.get("Preferences").add_page(DISPLAY_NAME, self._blk_prefs)
    component.get("PluginManager").register_hook(
        "on_apply_prefs", self._do_save_preferences)
    component.get("PluginManager").register_hook(
        "on_show_prefs", self._do_load_preferences)

    self._initialized = True

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

    col = gtk.TreeViewColumn()
    view.append_column(col)

    cr = gtk.CellRendererToggle()
    cr.set_property("xpad", 4)
    cr.connect("toggled", self._do_enable_toggled, model, 0)
    col.pack_start(cr)
    col.set_cell_data_func(cr, self._render_cell, "toggle")

    col = gtk.TreeViewColumn(_("Name"), gtk.CellRendererText(), text=1)
    view.append_column(col)

    col = gtk.TreeViewColumn(_("Setting"))
    view.append_column(col)

    cr = gtk.CellRendererText()
    cr.set_property("xalign", 0.0)
    cr.connect("edited", self._do_edited, model, 2)
    col.pack_start(cr)
    col.set_attributes(cr, editable=0, sensitive=0)
    col.set_cell_data_func(cr, self._render_cell, "text")

    cr = gtk.CellRendererToggle()
    cr.set_property("xalign", 0.0)
    cr.connect("toggled", self._do_toggled, model, 2)
    col.pack_start(cr)
    col.set_attributes(cr, activatable=0, sensitive=0)
    col.set_cell_data_func(cr, self._render_cell, "toggle")

    col = gtk.TreeViewColumn(_("Actual"))
    view.append_column(col)

    cr = gtk.CellRendererText()
    cr.set_property("xalign", 0.0)
    col.pack_start(cr)
    col.set_cell_data_func(cr, self._render_cell, "text")

    cr = gtk.CellRendererToggle()
    cr.set_property("xalign", 0.0)
    col.pack_start(cr)
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
        cell.set_property("text", value)

    elif cell_type == "toggle":
      if val_type != bool:
        visible = False
      else:
        cell.set_property("active", value)

    else:
      visible = False

    cell.set_property("visible", visible)


  def _do_update_version(self, version):

    self._lbl_ver.set_label(version)


  def _do_save_preferences(self):

    log.debug("Save preferences")

    if not self._initialized:
      log.debug("Not initialized")
      return

    settings = {}

    for row in self._view.get_model():
      if row[0]:
        settings[row[1]] = row[2]

    preferences = {
      "settings": settings,
      "apply_on_start": self._chk_apply_on_start.get_active(),
    }

    client.ltconfig.set_preferences(preferences)


  def _do_load_preferences(self):

    log.debug("Load preferences")

    if not self._initialized:
      log.debug("Not initialized")
      return

    client.ltconfig.get_preferences().addCallback(self._update_preferences)


  def _update_preferences(self, preferences):

    self._chk_apply_on_start.set_active(preferences["apply_on_start"])

    settings = preferences["settings"]
    model = self._view.get_model()

    for key in settings:
      model.set(self._row_map[key], 0, True, 2, settings[key])

    client.ltconfig.get_settings().addCallback(self._update_actual_values)


  def _update_actual_values(self, settings):

    model = self._view.get_model()

    for key in settings:
      model.set(self._row_map[key], 3, settings[key])
