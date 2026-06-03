// Copyright (C) 2014-2026 Daniele Simonetti
// QML replacement for l5r/widgets/familychooser.py FamilyChooserDialog.
// Two combos (Clan, Family) + source-book and bonus-trait readouts.
// Closes via Accept to commit the selection through appCtrl.setFamily(),
// or Cancel to discard. Built on Widgets.L5RDialog (shared chrome); the
// blue accent + 家 seal mark it as an identity/configuration dialog.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0
import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: 480
    padding: Theme.s5
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- chrome ---------------------------------------------------
    title: qsTr("Clan and Family")
    tagline: qsTr("a Samurai should serve its clan first and foremost")
    seal: "家"   // ie -- house / family
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Accept")
    acceptEnabled: _selectedFamilyId.length > 0

    // Caller sets this before open() so we can preselect.
    property string initialFamilyId: ""

    // Working state, separate from the model until Accept fires.
    property string _selectedClanId: ""
    property string _selectedFamilyId: ""
    property var _families: []

    onAboutToShow: {
        _selectedFamilyId = initialFamilyId;
        _selectedClanId = appCtrl ? appCtrl.currentClanId() : "";
        _refreshFamilies();
        _syncClanCombo();
        _syncFamilyCombo();
    }

    onAccepted: {
        if (_selectedFamilyId && appCtrl) {
            appCtrl.setFamily(_selectedFamilyId);
        }
    }

    function _refreshFamilies() {
        _families = appCtrl ? appCtrl.familiesForClan(_selectedClanId) : [];
    }

    function _syncClanCombo() {
        if (!appCtrl)
            return;
        var idx = -1;
        for (var i = 0; i < clanCombo.count; ++i) {
            if (clanCombo.model[i].id === _selectedClanId) {
                idx = i;
                break;
            }
        }
        clanCombo.currentIndex = idx >= 0 ? idx : 0;
    }

    function _syncFamilyCombo() {
        var idx = -1;
        for (var i = 0; i < _families.length; ++i) {
            if (_families[i].id === _selectedFamilyId) {
                idx = i;
                break;
            }
        }
        familyCombo.currentIndex = idx >= 0 ? idx : 0;
        _selectedFamilyId = familyCombo.count > 0 ? _families[familyCombo.currentIndex].id : "";
    }

    function _currentFamilyRecord() {
        if (familyCombo.currentIndex < 0 || familyCombo.currentIndex >= _families.length)
            return null;
        return _families[familyCombo.currentIndex];
    }

    // --- body -----------------------------------------------------
    contentItem: GridLayout {
        columns: 2
        columnSpacing: 12
        rowSpacing: 8

        Label {
            text: qsTr("Clan:")
        }
        Widgets.L5RComboBox {
            id: clanCombo
            Layout.fillWidth: true
            textRole: "name"
            accent: root.accent
            model: {
                var clans = appCtrl ? appCtrl.clansList() : [];
                return [{
                        "id": "",
                        "name": qsTr("No Clan")
                    }].concat(clans);
            }
            onActivated: function (index) {
                var rec = clanCombo.model[index];
                root._selectedClanId = rec ? rec.id : "";
                root._refreshFamilies();
                root._syncFamilyCombo();
            }
        }

        Label {
            text: qsTr("Family:")
        }
        Widgets.L5RComboBox {
            id: familyCombo
            Layout.fillWidth: true
            textRole: "name"
            accent: root.accent
            model: root._families
            onActivated: function (index) {
                var rec = root._families[index];
                root._selectedFamilyId = rec ? rec.id : "";
            }
        }

        Label {
            text: qsTr("Source:")
        }
        Label {
            Layout.fillWidth: true
            font.italic: true
            opacity: 0.8
            text: {
                var rec = root._currentFamilyRecord();
                if (!rec || !rec.book)
                    return "";
                return rec.page ? qsTr("%1, page %2").arg(rec.book).arg(rec.page) : rec.book;
            }
        }

        Rectangle {
            Layout.columnSpan: 2
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.divider
            opacity: Theme.dividerOpacity
        }

        Label {
            text: qsTr("Bonus:")
        }
        Label {
            Layout.fillWidth: true
            color: Theme.positive
            text: {
                var rec = root._currentFamilyRecord();
                return rec && rec.trait ? qsTr("+1 %1").arg(rec.trait) : "";
            }
        }
    }
}
