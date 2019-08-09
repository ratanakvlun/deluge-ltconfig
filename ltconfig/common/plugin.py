#
# plugin.py
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


import os
import pkg_resources
import gettext

from . import util


_ = gettext.gettext

PLUGIN_NAME = "ltConfig"
MODULE_NAME = "ltconfig"
DISPLAY_NAME = _("ltConfig")

LOG_HANDLER = util.PrefixHandler("[%s] " % PLUGIN_NAME)


class PrefixFilter(object):
  def filter(self, record):
    record.msg = "[%s] %s" % (PLUGIN_NAME, record.msg)
    return True

prefix_filter = PrefixFilter()


def get_resource(filename):
  return pkg_resources.resource_filename(
      MODULE_NAME, os.path.join("data", filename))
