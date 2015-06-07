#
# core.py
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


from deluge._libtorrent import lt as libtorrent


from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export


from common.plugin import (
  PLUGIN_NAME, MODULE_NAME,
  LOG_HANDLER,
)



CONFIG_FILE = "%s.conf" % MODULE_NAME

DEFAULT_PREFS = {
  "apply_on_start": False,
  "settings": {},
}



log = logging.getLogger(__name__)
log.addHandler(LOG_HANDLER)



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
  def get_settings(self):

    log.debug("Get settings")

    return self._get_session_settings(self._session)


  @export
  def get_original_settings(self):

    log.debug("Get original settings")

    return dict(self._initial_settings)


  @export
  def get_preset(self, preset):

    log.debug("Get preset")

    settings_obj = None

    if preset == 1:
      if hasattr(libtorrent, "high_performance_seed"):
        settings_obj = libtorrent.high_performance_seed()
    elif preset == 2:
      if hasattr(libtorrent, "min_memory_usage"):
        settings_obj = libtorrent.min_memory_usage()

    settings = self._convert_from_libtorrent_settings(settings_obj)

    for key in settings.keys():
      if settings[key] == self._initial_settings[key]:
        del settings[key]

    return settings


  @export
  def set_preferences(self, preferences):

    log.debug("Set preferences")

    self._config["apply_on_start"] = preferences["apply_on_start"]

    settings = preferences["settings"]
    self._normalize_settings(settings)

    old_settings = dict(self._settings)
    self._settings.clear()
    self._settings.update(settings)

    self._config.save()

    for key in old_settings:
      if key not in settings:
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


  def _convert_from_libtorrent_settings(self, settings_obj):

    settings = {}

    for k in dir(settings_obj):
      if k.startswith("_") or k == "peer_tos":
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


  def _get_session_settings(self, session):

    return self._convert_from_libtorrent_settings(session.settings())


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
      else:
        val_type = type(self._initial_settings[k])
        try:
          settings[k] = val_type(settings[k])
        except TypeError, ValueError:
          settings[k] = self._initial_settings[k]


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
