ltConfig
========

ltConfig is a plugin for [Deluge](http://deluge-torrent.org) that
allows direct modification to libtorrent settings and has preset support.

This plugin adds a preference page to both GtkUI and WebUI.

WARNING: Modify settings at your own risk!

For information about each setting, see the libtorrent [reference](https://www.rasterbar.com/products/libtorrent/reference.html) and [tuning guide](https://www.rasterbar.com/products/libtorrent/tuning-ref.html).
NOTE: Older versions of libtorrent may have different setting names.

Building
--------

To build this plugin, you'll need [Python](https://www.python.org/) and the `setuptools` module. Instructions for installing `setuptools` can be found [here](https://packaging.python.org/tutorials/installing-packages/#install-pip-setuptools-and-wheel).

To build the plugin, run:
```
python setup.py bdist_egg
```

This will produce a `dist` directory containing the plugin egg.
