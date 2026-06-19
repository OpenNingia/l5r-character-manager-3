// Copyright (C) 2014-2026 Daniele Simonetti
// Unified origin picker (issue #451): clan -> family -> school -> optional
// rank-1 path, captured in one place and committed atomically through
// appCtrl.setOrigin(). Replaces the separate FamilyChooserDialog and
// FirstSchoolChooserDialog (both of which already carried a Clan combo and
// could leave the character half-built, e.g. a school with no family).
//
// The origin grants the starting trait bonuses, so it must be chosen before
// any XP is spent; the host gates opening this on pcProxy.canEditOrigin. The
// summed-bonus readout makes the family + school trait gifts explicit.
//
// Built on Widgets.L5RDialog (shared chrome); the blue secondary accent and a
// 源 (origin) seal mark it as an identity/configuration dialog.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0
import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: 540
    padding: Theme.s5
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- chrome ---------------------------------------------------
    title: qsTr("Choose your Origin")
    tagline: qsTr("clan, family and school define who a Samurai is")
    seal: "源"   // gen -- origin / source
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Accept")
    // Rules require both a family (clan) and a school: the two carry the
    // starting trait bonuses and the school seeds the rank-1 technique.
    acceptEnabled: _selectedFamilyId.length > 0 && _selectedSchoolId.length > 0

    // Working state, separate from the model until Accept fires.
    property string _selectedClanId: ""
    property string _selectedFamilyId: ""
    property string _selectedSchoolId: ""
    property string _selectedPathId: ""
    property var _families: []
    property var _schools: []
    property var _paths: []

    onAboutToShow: {
        _selectedClanId = appCtrl ? appCtrl.currentClanId() : "";
        _selectedFamilyId = appCtrl ? appCtrl.currentFamilyId() : "";
        _selectedSchoolId = appCtrl ? appCtrl.currentFirstSchoolId() : "";
        _selectedPathId = "";
        _refreshLists();
        _syncClanCombo();
        _syncFamilyCombo();
        _syncSchoolCombo();
        pathCombo.currentIndex = 0;
    }

    onAccepted: {
        if (appCtrl && _selectedFamilyId && _selectedSchoolId) {
            appCtrl.setOrigin(_selectedFamilyId, _selectedSchoolId, _selectedPathId);
        }
    }

    function _refreshLists() {
        _families = appCtrl ? appCtrl.familiesForClan(_selectedClanId) : [];
        _schools = appCtrl ? appCtrl.basicSchoolsForClan(_selectedClanId) : [];
        _paths = appCtrl ? appCtrl.rank1PathsForClan(_selectedClanId) : [];
    }

    function _syncClanCombo() {
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

    function _syncSchoolCombo() {
        var idx = -1;
        for (var i = 0; i < _schools.length; ++i) {
            if (_schools[i].id === _selectedSchoolId) {
                idx = i;
                break;
            }
        }
        schoolCombo.currentIndex = idx >= 0 ? idx : 0;
        _selectedSchoolId = schoolCombo.count > 0 ? _schools[schoolCombo.currentIndex].id : "";
    }

    function _currentFamilyRecord() {
        if (familyCombo.currentIndex < 0 || familyCombo.currentIndex >= _families.length)
            return null;
        return _families[familyCombo.currentIndex];
    }

    function _currentSchoolRecord() {
        if (schoolCombo.currentIndex < 0 || schoolCombo.currentIndex >= _schools.length)
            return null;
        return _schools[schoolCombo.currentIndex];
    }

    // Summed starting trait bonuses (family + school), e.g. "+1 strength, +1 willpower".
    function _bonusText() {
        var parts = [];
        var fam = _currentFamilyRecord();
        if (fam && fam.trait)
            parts.push(qsTr("+1 %1").arg(fam.trait));
        var sch = _currentSchoolRecord();
        if (sch && sch.trait)
            parts.push(qsTr("+1 %1").arg(sch.trait));
        return parts.join(", ");
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
                root._refreshLists();
                root._syncFamilyCombo();
                root._syncSchoolCombo();
                pathCombo.currentIndex = 0;
                root._selectedPathId = "";
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
            text: qsTr("School:")
        }
        Widgets.L5RComboBox {
            id: schoolCombo
            Layout.fillWidth: true
            textRole: "name"
            accent: root.accent
            model: root._schools
            onActivated: function (index) {
                var rec = root._schools[index];
                root._selectedSchoolId = rec ? rec.id : "";
            }
        }

        Label {
            text: qsTr("Path:")
        }
        Widgets.L5RComboBox {
            id: pathCombo
            Layout.fillWidth: true
            textRole: "name"
            accent: root.accent
            model: {
                var none = [{
                        "id": "",
                        "name": qsTr("None")
                    }];
                return none.concat(root._paths);
            }
            onActivated: function (index) {
                var rec = pathCombo.model[index];
                root._selectedPathId = rec ? rec.id : "";
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
                var rec = root._currentSchoolRecord();
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
            text: root._bonusText()
        }
    }
}
