#
# core.py
#
# Copyright (C) 2017 Ratanak Lun <ratanakvlun@gmail.com>
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


import re
import logging

from deluge._libtorrent import lt as libtorrent
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

from .common.plugin import (
  PLUGIN_NAME, MODULE_NAME,
  LOG_HANDLER,
)

from .common.config.file import init_config
from .common.config.plugin import (
  CONFIG_VERSION, CONFIG_DEFAULTS, CONFIG_SPECS,
)

from .common.presets import (
  LIBTORRENT_DEFAULTS, MIN_MEMORY_USAGE, HIGH_PERFORMANCE_SEED
)


CONFIG_FILE = "%s.conf" % MODULE_NAME

log = logging.getLogger(__name__)
log.addHandler(LOG_HANDLER)


SETTING_EXCLUSIONS = [
  "peer_tos"
]

# Settings that should be floats before 1.1.x.
DEPRECATED_FLOATS = [
  "peer_turnover",
  "peer_turnover_cutoff",
  "seed_time_ratio_limit",
  "share_ratio_limit"
]

NETWORK_SERVICES = ["dht", "lsd", "natpmp", "upnp"]


def merged_dict(a, b):
  dict_a = dict(a)
  dict_b = dict(b)
  for key, value in dict_b.items():
    dict_a[key] = value
  return dict_a

class Core(CorePluginBase):

  def __init__(self, plugin_name):

    super(Core, self).__init__(plugin_name)

    self._config = None


  def enable(self):

    log.debug("Enabling Core...")

    self._session = component.get("Core").session
    self._config = deluge.configmanager.ConfigManager(
        CONFIG_FILE, CONFIG_DEFAULTS)

    self._initial_settings = self._get_session_settings(self._session)
    self._default_settings = self.get_preset(1)

    self._settings = self._config["settings"]
    self._normalize_settings(self._settings)

    if self._config["apply_on_start"]:
      self._apply_settings(self._settings)

    log.debug("Core enabled")


  def _load_config(self):

    config = deluge.configmanager.ConfigManager(CONFIG_FILE)

    old_ver = init_config(config, CONFIG_DEFAULTS,
      CONFIG_VERSION, CONFIG_SPECS)

    if old_ver != CONFIG_VERSION:
      log.debug("Config file converted: v%s -> v%s", old_ver, CONFIG_VERSION)

    return config


  def disable(self):

    log.debug("Disabling Core...")

    if self._config:
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

    log.debug("Get preset %d" % preset)

    settings = {}

    if preset == 1:
      settings = dict(LIBTORRENT_DEFAULTS)
    elif preset == 2:
      settings = dict(HIGH_PERFORMANCE_SEED)
    elif preset == 3:
      settings = dict(MIN_MEMORY_USAGE)
    elif preset == 4:
      settings = merged_dict(LIBTORRENT_DEFAULTS, HIGH_PERFORMANCE_SEED)
    elif preset == 5:
      settings = merged_dict(LIBTORRENT_DEFAULTS, MIN_MEMORY_USAGE)

    for key in list(settings.keys()):
      # Presets use integer values in place of floats (for >= 1.1.x).
      # Need to convert to float for earlier versions.
      if key in DEPRECATED_FLOATS and \
          (libtorrent.version_major < 1 or \
          (libtorrent.version_major == 1 and libtorrent.version_minor < 1)):
        settings[key] = settings[key] / 100.0

      if key not in self._initial_settings or settings[key] == self._initial_settings[key]:
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


  def _convert_from_libtorrent_settings(self, settings_obj, prefix=""):

    settings = {}

    if type(settings_obj) == dict:
      for k in settings_obj:
        name = prefix + k

        if name in SETTING_EXCLUSIONS:
          continue

        settings[name] = settings_obj[k]

      return settings

    for k in dir(settings_obj):
      name = prefix + k

      if k.startswith("_") or name in SETTING_EXCLUSIONS:
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

      settings[name] = v

    return settings


  def _convert_to_libtorrent_settings(self, settings, settings_obj, prefix=""):

    for name in settings:
      if not name.startswith(prefix):
        continue

      k = re.sub(r"^%s" % re.escape(prefix), "", name)

      if type(settings_obj) == dict:
        if k in settings_obj:
          settings_obj[k] = settings[name]
      else:
        if k in dir(settings_obj):
          val_type = type(getattr(settings_obj, k))
          v = val_type(settings[name])

          setattr(settings_obj, k, v)


  def _get_session_settings(self, session):

    if hasattr(session, "get_settings"):
      settings_obj = session.get_settings()
    else:
      settings_obj = session.settings()

    settings = self._convert_from_libtorrent_settings(settings_obj)

    if hasattr(session, "get_dht_settings"):
      dht_settings = self._convert_from_libtorrent_settings(
        session.get_dht_settings(), "dht.")
      settings.update(dht_settings)

    return settings


  def _set_session_settings(self, session, settings):

    if hasattr(session, "get_settings"):
      settings_obj = session.get_settings()
    else:
      settings_obj = session.settings()

    self._convert_to_libtorrent_settings(settings, settings_obj)

    if hasattr(session, "apply_settings"):
      session.apply_settings(settings_obj)
    else:
      session.set_settings(settings_obj)

    if hasattr(session, "get_dht_settings"):
      settings_obj = session.get_dht_settings()
      self._convert_to_libtorrent_settings(settings, settings_obj, "dht.")
      session.set_dht_settings(settings_obj)

    self._stop_network_services()
    self._start_network_services()


  def _normalize_settings(self, settings):

    for k in settings.keys():
      if k not in self._initial_settings:
        del settings[k]
      else:
        val_type = type(self._initial_settings[k])
        try:
          settings[k] = val_type(settings[k])
        except (TypeError, ValueError):
          settings[k] = self._initial_settings[k]


  def _apply_settings(self, settings):

    self._set_session_settings(self._session, settings)


  def _start_network_services(self):
    config = component.get("PreferencesManager").config

    for service in NETWORK_SERVICES:
      if config[service]:
        method = getattr(self._session, "start_%s" % service, None)
        if method:
          method()


  def _stop_network_services(self):
    config = component.get("PreferencesManager").config

    for service in NETWORK_SERVICES:
      if config[service]:
        method = getattr(self._session, "stop_%s" % service, None)
        if method:
          method()


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
