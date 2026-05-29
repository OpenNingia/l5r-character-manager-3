// Copyright (C) 2014-2026 Daniele Simonetti
// QML replacement for l5r/widgets/familychooser.py FamilyChooserDialog.
// Two combos (Clan, Family) + source-book and bonus-trait readouts.
// Closes via OK to commit the selection through appCtrl.setFamily(),
// or Cancel to discard.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

Dialog {
    id: root
    title: qsTr("Clan and Family")
    standardButtons: Dialog.Ok | Dialog.Cancel
    modal: true
    width: 480
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // Caller sets this before open() so we can preselect.
    property string initialFamilyId: ""

    // Working state, separate from the model until OK fires.
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

    contentItem: ColumnLayout {
        spacing: 14

        Label {
            Layout.fillWidth: true
            Layout.topMargin: 6
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("Select Clan and Family")
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsHeading1
            font.weight: Font.DemiBold
            color: Theme.heading
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("a Samurai should serve its clan first and foremost")
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

            Label {
                text: qsTr("Clan:")
            }
            ComboBox {
                id: clanCombo
                Layout.fillWidth: true
                textRole: "name"
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
            ComboBox {
                id: familyCombo
                Layout.fillWidth: true
                textRole: "name"
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
                font.weight: Font.DemiBold
                text: {
                    var rec = root._currentFamilyRecord();
                    return rec && rec.trait ? qsTr("+1 %1").arg(rec.trait) : "";
                }
            }
        }
    }
}
