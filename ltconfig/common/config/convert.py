#
# convert.py
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


import copy

from ..util import (
  update_dict, get_path_mapped_dict,
)


#
# spec format:
# {
#   "version_in": version of input config data,
#   "version_out": version of output config data,
#   "defaults": dict of defaults for the target output version,
#   "strict": whether or not invalid paths cause exceptions,
#   "deepcopy": whether or not to deepcopy when copying values,
#   "pre_func": called before mapping, void pre_func(spec, dict),
#   "post_func": called after mapping, void post_func(spec, dict),
#   "map": {
#     "path/variable": "path/variable",
#   },
# }
#


def convert(spec, config):

  version_in = spec["version_in"]
  version_out = spec["version_out"]

  if config._Config__version["file"] != version_in:
    raise ValueError("Unable to convert because version mismatch")

  input = config.config
  output = process_spec(spec, input)

  config._Config__version["file"] = version_out
  config._Config__config = output


def process_spec(spec, dict_in):

  # Pre function meant for mapping preparations
  pre_func = spec.get("pre_func")
  if pre_func:
    pre_func(spec, dict_in)

  # Mapping meant for excluding unused keys or remapping keys
  working_dict = {}
  if spec.get("map"):
    if spec["map"]["*"] == "*":
      working_dict = dict_in
    else:
      for src, dest in sorted(spec["map"].items(),
          key=lambda x: x[1].count("/")):
        mapped = get_path_mapped_dict(dict_in, src, dest,
          spec["deepcopy"], spec["strict"])
        update_dict(working_dict, mapped)

    # Post function meant for altering values
    post_func = spec.get("post_func")
    if post_func:
      post_func(spec, working_dict)

  # Make sure any missing keys are in the final dict
  dict_out = copy.deepcopy(spec["defaults"])
  update_dict(dict_out, working_dict)

  return dict_out
