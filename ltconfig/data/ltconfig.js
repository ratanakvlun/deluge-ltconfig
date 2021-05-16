/*
Script: ltconfig.js
    The client-side javascript code for the ltConfig plugin.

Copyright:
    (C) Ratanak Lun 2017 <ratanakvlun@gmail.com>
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

  for (var key in dict) {
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

  for (var key in a) {
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

    var caption = _('libtorrent version') + ': ';
    this.lblVersion = this.add({
      xtype: 'label',
      margins: '5 5 5 5',
      caption: caption,
      text: caption + '?'
    });

    this.presetsContainer = this.add({
      xtype: 'container',
      layout: 'hbox',
      margins: '0 5 8 5',
      items: [{
        xtype: 'combo',
        margins: '0 8 0 0',
        mode: 'local',
        store: [
          [0, 'Pre-ltConfig Settings'],
          [1, 'Libtorrent Defaults'],
          [2, 'High Performance Seed'],
          [3, 'Minimum Memory Usage'],
          [4, 'Libtorrent Defaults + High Performance Seed'],
          [5, 'Libtorrent Defaults + Minimum Memory Usage']
        ],
        value: 0,
        editable: false,
        triggerAction: 'all',
        flex: 2
      }, {
        xtype: 'button',
        text: 'Load Preset'
      }]
    });

    this.tblSettings = this.add({
      xtype: 'editorgrid',
      margins: '0 5 0 5',
      flex: 1,
      autoExpandColumn: 'name',

      viewConfig: {
        emptyText: _('Loading settings...'),
        deferEmptyText: false
      },

      colModel: new Ext.grid.ColumnModel({
        defaults: {
          renderer: function(value, meta, record, rowIndex, colIndex, store) {
            if (colIndex == 3 || !record.get('enabled')) {
              meta.attr = 'style="color: gray;"';
            }

            if (Ext.isNumber(value) && parseInt(value) !== value) {
              return value.toFixed(6);
            } else if (Ext.isBoolean(value)) {
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
            menuDisabled: true
          },
          {
            id: 'name',
            header: _('Name'),
            dataIndex: 'name',
            sortable: true,
            hideable: false
          },
          {
            id: 'setting',
            header: _('Setting'),
            dataIndex: 'setting',
            hideable: false,
            width: 60,
            editor: {
              xtype: 'textfield'
            }
          },
          {
            id: 'actual',
            header: _('Actual'),
            dataIndex: 'actual',
            width: 60
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
        cellclick: function(grid, rowIndex, colIndex, e) {
          var record = grid.getStore().getAt(rowIndex);
          var field = grid.getColumnModel().getDataIndex(colIndex);
          var value = record.get(field);

          if (colIndex == 0 || (record.get('enabled') && colIndex == 2)) {
            if (Ext.isBoolean(value)) {
              record.set(field, !value);

              if (colIndex == 0 && !record.get('enabled')) {
                record.set('setting', this.baseSettings[record.get('name')]);
              }

              record.commit();
            }
          }
        },

        beforeedit: function(e) {
          if (Ext.isBoolean(e.value)) {
            return false;
          }

          return e.record.get('enabled');
        },

        afteredit: function(e) {
          e.record.commit();
        }
      },

      setEmptyText: function(text) {
        if (this.viewReady) {
          this.getView().emptyText = text;
          this.getView().refresh();
        } else {
          Ext.apply(this.viewConfig, {emptyText: text});
        }
      },

      loadData: function(data) {
        this.getStore().loadData(data);
        if (this.viewReady) {
          this.getView().updateHeaders();
        }
      }
    });

    this.presetsContainer.getComponent(1).setHandler(this.loadPreset, this);

    deluge.preferences.on('show', this.loadPrefs, this);
    deluge.preferences.buttons[1].on('click', this.savePrefs, this);
    deluge.preferences.buttons[2].on('click', this.savePrefs, this);

    this.waitForClient(10);
  },

  onDestroy: function() {
    deluge.preferences.un('show', this.loadPrefs, this);
    deluge.preferences.buttons[1].un('click', this.savePrefs, this);
    deluge.preferences.buttons[2].un('click', this.savePrefs, this);

    Deluge.plugins.ltconfig.ui.PreferencePage.superclass.onDestroy.call(this);
  },

  waitForClient: function(triesLeft) {
    if (triesLeft < 1) {
      this.tblSettings.setEmptyText(_('Unable to load settings'));
      return;
    }

    if (deluge.login.isVisible() || !deluge.client.core ||
        !deluge.client.ltconfig) {
      var self = this;
      var t = deluge.login.isVisible() ? triesLeft : triesLeft-1;
      setTimeout(function() { self.waitForClient.apply(self, [t]); }, 1000);
    } else if (!this.isDestroyed) {
      this.loadBaseState();
    }
  },

  loadBaseState: function() {
    this._loadBaseState1();
  },

  _loadBaseState1: function() {
    deluge.client.core.get_libtorrent_version({
      success: function(version) {
        var parts = version.split('.');
        if (Number(parts[0]) < 1 && Number(parts[1]) < 16) {
          this.presetsContainer.getComponent(0).getStore().removeAt(2);
          this.presetsContainer.getComponent(0).getStore().removeAt(1);
        }
        this.lblVersion.setText(this.lblVersion.caption + version);
        this._loadBaseState2();
      },
      scope: this
    });
  },

  _loadBaseState2: function() {
    deluge.client.ltconfig.get_original_settings({
      success: function(settings) {
        this.tblSettings.baseSettings = settings;

        var data = [];
        var keys = Ext.keys(settings).sort();

        for (var i = 0; i < keys.length; i++) {
          var key = keys[i];
          data.push([false, key, settings[key], settings[key]]);
        }

        this.tblSettings.loadData(data);
        this.loadPrefs();
      },
      scope: this
    });
  },

  loadPrefs: function() {
    if (deluge.preferences.isVisible()) {
      this._loadPrefs1();
    }
  },

  _loadPrefs1: function() {
    deluge.client.ltconfig.get_preferences({
      success: function(prefs) {
        this.preferences = prefs;
        this.chkApplyOnStart.setValue(prefs['apply_on_start']);
        this.loadSettings(prefs['settings']);
        this._loadPrefs2();
      },
      scope: this
    });
  },

  _loadPrefs2: function() {
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
  },

  loadSettings: function(settings) {
    var store = this.tblSettings.getStore();

    for (var i = 0; i < store.getCount(); i++) {
      var record = store.getAt(i);
      var name = record.get('name');

      if (name in settings) {
        record.set('enabled', true);
        record.set('setting', settings[name]);
      } else {
        record.set('enabled', false);
        record.set('setting', this.tblSettings.baseSettings[name]);
      }
    }

    store.commitChanges();
  },

  loadPreset: function() {
    var preset = this.presetsContainer.getComponent(0).getValue();

    if (Ext.isNumber(preset)) {
      deluge.client.ltconfig.get_preset(preset, {
        success: this.loadSettings,
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

    console.log('%s enabled', Deluge.plugins.ltconfig.PLUGIN_NAME);
  },

  onDisable: function() {
    deluge.preferences.selectPage(_('Plugins'));
    deluge.preferences.removePage(this.prefsPage);
    this.prefsPage.destroy();

    console.log('%s disabled', Deluge.plugins.ltconfig.PLUGIN_NAME);
  }
});

Deluge.registerPlugin(Deluge.plugins.ltconfig.PLUGIN_NAME,
  Deluge.plugins.ltconfig.Plugin);
