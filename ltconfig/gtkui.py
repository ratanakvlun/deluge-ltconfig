#
# gtkui.py
#
# Copyright (C) 2013 Ratanak Lun <ratanakvlun@gmail.com>
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


  def enable(self):

    log.debug("Enabling GtkUI...")

    self._modified = False

    self._ui = gtk.glade.XML(get_resource("wnd_preferences.glade"))

    self._blk_prefs = self._ui.get_widget("blk_preferences")
    self._lbl_ver = self._ui.get_widget("lbl_version")
    self._chk_apply_on_start = self._ui.get_widget("chk_apply_on_start")
    self._blk_view = self._ui.get_widget("blk_view")

    self._view = self._build_view()
    frame = gtk.Frame()
    frame.add(self._view)
    self._blk_view.add(frame)

    self._blk_prefs.show_all()

    component.get("Preferences").add_page(DISPLAY_NAME, self._blk_prefs)
    component.get("PluginManager").register_hook(
        "on_apply_prefs", self._do_save_preferences)
    component.get("PluginManager").register_hook(
        "on_show_prefs", self._do_load_preferences)

    client.core.get_libtorrent_version().addCallback(self._do_update_version)
    self._do_load_preferences()

    log.debug("GtkUI enabled")


  def disable(self):

    log.debug("Disabling GtkUI...")

    component.get("Preferences").remove_page(DISPLAY_NAME)
    component.get("PluginManager").deregister_hook(
        "on_apply_prefs", self._do_save_preferences)
    component.get("PluginManager").deregister_hook(
        "on_show_prefs", self._do_load_preferences)

    log.debug("GtkUI disabled")


  def _build_view(self):

    model = gtk.ListStore(str, gobject.TYPE_PYOBJECT)
    view = gtk.TreeView(model)

    col = gtk.TreeViewColumn(_("Name"), gtk.CellRendererText(), text=0)
    view.append_column(col)

    col = gtk.TreeViewColumn(_("Value"))
    view.append_column(col)

    cr = gtk.CellRendererText()
    cr.set_property("editable", True)
    cr.set_property("xalign", 0.0)
    cr.connect("edited", self._do_edited, model)
    col.pack_start(cr)
    col.set_cell_data_func(cr, self._render_cell, "text")

    cr = gtk.CellRendererToggle()
    cr.set_property("xalign", 0.0)
    cr.connect("toggled", self._do_toggled, model)
    col.pack_start(cr)
    col.set_cell_data_func(cr, self._render_cell, "toggle")

    return view


  def _update_view(self, settings):

    model = self._view.get_model()
    model.clear()

    for k in sorted(settings):
      model.append((k, settings[k]))

    self._modified = False


  def _do_edited(self, cell, path, text, model):

    value = model[path][1]
    val_type = type(value)

    model[path][1] = val_type(text)

    self._modified = True


  def _do_toggled(self, cell, path, model):

    model[path][1] = not model[path][1]

    self._modified = True


  def _render_cell(self, col, cell, model, iter, cell_type):

    name = model[iter][0]
    value = model[iter][1]
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

    if self._modified:
      log.debug("Save preferences")

      settings = {}

      for row in self._view.get_model():
        settings[row[0]] = row[1]

      preferences = {
        "settings": settings,
        "apply_on_start": self._chk_apply_on_start.get_active(),
      }

      client.ltconfig.set_preferences(preferences)

      self._modified = False


  def _do_load_preferences(self):

    log.debug("Load preferences")

    client.ltconfig.get_preferences().addCallback(self._update_preferences)
    client.ltconfig.get_settings().addCallback(self._update_view)


  def _update_preferences(self, preferences):

    self._chk_apply_on_start.set_active(preferences["apply_on_start"])
