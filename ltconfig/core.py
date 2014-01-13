#
# core.py
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


import libtorrent


from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export


from common import PLUGIN_NAME
from common import MODULE_NAME
from common import prefix_filter



CONFIG_FILE = "%s.conf" % MODULE_NAME

DEFAULT_PREFS = {
  "apply_on_start": False,
  "settings": {},
}



log = logging.getLogger(__name__)
log.addFilter(prefix_filter)



class Core(CorePluginBase):


  def enable(self):

    log.debug("Enabling Core...")

    self._session = component.get("Core").session
    self._config = deluge.configmanager.ConfigManager(
        CONFIG_FILE, DEFAULT_PREFS)

    self._initial_settings = self._get_session_settings(self._session)

    self._settings = self._config["settings"]
    self._normalize_settings(self._settings)

    if self._config["apply_on_start"]:
      self._apply_settings(self._settings)

    log.debug("Core enabled")


  def disable(self):

    log.debug("Disabling Core...")

    self._config.save()
    deluge.configmanager.close(CONFIG_FILE)

    self._rpc_deregister(PLUGIN_NAME)

    log.debug("Core disabled")


  @export
  def set_settings(self, settings):

    log.debug("Set settings")

    self._normalize_settings(settings)

    self._settings.update(settings)
    self._config.save()

    self._apply_settings(self._settings)


  @export
  def get_settings(self):

    log.debug("Get settings")

    settings = self._get_session_settings(self._session)

    return settings


  @export
  def get_original_settings(self):

    log.debug("Get original settings")

    return dict(self._initial_settings)


  @export
  def set_preferences(self, preferences):

    log.debug("Set preferences")

    self._config["apply_on_start"] = preferences["apply_on_start"]

    settings = preferences["settings"]
    self._normalize_settings(settings)

    self._settings.clear()
    self._settings.update(settings)

    self._config.save()

    for key in self._initial_settings:
      if key not in settings.keys():
        settings[key] = self._initial_settings[key]

    self._apply_settings(settings)


  @export
  def get_preferences(self):

    log.debug("Get preferences")

    preferences = {
      "apply_on_start": self._config["apply_on_start"],
      "settings": dict(self._settings),
    }

    return preferences


  def _get_session_settings(self, session):

    settings = {}
    settings_obj = session.settings()

    for k in dir(settings_obj):
      if k.startswith("_"):
        continue

      try:
        v = getattr(settings_obj, k)
      except TypeError:
        continue

      val_type = type(v)
      if val_type.__module__ == "libtorrent":
        try:
          v = int(v)
        except ValueError:
          continue

      settings[k] = v

    return settings


  def _set_session_settings(self, session, settings):

    settings_obj = session.settings()

    for k in dir(settings_obj):
      if k.startswith("_"):
        continue

      if k in settings:
        val_type = type(getattr(settings_obj, k))
        v = val_type(settings[k])

        setattr(settings_obj, k, v)

    session.set_settings(settings_obj)


  def _normalize_settings(self, settings):

    for k in settings.keys():
      if k not in self._initial_settings:
        del settings[k]


  def _apply_settings(self, settings):

    for k, v in settings.iteritems():
      if isinstance(v, unicode):
        try:
          settings[k] = str(v)
        except UnicodeEncodeError:
          del settings[k]

    self._set_session_settings(self._session, settings)


  def _rpc_deregister(self, name):

    server = component.get("RPCServer")
    name = name.lower()

    for d in dir(self):
      if d[0] == "_": continue

      if getattr(getattr(self, d), '_rpcserver_export', False):
        method = "%s.%s" % (name, d)
        if method in server.factory.methods:
          log.debug("Deregistering method: %s", method)
          del server.factory.methods[method]
