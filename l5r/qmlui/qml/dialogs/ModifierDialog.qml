// Copyright (C) 2014-2026 Daniele Simonetti
// ModifierDialog -- QML-native form for adding or re-keying a custom
// roll/stat modifier. Replaces the legacy QWidget ModifierDialog
// (l5r/dialogs/modifiersdlg.py) without reusing any of its widgets. Two
// entrypoints from MiscSection:
//     modifierDlg.presentAdd()        // declare a new modifier
//     modifierDlg.presentEdit(item)   // re-key an existing one
//
// The "Modifies" dropdown picks what the modifier affects; the kind it
// picks decides whether the "Detail" field is live (a skill / weapon /
// trait / ring name) or disabled (rolls that need no further target). The
// "Value" field is roll-and-keep with an optional flat bonus (e.g. "+2",
// "1k0", "2k1+3"); the "Reason" is the player's own note. The toggle
// declares whether the modifier is applied straight away.
//
// On accept:
//   add  -> appCtrl.addModifier(type, detail, value, reason, active)
//   edit -> appCtrl.editModifier(id, type, detail, value, reason, active)
// where the controller exposes:
//   appCtrl.modifierTypes() -> [{ key, label, detailKind, detailLabel }]
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property bool _editMode: false
    property string _modId: ""
    property var _types: []

    // --- derived --------------------------------------------------
    readonly property color _accent: Theme.accent
    readonly property var _currentType: (typeCombo.currentIndex >= 0 && dlg._types.length > typeCombo.currentIndex) ? dlg._types[typeCombo.currentIndex] : null
    readonly property string _detailKind: dlg._currentType ? dlg._currentType.detailKind : "none"
    readonly property bool _detailEnabled: dlg._detailKind !== "none"
    readonly property string _detailPrompt: dlg._currentType && dlg._currentType.detailLabel ? dlg._currentType.detailLabel : ""

    // --- size -----------------------------------------------------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 540, 540)
    padding: Theme.s5

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "雑"
    title: dlg._editMode ? qsTr("Edit Modifier") : qsTr("Add a Modifier")
    tagline: dlg._editMode ? qsTr("re-key a bonus or penalty you carry") : qsTr("note a bonus or penalty to your rolls")
    accent: _accent
    accentDark: Theme.accentMuted
    acceptText: dlg._editMode ? qsTr("Save") : qsTr("Add")
    acceptGlyph: "雑"
    acceptEnabled: valueFF.text.trim().length > 0
    statusText: dlg._detailEnabled ? qsTr("Name the %1 this modifier applies to.").arg((dlg._detailPrompt || "").toLowerCase()) : qsTr("A modifier is figured into your rolls only while it is applied.")
    onAccepted: {
        if (!appCtrl)
            return;
        var typeKey = dlg._currentType ? dlg._currentType.key : "anyr";
        var detail = dlg._detailEnabled ? detailFF.text : "";
        if (dlg._editMode) {
            appCtrl.editModifier(dlg._modId, typeKey, detail, valueFF.text, reasonFF.text, activeToggle.checked);
        } else {
            appCtrl.addModifier(typeKey, detail, valueFF.text, reasonFF.text, activeToggle.checked);
        }
    }

    // --- entrypoints ----------------------------------------------
    function presentAdd() {
        dlg._editMode = false;
        dlg._modId = "";
        dlg._types = (appCtrl && appCtrl.modifierTypes) ? (appCtrl.modifierTypes() || []) : [];
        typeCombo.currentIndex = 0;
        detailFF.text = "";
        valueFF.text = "";
        reasonFF.text = "";
        // A fresh modifier is applied straight away -- the player adds one
        // to use it; the toggle is there to declare otherwise.
        activeToggle.checked = true;
        dlg.open();
        reasonFF.forceActiveFocus();
    }

    function presentEdit(item) {
        if (!item)
            return;
        dlg._editMode = true;
        dlg._modId = item.id || "";
        dlg._types = (appCtrl && appCtrl.modifierTypes) ? (appCtrl.modifierTypes() || []) : [];
        var idx = 0;
        for (var i = 0; i < dlg._types.length; ++i) {
            if (dlg._types[i].key === item.type) {
                idx = i;
                break;
            }
        }
        typeCombo.currentIndex = idx;
        detailFF.text = item.detail || "";
        valueFF.text = item.value || "";
        reasonFF.text = item.reason || "";
        activeToggle.checked = !!item.active;
        dlg.open();
        reasonFF.forceActiveFocus();
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: 14

        // ---- Modifies (type) -------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Label {
                text: qsTr("MODIFIES")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.4
                color: Theme.heading
            }
            Widgets.L5RComboBox {
                id: typeCombo
                Layout.fillWidth: true
                accent: dlg._accent
                model: dlg._types
                textRole: "label"
            }
        }

        // ---- Detail ----------------------------------------------
        // Live only for kinds that need a target (a skill/weapon/trait/
        // ring name); disabled and greyed for rolls that don't.
        FormField {
            id: detailFF
            Layout.fillWidth: true
            label: qsTr("Detail")
            placeholder: dlg._detailEnabled ? qsTr("name the %1…").arg((dlg._detailPrompt || "").toLowerCase()) : qsTr("not needed for this modifier")
            fieldEnabled: dlg._detailEnabled
        }

        // ---- Value + Reason --------------------------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 16
            rowSpacing: 12

            FormField {
                id: valueFF
                Layout.preferredWidth: 140
                label: qsTr("Value")
                placeholder: qsTr("e.g. +2 or 1k0")
            }
            FormField {
                id: reasonFF
                Layout.fillWidth: true
                label: qsTr("Reason")
                placeholder: qsTr("why you have this edge…")
            }
        }

        Label {
            Layout.fillWidth: true
            text: qsTr("Value is roll-and-keep with an optional flat bonus — “+2”, “1k0”, or “2k1+3”.")
            font.italic: true
            font.pixelSize: Theme.fsCaption
            color: Theme.ink
            opacity: 0.6
            wrapMode: Text.WordWrap
        }

        // ---- Applied toggle --------------------------------------
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 2
            spacing: Theme.s2
            Label {
                text: qsTr("APPLY NOW")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.4
                color: Theme.heading
            }
            Item {
                Layout.fillWidth: true
            }
            Widgets.L5RToggle {
                id: activeToggle
                checked: true
            }
        }
    }

    // =================================================================
    // FormField -- a captioned, parchment-skinned text input. `text` is a
    // two-way alias of the field; `fieldEnabled` greys it out (used for
    // the Detail field on target-less modifier kinds).
    // =================================================================
    component FormField: ColumnLayout {
        id: ff
        property string label: ""
        property string placeholder: ""
        property bool fieldEnabled: true
        property alias text: input.text
        spacing: 3

        function forceActiveFocus() {
            input.forceActiveFocus();
        }

        Label {
            text: ff.label.toUpperCase()
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsCaption
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.4
            color: ff.fieldEnabled ? Theme.heading : Theme.inkFaint
        }
        TextField {
            id: input
            Layout.fillWidth: true
            implicitHeight: 34
            enabled: ff.fieldEnabled
            placeholderText: ff.placeholder
            color: Theme.ink
            placeholderTextColor: Theme.inkFaint
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            background: Rectangle {
                color: ff.fieldEnabled ? Theme.parchmentBase : Theme.disabledBg
                border.color: input.activeFocus ? dlg._accent : Theme.borderSubtle
                border.width: 1
                radius: 2
            }
        }
    }
}
