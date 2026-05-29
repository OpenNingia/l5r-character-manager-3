// Copyright (C) 2014-2026 Daniele Simonetti
// Inline chooser for "Buy New Skill" -- replaces the legacy QWidget
// BuyAdvDialog(tag='skill') (l5r/dialogs/advdlg.py) without reusing any
// of its widgets. Pulls the candidate list from
// appCtrl.availableSkillsToBuy() and, on accept, walks the selected skill
// from rank 0 -> 1 via appCtrl.buySkillRank(id) -- the same purchase path
// used to level up an existing skill.
// Built on Widgets.L5RDialog: the kakemono header, parchment background
// and Cancel/Add footer come from the shared shell; this file only sets
// the chrome props and supplies the body.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 520, 520)
    padding: 16

    // --- chrome (blue Blessing-style accent) ----------------------
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    seal: "修"   // "to cultivate / to train" -- learning a discipline
    title: qsTr("Add a new skill to your repertoire")
    tagline: qsTr("the first rank of any unknown skill costs experience")
    acceptText: qsTr("Add")
    acceptGlyph: "修"
    acceptEnabled: root._selectedId.length > 0
    onAccepted: if (root._selectedId && appCtrl)
        appCtrl.buySkillRank(root._selectedId)

    // --- state ----------------------------------------------------
    property var _candidates: []
    property string _selectedId: ""

    onAboutToShow: {
        _candidates = appCtrl ? appCtrl.availableSkillsToBuy() : [];
        skillCombo.currentIndex = _candidates.length > 0 ? 0 : -1;
        _selectedId = _candidates.length > 0 ? _candidates[0].id : "";
    }

    function _currentRecord() {
        if (skillCombo.currentIndex < 0 || skillCombo.currentIndex >= _candidates.length)
            return null;
        return _candidates[skillCombo.currentIndex];
    }

    // --- body -----------------------------------------------------
    ColumnLayout {
        spacing: 14

        // Empty-state notice when no candidates exist (rare -- requires
        // the datapacks to be empty or the character to already know
        // everything in them).
        ColumnLayout {
            visible: root._candidates.length === 0
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 6

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "修"
                font.family: Theme.fontKanji
                font.pixelSize: 90
                color: root.accent
                opacity: 0.15
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("No further skills are available to learn.")
                font.italic: true
                color: Theme.ink
                opacity: 0.7
            }
        }

        // --- chooser body: combo + read-only details ----------------
        GridLayout {
            visible: root._candidates.length > 0
            Layout.fillWidth: true
            Layout.topMargin: 4
            columns: 2
            columnSpacing: 14
            rowSpacing: 10

            Label {
                text: qsTr("Skill")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
                Layout.preferredWidth: 90
            }
            Widgets.L5RComboBox {
                id: skillCombo
                Layout.fillWidth: true
                textRole: "name"
                model: root._candidates
                accent: root.accent
                onActivated: function (index) {
                    var rec = root._candidates[index];
                    root._selectedId = rec ? rec.id : "";
                }
            }

            Label {
                text: qsTr("Category")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
            }
            Label {
                Layout.fillWidth: true
                font.italic: true
                color: Theme.ink
                opacity: 0.85
                text: {
                    var rec = root._currentRecord();
                    return rec ? rec.category : "";
                }
            }

            Label {
                text: qsTr("Trait")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
            }
            Label {
                Layout.fillWidth: true
                font.family: Theme.fontDisplay
                font.letterSpacing: 1.4
                font.weight: Theme.wSemiBold
                color: Theme.heading
                text: {
                    var rec = root._currentRecord();
                    return rec ? rec.trait.toUpperCase() : "";
                }
            }
        }
    }
}
