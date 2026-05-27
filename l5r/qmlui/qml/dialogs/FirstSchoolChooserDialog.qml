// Copyright (C) 2014-2026 Daniele Simonetti
// QML replacement for l5r/widgets/schoolchooser.py FirstSchoolChooserDialog.
// Three combos -- Clan, Basic School, Rank-1 Alternate Path (optional) --
// plus source-book and bonus-trait readouts. The legacy dialog only
// surfaces basic schools and rank-1 paths; advanced schools are reached
// later through the Advancements tab.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Theme 1.0

Dialog {
    id: root
    title: qsTr("L5R: CM - First School")
    standardButtons: Dialog.Ok | Dialog.Cancel
    modal: true
    width: 540
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    property string initialSchoolId: ""

    property string _selectedClanId: ""
    property string _selectedSchoolId: ""
    property string _selectedPathId: ""
    property var _schools: []
    property var _paths: []

    onAboutToShow: {
        _selectedSchoolId = initialSchoolId
        _selectedClanId = appCtrl ? appCtrl.currentClanId() : ""
        _selectedPathId = ""
        _refreshSchools()
        _refreshPaths()
        _syncClanCombo()
        _syncSchoolCombo()
        pathCombo.currentIndex = 0
    }

    onAccepted: {
        if (_selectedSchoolId && appCtrl) {
            appCtrl.setFirstSchool(_selectedSchoolId, _selectedPathId)
        }
    }

    function _refreshSchools() {
        _schools = appCtrl ? appCtrl.basicSchoolsForClan(_selectedClanId) : []
    }
    function _refreshPaths() {
        _paths = appCtrl ? appCtrl.rank1PathsForClan(_selectedClanId) : []
    }

    function _syncClanCombo() {
        var idx = -1
        for (var i = 0; i < clanCombo.count; ++i) {
            if (clanCombo.model[i].id === _selectedClanId) { idx = i; break }
        }
        clanCombo.currentIndex = idx >= 0 ? idx : 0
    }

    function _syncSchoolCombo() {
        var idx = -1
        for (var i = 0; i < _schools.length; ++i) {
            if (_schools[i].id === _selectedSchoolId) { idx = i; break }
        }
        schoolCombo.currentIndex = idx >= 0 ? idx : 0
        _selectedSchoolId = schoolCombo.count > 0
            ? _schools[schoolCombo.currentIndex].id : ""
    }

    function _currentSchoolRecord() {
        if (schoolCombo.currentIndex < 0
            || schoolCombo.currentIndex >= _schools.length) return null
        return _schools[schoolCombo.currentIndex]
    }

    contentItem: ColumnLayout {
        spacing: 14

        Label {
            Layout.fillWidth: true
            Layout.topMargin: 6
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("Join your First School")
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.titleFont
            font.weight: Font.DemiBold
            color: Theme.heading
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("In this phase you're limited to base schools")
            opacity: 0.75
            font.italic: true
            color: Theme.accentMuted
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.topMargin: 10
            columns: 2
            columnSpacing: 12
            rowSpacing: 8

            Label { text: qsTr("Clan:") }
            ComboBox {
                id: clanCombo
                Layout.fillWidth: true
                textRole: "name"
                model: {
                    var clans = appCtrl ? appCtrl.clansList() : []
                    return [{ id: "", name: qsTr("No Clan") }].concat(clans)
                }
                onActivated: function(index) {
                    var rec = clanCombo.model[index]
                    root._selectedClanId = rec ? rec.id : ""
                    root._refreshSchools()
                    root._refreshPaths()
                    root._syncSchoolCombo()
                    pathCombo.currentIndex = 0
                    root._selectedPathId = ""
                }
            }

            Label { text: qsTr("School:") }
            ComboBox {
                id: schoolCombo
                Layout.fillWidth: true
                textRole: "name"
                model: root._schools
                onActivated: function(index) {
                    var rec = root._schools[index]
                    root._selectedSchoolId = rec ? rec.id : ""
                }
            }

            Label { text: qsTr("Path:") }
            ComboBox {
                id: pathCombo
                Layout.fillWidth: true
                textRole: "name"
                model: {
                    var none = [{ id: "", name: qsTr("None") }]
                    return none.concat(root._paths)
                }
                onActivated: function(index) {
                    var rec = pathCombo.model[index]
                    root._selectedPathId = rec ? rec.id : ""
                }
            }

            Label { text: qsTr("Source:") }
            Label {
                Layout.fillWidth: true
                font.italic: true
                opacity: 0.8
                text: {
                    var rec = root._currentSchoolRecord()
                    if (!rec || !rec.book) return ""
                    return rec.page
                        ? qsTr("%1, page %2").arg(rec.book).arg(rec.page)
                        : rec.book
                }
            }

            Rectangle {
                Layout.columnSpan: 2
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Theme.divider
                opacity: Theme.dividerOpacity
            }

            Label { text: qsTr("Bonus:") }
            Label {
                Layout.fillWidth: true
                color: {
                    var rec = root._currentSchoolRecord()
                    return rec && rec.trait ? Theme.positive : Theme.negative
                }
                font.weight: Font.DemiBold
                text: {
                    var rec = root._currentSchoolRecord()
                    return rec && rec.trait
                        ? qsTr("+1 %1").arg(rec.trait)
                        : qsTr("None")
                }
            }
        }
    }
}
