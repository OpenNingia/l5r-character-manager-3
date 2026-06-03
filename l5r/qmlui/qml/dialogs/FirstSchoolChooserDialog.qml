// Copyright (C) 2014-2026 Daniele Simonetti
// QML replacement for l5r/widgets/schoolchooser.py FirstSchoolChooserDialog.
// Three combos -- Clan, Basic School, Rank-1 Alternate Path (optional) --
// plus source-book and bonus-trait readouts. The legacy dialog only
// surfaces basic schools and rank-1 paths; advanced schools are reached
// later through the Advancements tab. Built on Widgets.L5RDialog.
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
    title: qsTr("Join your First School")
    tagline: qsTr("in this phase you're limited to base schools")
    seal: "流"   // ryū -- school / style
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Accept")
    acceptEnabled: _selectedSchoolId.length > 0

    property string initialSchoolId: ""

    property string _selectedClanId: ""
    property string _selectedSchoolId: ""
    property string _selectedPathId: ""
    property var _schools: []
    property var _paths: []

    onAboutToShow: {
        _selectedSchoolId = initialSchoolId;
        _selectedClanId = appCtrl ? appCtrl.currentClanId() : "";
        _selectedPathId = "";
        _refreshSchools();
        _refreshPaths();
        _syncClanCombo();
        _syncSchoolCombo();
        pathCombo.currentIndex = 0;
    }

    onAccepted: {
        if (_selectedSchoolId && appCtrl) {
            appCtrl.setFirstSchool(_selectedSchoolId, _selectedPathId);
        }
    }

    function _refreshSchools() {
        _schools = appCtrl ? appCtrl.basicSchoolsForClan(_selectedClanId) : [];
    }
    function _refreshPaths() {
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

    function _currentSchoolRecord() {
        if (schoolCombo.currentIndex < 0 || schoolCombo.currentIndex >= _schools.length)
            return null;
        return _schools[schoolCombo.currentIndex];
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
                root._refreshSchools();
                root._refreshPaths();
                root._syncSchoolCombo();
                pathCombo.currentIndex = 0;
                root._selectedPathId = "";
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
            color: {
                var rec = root._currentSchoolRecord();
                return rec && rec.trait ? Theme.positive : Theme.negative;
            }
            text: {
                var rec = root._currentSchoolRecord();
                return rec && rec.trait ? qsTr("+1 %1").arg(rec.trait) : qsTr("None");
            }
        }
    }
}
