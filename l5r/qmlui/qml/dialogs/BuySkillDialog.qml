// Copyright (C) 2014-2026 Daniele Simonetti
// Inline chooser for "Buy New Skill" -- replaces the legacy QWidget
// BuyAdvDialog(tag='skill') (l5r/dialogs/advdlg.py) without reusing
// any of its widgets. Pulls the candidate list from
// appCtrl.availableSkillsToBuy() and, on accept, walks the selected
// skill from rank 0 -> 1 via appCtrl.buySkillRank(id) -- the same
// purchase path used to level up an existing skill.
// Lives in qml/dialogs/ alongside the family / school choosers; the
// SkillsSection drives it through `id` + `open()`.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

Dialog {
    id: root
    title: qsTr("L5R: CM - Buy Skill")
    standardButtons: Dialog.Ok | Dialog.Cancel
    modal: true
    width: 520
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    property var _candidates: []
    property string _selectedId: ""

    onAboutToShow: {
        _candidates = appCtrl ? appCtrl.availableSkillsToBuy() : [];
        skillCombo.currentIndex = _candidates.length > 0 ? 0 : -1;
        _selectedId = _candidates.length > 0 ? _candidates[0].id : "";
    }
    onAccepted: {
        if (_selectedId && appCtrl)
            appCtrl.buySkillRank(_selectedId);
    }

    function _currentRecord() {
        if (skillCombo.currentIndex < 0 || skillCombo.currentIndex >= _candidates.length)
            return null;
        return _candidates[skillCombo.currentIndex];
    }

    contentItem: ColumnLayout {
        spacing: 14

        Label {
            Layout.fillWidth: true
            Layout.topMargin: 6
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("Add a new skill to your repertoire")
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.titleFont
            font.weight: Font.DemiBold
            color: Theme.heading
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("The first rank of any unknown skill costs experience.")
            opacity: 0.75
            font.italic: true
            color: Theme.accentMuted
        }

        // Empty-state notice when no candidates exist (rare -- requires
        // the datapacks to be empty or the character to already know
        // everything in them).
        Label {
            visible: root._candidates.length === 0
            Layout.fillWidth: true
            Layout.topMargin: 12
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("No further skills are available to learn.")
            opacity: 0.7
            font.italic: true
        }

        GridLayout {
            visible: root._candidates.length > 0
            Layout.fillWidth: true
            Layout.topMargin: 10
            columns: 2
            columnSpacing: 12
            rowSpacing: 8

            Label {
                text: qsTr("Skill:")
            }
            ComboBox {
                id: skillCombo
                Layout.fillWidth: true
                textRole: "name"
                model: root._candidates
                onActivated: function (index) {
                    var rec = root._candidates[index];
                    root._selectedId = rec ? rec.id : "";
                }
            }

            Label {
                text: qsTr("Category:")
            }
            Label {
                Layout.fillWidth: true
                font.italic: true
                opacity: 0.85
                text: {
                    var rec = root._currentRecord();
                    return rec ? rec.category : "";
                }
            }

            Label {
                text: qsTr("Trait:")
            }
            Label {
                Layout.fillWidth: true
                font.family: Theme.fontDisplay
                font.letterSpacing: 1.4
                color: Theme.heading
                text: {
                    var rec = root._currentRecord();
                    return rec ? rec.trait.toUpperCase() : "";
                }
            }
        }
    }
}
