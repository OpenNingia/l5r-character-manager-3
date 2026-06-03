// Copyright (C) 2014-2026 Daniele Simonetti
// AddArmorDialog -- QML-native catalogue picker for the armour a samurai
// dons from the datapack. Replaces the armour path of the legacy QWidget
// ChooseItemDialog (l5r/dialogs/itemseldlg.py) without reusing any of its
// widgets. Opened from WeaponsSection's armour rail:
//     addArmorDlg.present()
//
// A two-pane brushed scroll, same vocabulary as AddWeaponDialog but
// trimmed (armour has no skill / category axis): the left column is the
// searchable list of armours, the right the chosen armour's plate -- the
// TN bonus it grants, the reduction it affords, its cost, and the effect
// prose. A character wears one armour at a time, so accepting simply
// replaces whatever was worn.
//
// Catalogue entry shape (from appCtrl.availableArmors()):
//   { name, tn:int, rd:int, cost:str, effect:str }
// A synthetic "No Armor (Clothing)" entry (clothing:true) is prepended so
// the dialog can return the character to an unarmored state (issue #379);
// the worn-armour card's take-off handle does the same from the rack.
// On accept the dialog calls appCtrl.wearArmor(name) -- or, for the
// clothing entry, appCtrl.removeArmor().
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property var _catalogue: []
    property var _selected: null
    property string _search: ""

    // --- derived --------------------------------------------------
    // Earth is the armourer's accent -- leather, lacquer, the weight you
    // bear. Distinct from the weapon rails (crimson / blue / amber).
    readonly property color _accent: Theme.ringEarth

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 820, 820)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 600, 600)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "鎧"
    title: qsTr("Don Armor")
    tagline: qsTr("take up the harness that will turn a blow")
    accent: _accent
    accentDark: Qt.darker(_accent, 1.3)
    acceptText: (dlg._selected && dlg._selected.clothing) ? qsTr("Remove Armor") : qsTr("Wear Armor")
    acceptGlyph: "鎧"
    acceptEnabled: dlg._selected !== null
    statusText: !dlg._selected ? qsTr("Choose an armour to wear.") : (dlg._selected.clothing ? qsTr("Return to wearing no armour.") : qsTr("Wear the %1.").arg(dlg._selected.name || ""))
    onAccepted: {
        if (!dlg._selected || !appCtrl)
            return;
        if (dlg._selected.clothing)
            appCtrl.removeArmor();
        else
            appCtrl.wearArmor(dlg._selected.name);
    }

    // The "unarmored" entry that heads the list (issue #379). A plain JS
    // object with clothing:true; the accept path clears the worn armour.
    readonly property var _clothingEntry: ({
            "name": qsTr("No Armor (Clothing)"),
            "clothing": true,
            "tn": 0,
            "rd": 0,
            "cost": "",
            "effect": qsTr("Unarmored — only your reflexes and bearing turn a blow.")
        })

    // --- entrypoint -----------------------------------------------
    function present() {
        var stock = (appCtrl && appCtrl.availableArmors) ? (appCtrl.availableArmors() || []) : [];
        dlg._catalogue = [dlg._clothingEntry].concat(stock);
        dlg._selected = null;
        dlg._search = "";
        searchField.text = "";
        dlg.open();
    }

    function _filteredCatalogue() {
        var needle = (dlg._search || "").toLowerCase();
        if (needle.length === 0)
            return dlg._catalogue;
        var out = [];
        for (var i = 0; i < dlg._catalogue.length; ++i) {
            var c = dlg._catalogue[i];
            if ((c.name || "").toLowerCase().indexOf(needle) >= 0)
                out.push(c);
        }
        return out;
    }

    padding: Theme.s1   // thin inset so the opaque two-pane body reveals the gold frame

    contentItem: ColumnLayout {
        spacing: 0

        // =============================================================
        // FILTER BAND -- search field across both panes.
        // =============================================================
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentInset
            implicitHeight: filterRow.implicitHeight + 16
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.heading
                opacity: 0.3
            }
            RowLayout {
                id: filterRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                Widgets.L5RSearchField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholder: qsTr("seek an armour by name…")
                    onTextChanged: dlg._search = text
                }
            }
        }

        // =============================================================
        // The body row -- list, divider, detail plate.
        // =============================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ---- LEFT PANE: the list --------------------------------
            Pane {
                Layout.fillHeight: true
                Layout.preferredWidth: 300
                padding: 0
                background: Rectangle {
                    color: Theme.parchmentSidebar
                    radius: 0
                    Widgets.RicePaperOverlay {}
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase

                ListView {
                    id: listView
                    anchors.fill: parent
                    clip: true
                    model: dlg._filteredCatalogue()
                    spacing: 0
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: AbstractButton {
                        id: row
                        width: listView.width
                        implicitHeight: 48
                        readonly property bool _active: dlg._selected && dlg._selected.name === modelData.name

                        onClicked: dlg._selected = modelData

                        background: Rectangle {
                            color: row._active ? Qt.tint(Theme.parchment, Qt.rgba(dlg._accent.r, dlg._accent.g, dlg._accent.b, 0.18)) : (row.hovered ? Qt.lighter(Theme.parchmentSidebar, 1.04) : "transparent")
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: row._active ? 3 : 0
                                color: dlg._accent
                            }
                        }

                        contentItem: RowLayout {
                            anchors.fill: parent
                            spacing: 8
                            Label {
                                Layout.leftMargin: row._active ? 13 : 11
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                text: modelData.name || qsTr("(unnamed)")
                                font.pixelSize: Theme.fsBody
                                font.weight: row._active ? Theme.wSemiBold : Theme.wRegular
                                color: Theme.ink
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.rightMargin: 12
                                Layout.alignment: Qt.AlignVCenter
                                visible: !modelData.clothing
                                text: qsTr("TN +%1 · RD %2").arg(modelData.tn || 0).arg(modelData.rd || 0)
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsCaption - 1
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.0
                                color: dlg._accent
                                opacity: 0.85
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: listView.count === 0
                        text: dlg._catalogue.length === 0 ? qsTr("the armoury is empty — import a datapack") : qsTr("nothing matches that brushstroke")
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.55
                        width: parent.width - 32
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ---- VERTICAL DIVIDER -----------------------------------
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.heading
                opacity: 0.35
            }

            // ---- RIGHT PANE: the plate ------------------------------
            Pane {
                Layout.fillWidth: true
                Layout.fillHeight: true
                padding: 0
                background: Rectangle {
                    color: Theme.parchment
                    radius: 0
                    Widgets.RicePaperOverlay {}
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase
                palette.buttonText: Theme.ink

                // Unselected state.
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    visible: dlg._selected === null
                    spacing: 4
                    Item {
                        Layout.fillHeight: true
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "鎧"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose an armour from the list at your left.")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsHeading1
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.4
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.heading
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        Layout.maximumWidth: 360
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("Its TN and reduction fold into your defence the moment you put it on.")
                        font.italic: true
                        font.pixelSize: Theme.fsBody
                        color: Theme.ink
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.7
                        wrapMode: Text.WordWrap
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }

                // Selected state.
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 22
                    visible: dlg._selected !== null
                    spacing: 10

                    Label {
                        Layout.fillWidth: true
                        text: dlg._selected ? dlg._selected.name : ""
                        font.family: Theme.fontDisplay
                        font.pixelSize: 22
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.0
                        color: Theme.heading
                        wrapMode: Text.WordWrap
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: dlg._accent
                        opacity: 0.5
                    }
                    Label {
                        visible: dlg._selected && (dlg._selected.cost || "").length > 0
                        text: dlg._selected ? qsTr("Cost: %1").arg(dlg._selected.cost) : ""
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.55
                    }

                    // Stat plate -- TN bonus + reduction (not for clothing).
                    Rectangle {
                        visible: !(dlg._selected && dlg._selected.clothing)
                        Layout.fillWidth: true
                        Layout.preferredHeight: statBody.implicitHeight + 22
                        color: Theme.parchmentInset
                        border.color: Theme.borderSubtle
                        border.width: 1
                        radius: 2
                        Row {
                            id: statBody
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 14
                            spacing: 36
                            StatItem {
                                label: qsTr("Armor TN")
                                value: dlg._selected ? ("+" + (dlg._selected.tn || 0)) : ""
                            }
                            StatItem {
                                label: qsTr("Reduction")
                                value: dlg._selected ? ("" + (dlg._selected.rd || 0)) : ""
                            }
                        }
                    }

                    ScrollView {
                        id: effectScroll
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth
                        Label {
                            width: effectScroll.availableWidth
                            text: dlg._selected && (dlg._selected.effect || "").length > 0 ? dlg._selected.effect : qsTr("No special effect recorded in the datapack.")
                            font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            color: Theme.ink
                            opacity: dlg._selected && (dlg._selected.effect || "").length > 0 ? 1.0 : 0.6
                            font.italic: !(dlg._selected && (dlg._selected.effect || "").length > 0)
                        }
                    }
                }
            }
        }
    }

    // =================================================================
    // StatItem -- one captioned figure on the armour plate.
    // =================================================================
    component StatItem: Column {
        property string label: ""
        property string value: ""
        spacing: 0
        Label {
            text: label.toUpperCase()
            font.family: Theme.fontDisplay
            font.pixelSize: 9
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.2
            color: Theme.inkMuted
        }
        Label {
            text: value
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatSmall
            font.weight: Theme.wRegular
            font.features: Theme.tabularNumbers
            color: Theme.heading
        }
    }
}
