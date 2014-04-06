/*
Script: ltconfig.js
    The client-side javascript code for the ltConfig plugin.

Copyright:
    (C) Ratanak Lun 2014 <ratanakvlun@gmail.com>
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, write to:
        The Free Software Foundation, Inc.,
        51 Franklin Street, Fifth Floor
        Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
*/


Ext.namespace('Deluge.plugins.ltconfig');
Ext.namespace('Deluge.plugins.ltconfig.ui');
Ext.namespace('Deluge.plugins.ltconfig.util');


if (typeof(console) === 'undefined') {
  console = {
    log: function() {}
  };
}


Deluge.plugins.ltconfig.PLUGIN_NAME = 'ltConfig';
Deluge.plugins.ltconfig.MODULE_NAME = 'ltconfig';
Deluge.plugins.ltconfig.DISPLAY_NAME = _('ltConfig');


Deluge.plugins.ltconfig.util.dictLength = function(dict) {
  var i = 0;

  for (key in dict) {
    if (dict.hasOwnProperty(key)) {
      i++;
    }
  }

  return i;
};


Deluge.plugins.ltconfig.util.dictEquals = function(a, b) {
  if (a === b) {
    return true;
  }

  if (Deluge.plugins.ltconfig.util.dictLength(a) !=
      Deluge.plugins.ltconfig.util.dictLength(b)) {
    return false;
  }

  for (key in a) {
    if (!a.hasOwnProperty(key)) {
      continue;
    }

    if (!b.hasOwnProperty(key) || a[key] != b[key]) {
      return false;
    }
  }

  return true;
};


Deluge.plugins.ltconfig.ui.PreferencePage = Ext.extend(Ext.Panel, {

  title: Deluge.plugins.ltconfig.DISPLAY_NAME,

  layout: {
    type: 'vbox',
    align: 'stretch'
  },

  initComponent: function() {
    Deluge.plugins.ltconfig.ui.PreferencePage.superclass.initComponent.call(
      this);

    this.chkApplyOnStart = this.add({
      xtype: 'checkbox',
      margins: '0 5 5 5',
      boxLabel: _('Apply settings on startup')
    });

    this.lblVersion = this.add({
      xtype: 'label',
      margins: '5 5 5 5',
      caption: _('libtorrent version') + ": ",
      text: _('libtorrent version') + ": ?",
    });

    this.tblSettings = this.add({
      xtype: 'editorgrid',
      flex: 1,
      autoExpandColumn: 'name',

      viewConfig: {
        emptyText: _("Loading...")
      },

      colModel: new Ext.grid.ColumnModel({
        defaults: {
          renderer: function(value, meta, record, rowIndex, colIndex, store) {
            if (colIndex == 3 || !record.get('enabled')) {
              meta.attr = 'style="color: gray;"';
            }

            if (typeof(value) == 'number' && !(parseInt(value) === value)) {
              return value.toFixed(6);
            } else if (typeof(value) === 'boolean') {
              return '<div class="x-grid3-check-col' + (value ? '-on' : '') +
                '" style="width: 20px;">&#160;</div>';
            }

            return value;
          }
        },

        columns: [
          {
            id: 'enabled',
            header: '',
            dataIndex: 'enabled',
            sortable: true,
            hideable: false,
            width: 30,
          },
          {
            id: 'name',
            header: _("Name"),
            dataIndex: 'name',
            sortable: true,
            hideable: false,
          },
          {
            id: 'setting',
            header: _("Setting"),
            dataIndex: 'setting',
            hideable: false,
            width: 60,
            editor: {
              xtype: 'textfield',
              allowBlank: false,
            },
          },
          {
            id: 'actual',
            header: _("Actual"),
            dataIndex: 'actual',
            width: 60,
          }
        ]
      }),

      store: new Ext.data.ArrayStore({
        autoDestroy: true,

        fields: [
          {name: 'enabled'},
          {name: 'name'},
          {name: 'setting'},
          {name: 'actual'}
        ]
      }),

      listeners: {
        viewready: function(store, records, options) {
          this.getView().refresh();
        },

        cellclick: function(grid, rowIndex, colIndex, e) {
          var record = grid.getStore().getAt(rowIndex);
          var field = grid.getColumnModel().getDataIndex(colIndex);
          var value = record.get(field);

          if (colIndex == 0 || (record.get('enabled') && colIndex == 2)) {
            if (typeof(value) === 'boolean') {
              record.set(field, !value);

              if (colIndex == 0 && !record.get('enabled')) {
                record.set('setting',
                  this.initialSettings[record.get('name')]);
              }

              record.commit();
            }
          }
        },

        beforeedit: function(e) {
          if (typeof(e.value) === 'boolean') {
            return false;
          }

          return e.record.get('enabled');
        },

        afteredit: function(e) {
          e.record.commit();
        }
      }
    });

    deluge.client.on('connected', this.loadBaseState, this);
  },

  loadBaseState: function() {
    deluge.client.core.get_libtorrent_version({
      success: function(version) {
        this.lblVersion.text = this.lblVersion.caption + version;
      },
      scope: this
    });

    deluge.client.ltconfig.get_original_settings({
      success: function(settings) {
        this.tblSettings.initialSettings = settings;

        var keys = Ext.keys(settings).sort();
        var data = [];

        for (var i = 0; i < keys.length; i++) {
          key = keys[i]
          data.push([false, key, settings[key], settings[key]]);
        }

        this.tblSettings.getStore().loadData(data);
      },
      scope: this
    });
  },

  loadPrefs: function() {
    if (!deluge.preferences.isVisible()) {
      return;
    }

    deluge.client.ltconfig.get_preferences({
      success: function(prefs) {
        this.preferences = prefs;
        this.chkApplyOnStart.setValue(prefs['apply_on_start']);

        var settings = prefs['settings'];
        var store = this.tblSettings.getStore();

        for (var i = 0; i < store.getCount(); i++) {
          var record = store.getAt(i);
          var name = record.get('name');

          if (name in settings) {
            record.set('enabled', true);
            record.set('setting', settings[name]);
            record.commit();
          } else if (record.get('enabled')) {
            record.set('enabled', false);
            record.commit();
          }
        }
      },
      scope: this
    });

    deluge.client.ltconfig.get_settings({
      success: function(settings) {
        var store = this.tblSettings.getStore();

        for (var i = 0; i < store.getCount(); i++) {
          var record = store.getAt(i);
          var name = record.get('name');

          if (name in settings) {
            record.set('actual', settings[name]);
            record.commit();
          }
        }
      },
      scope: this
    });
  },

  savePrefs: function() {
    var settings = {};
    var store = this.tblSettings.getStore();
    var apply = false;

    for (var i = 0; i < store.getCount(); i++) {
      var record = store.getAt(i);
      var name = record.get('name');

      if (record.get('enabled')) {
        settings[name] = record.get('setting');
        apply |= record.get('setting') != record.get('actual');
      }
    }

    var prefs = {
      apply_on_start: this.chkApplyOnStart.getValue(),
      settings: settings
    };

    apply |= prefs['apply_on_start'] != this.preferences['apply_on_start'];
    apply |= !Deluge.plugins.ltconfig.util.dictEquals(prefs['settings'],
      this.preferences['settings']);

    if (apply) {
      deluge.client.ltconfig.set_preferences(prefs, {
        success: this.loadPrefs,
        scope: this
      });
    }
  }
});


Deluge.plugins.ltconfig.Plugin = Ext.extend(Deluge.Plugin, {

  name: Deluge.plugins.ltconfig.PLUGIN_NAME,

  onEnable: function() {
    this.prefsPage = new Deluge.plugins.ltconfig.ui.PreferencePage();
    deluge.preferences.addPage(this.prefsPage);

    deluge.preferences.on('show', this.prefsPage.loadPrefs, this.prefsPage);
    deluge.preferences.buttons[2].on('click', this.prefsPage.savePrefs,
      this.prefsPage);

    console.log(Deluge.plugins.ltconfig.PLUGIN_NAME + " enabled");
  },

  onDisable: function() {
    deluge.preferences.removePage(this.prefsPage);

    deluge.preferences.un('show', this.prefsPage.loadPrefs, this.prefsPage);
    deluge.preferences.buttons[2].un('click', this.prefsPage.savePrefs,
      this.prefsPage);

    console.log(Deluge.plugins.ltconfig.PLUGIN_NAME + " disabled");
  }
});

Deluge.registerPlugin(Deluge.plugins.ltconfig.PLUGIN_NAME,
  Deluge.plugins.ltconfig.Plugin);
