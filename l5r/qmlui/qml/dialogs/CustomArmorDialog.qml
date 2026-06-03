// Copyright (C) 2014-2026 Daniele Simonetti
// CustomArmorDialog -- QML-native form for forging a custom armour or
// re-statting the one already worn. Replaces the legacy QWidget
// CustomArmorDialog (l5r/dialogs/customitems.py) without reusing any of
// its widgets. Two entrypoints from WeaponsSection's armour rail:
//     customArmorDlg.presentAdd()        // forge a new armour
//     customArmorDlg.presentEdit(armor)  // re-stat the worn one
//
// In ADD mode a "base armour" dropdown seeds the figures from a catalogue
// template; the player then overrides the name / TN / reduction. In EDIT
// mode the base dropdown is hidden and the form is pre-filled from the
// worn armour. A character wears one armour, so either path replaces it.
//
// On accept:
//   add  -> appCtrl.wearCustomArmor({ name, tn, rd, notes })
//   edit -> appCtrl.editArmor({ name, tn, rd, notes })
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property bool _editMode: false
    property var _catalogue: []

    // --- derived --------------------------------------------------
    readonly property color _accent: Theme.ringEarth

    // --- size -----------------------------------------------------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 520, 520)
    padding: Theme.s5

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "鎧"
    title: dlg._editMode ? qsTr("Edit Armor") : qsTr("Forge Armor")
    tagline: dlg._editMode ? qsTr("re-stat the harness you wear") : qsTr("temper a harness to your own measure")
    accent: _accent
    accentDark: Qt.darker(_accent, 1.3)
    acceptText: dlg._editMode ? qsTr("Save") : qsTr("Wear")
    acceptGlyph: "鎧"
    acceptEnabled: nameFF.text.trim().length > 0
    statusText: dlg._editMode ? qsTr("Save your changes to this armour.") : qsTr("A custom armour replaces whatever you now wear.")
    onAccepted: {
        if (!appCtrl)
            return;
        var payload = {
            "name": nameFF.text,
            "tn": tnFF.text,
            "rd": rdFF.text,
            "notes": notesArea.text
        };
        if (dlg._editMode)
            appCtrl.editArmor(payload);
        else
            appCtrl.wearCustomArmor(payload);
    }

    // --- entrypoints ----------------------------------------------
    function presentAdd() {
        dlg._editMode = false;
        dlg._catalogue = (appCtrl && appCtrl.availableArmors) ? (appCtrl.availableArmors() || []) : [];
        nameFF.text = "";
        tnFF.text = "";
        rdFF.text = "";
        notesArea.text = "";
        if (dlg._catalogue.length > 0) {
            baseCombo.currentIndex = 0;
            dlg._applyBase(dlg._catalogue[0]);
        }
        dlg.open();
        nameFF.forceActiveFocus();
    }

    function presentEdit(armor) {
        if (!armor)
            return;
        dlg._editMode = true;
        nameFF.text = armor.name || "";
        tnFF.text = (armor.tn !== undefined && armor.tn !== null) ? ("" + armor.tn) : "";
        rdFF.text = (armor.rd !== undefined && armor.rd !== null) ? ("" + armor.rd) : "";
        notesArea.text = armor.desc || "";
        dlg.open();
        nameFF.forceActiveFocus();
    }

    function _applyBase(rec) {
        if (!rec)
            return;
        nameFF.text = rec.name || "";
        tnFF.text = "" + (rec.tn || 0);
        rdFF.text = "" + (rec.rd || 0);
        notesArea.text = rec.effect || "";
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: 14

        // ---- Base armour (add mode only) -------------------------
        ColumnLayout {
            Layout.fillWidth: true
            visible: !dlg._editMode
            spacing: 3
            Label {
                text: qsTr("BASE ARMOR")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.4
                color: Theme.heading
            }
            Widgets.L5RComboBox {
                id: baseCombo
                Layout.fillWidth: true
                accent: dlg._accent
                model: dlg._catalogue
                textRole: "name"
                onActivated: index => dlg._applyBase(dlg._catalogue[index])
            }
            Label {
                Layout.fillWidth: true
                text: qsTr("Seeds the figures below — change them freely.")
                font.italic: true
                font.pixelSize: Theme.fsCaption
                color: Theme.ink
                opacity: 0.6
                wrapMode: Text.WordWrap
            }
        }

        // ---- Name ------------------------------------------------
        FormField {
            id: nameFF
            Layout.fillWidth: true
            label: qsTr("Name")
            placeholder: qsTr("name your armour…")
        }

        // ---- TN + Reduction --------------------------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 16
            rowSpacing: 12
            FormField {
                id: tnFF
                Layout.fillWidth: true
                label: qsTr("Armor TN")
                placeholder: qsTr("e.g. 5")
            }
            FormField {
                id: rdFF
                Layout.fillWidth: true
                label: qsTr("Reduction")
                placeholder: qsTr("e.g. 3")
            }
        }

        // ---- Notes -----------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Label {
                text: qsTr("NOTES")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.4
                color: Theme.heading
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 84
                color: Theme.parchmentBase
                border.color: notesArea.activeFocus ? dlg._accent : Theme.borderSubtle
                border.width: 1
                radius: 2
                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 6
                    clip: true
                    TextArea {
                        id: notesArea
                        wrapMode: TextArea.Wrap
                        placeholderText: qsTr("special qualities, provenance…")
                        color: Theme.ink
                        placeholderTextColor: Theme.inkFaint
                        font.family: Theme.fontBody
                        font.pixelSize: Theme.fsBody
                        background: Item {}
                    }
                }
            }
        }
    }

    // =================================================================
    // FormField -- a captioned, parchment-skinned text input.
    // =================================================================
    component FormField: ColumnLayout {
        id: ff
        property string label: ""
        property string placeholder: ""
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
            color: Theme.heading
        }
        TextField {
            id: input
            Layout.fillWidth: true
            implicitHeight: 34
            placeholderText: ff.placeholder
            color: Theme.ink
            placeholderTextColor: Theme.inkFaint
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            background: Rectangle {
                color: Theme.parchmentBase
                border.color: input.activeFocus ? dlg._accent : Theme.borderSubtle
                border.width: 1
                radius: 2
            }
        }
    }
}
