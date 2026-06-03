// Copyright (C) 2014-2026 Daniele Simonetti
// CustomWeaponDialog -- QML-native form for forging a custom weapon or
// re-statting one already on the rack. Replaces the legacy QWidget
// CustomWeaponDialog (l5r/dialogs/customitems.py) without reusing any of
// its widgets. Two entrypoints from WeaponsSection:
//     customWeaponDlg.presentAdd()        // forge a new weapon
//     customWeaponDlg.presentEdit(item)   // re-stat an existing one
//
// In ADD mode a "base weapon" dropdown seeds the form from a catalogue
// template -- crucially it also carries the skill, trait and category
// tags the new weapon needs to roll and file correctly (the legacy
// dialog always began from a base for the same reason). The player then
// overrides the name and figures. In EDIT mode the base dropdown is
// hidden and the skill/category stay fixed; only the editable figures
// change.
//
// On accept:
//   add  -> appCtrl.addCustomWeapon({ base, name, dr, drAlt, range,
//                                     strength, minStr, notes })
//   edit -> appCtrl.editWeapon(id, { name, dr, drAlt, range, strength,
//                                    minStr, notes })
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property bool _editMode: false
    property string _weaponId: ""
    property string _baseName: ""
    property var _catalogue: []

    // --- derived --------------------------------------------------
    readonly property color _accent: Theme.accent

    // --- size -----------------------------------------------------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 560, 560)
    padding: Theme.s5

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "刀"
    title: dlg._editMode ? qsTr("Edit Weapon") : qsTr("Forge a Weapon")
    tagline: dlg._editMode ? qsTr("re-stat a weapon already on your rack") : qsTr("temper a weapon to your own measure")
    accent: _accent
    accentDark: Theme.accentMuted
    acceptText: dlg._editMode ? qsTr("Save") : qsTr("Forge")
    acceptGlyph: "刀"
    acceptEnabled: nameFF.text.trim().length > 0
    statusText: dlg._editMode ? qsTr("Save your changes to this weapon.") : qsTr("A custom weapon keeps the skill and class of its base.")
    onAccepted: {
        if (!appCtrl)
            return;
        var payload = {
            "name": nameFF.text,
            "dr": drFF.text,
            "drAlt": drAltFF.text,
            "range": rangeFF.text,
            "strength": strengthFF.text,
            "minStr": minStrFF.text,
            "notes": notesArea.text
        };
        if (dlg._editMode) {
            appCtrl.editWeapon(dlg._weaponId, payload);
        } else {
            payload.base = dlg._baseName;
            appCtrl.addCustomWeapon(payload);
        }
    }

    // --- entrypoints ----------------------------------------------
    function presentAdd() {
        dlg._editMode = false;
        dlg._weaponId = "";
        dlg._catalogue = (appCtrl && appCtrl.availableWeapons) ? (appCtrl.availableWeapons() || []) : [];
        dlg._clearFields();
        // Seed from the first base template so the new weapon inherits a
        // skill + category (a tag-less weapon would file nowhere).
        if (dlg._catalogue.length > 0) {
            baseCombo.currentIndex = 0;
            dlg._applyBase(dlg._catalogue[0]);
        } else {
            dlg._baseName = "";
        }
        dlg.open();
        nameFF.forceActiveFocus();
    }

    function presentEdit(item) {
        if (!item)
            return;
        dlg._editMode = true;
        dlg._weaponId = item.id || "";
        dlg._baseName = "";
        nameFF.text = item.name || "";
        drFF.text = item.dr || "";
        drAltFF.text = item.drAlt || "";
        rangeFF.text = item.range || "";
        strengthFF.text = item.strength || "";
        minStrFF.text = item.minStr || "";
        notesArea.text = item.description || "";
        dlg.open();
        nameFF.forceActiveFocus();
    }

    function _clearFields() {
        nameFF.text = "";
        drFF.text = "";
        drAltFF.text = "";
        rangeFF.text = "";
        strengthFF.text = "";
        minStrFF.text = "";
        notesArea.text = "";
    }

    function _applyBase(rec) {
        if (!rec)
            return;
        dlg._baseName = rec.name || "";
        nameFF.text = rec.name || "";
        drFF.text = rec.dr || "";
        drAltFF.text = rec.drAlt || "";
        rangeFF.text = rec.range || "";
        strengthFF.text = rec.strength || "";
        minStrFF.text = rec.minStr || "";
        notesArea.text = rec.effect || "";
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: 14

        // ---- Base weapon (add mode only) -------------------------
        ColumnLayout {
            Layout.fillWidth: true
            visible: !dlg._editMode
            spacing: 3

            Label {
                text: qsTr("BASE WEAPON")
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
                text: qsTr("Seeds the figures below — and fixes the skill and class your weapon rolls with.")
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
            placeholder: qsTr("name your weapon…")
        }

        // ---- Stat grid -------------------------------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 16
            rowSpacing: 12

            FormField {
                id: drFF
                Layout.fillWidth: true
                label: qsTr("Primary DR")
                placeholder: qsTr("e.g. 3k2")
            }
            FormField {
                id: drAltFF
                Layout.fillWidth: true
                label: qsTr("Secondary DR")
                placeholder: qsTr("e.g. 2k2")
            }
            FormField {
                id: rangeFF
                Layout.fillWidth: true
                label: qsTr("Range")
                placeholder: qsTr("e.g. 250'")
            }
            FormField {
                id: strengthFF
                Layout.fillWidth: true
                label: qsTr("Weapon Strength")
                placeholder: qsTr("e.g. 3")
            }
            FormField {
                id: minStrFF
                Layout.fillWidth: true
                label: qsTr("Minimum Strength")
                placeholder: qsTr("e.g. 2")
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
                        placeholderText: qsTr("effect, materials, provenance…")
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
    // FormField -- a captioned, parchment-skinned text input. `text` is
    // a two-way alias of the field; forceActiveFocus() forwards to it.
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
