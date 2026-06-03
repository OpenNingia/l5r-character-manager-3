// Copyright (C) 2014-2026 Daniele Simonetti
// AddWeaponDialog -- QML-native catalogue picker for arming the
// character from the datapack armoury. Replaces the weapon path of the
// legacy QWidget ChooseItemDialog (l5r/dialogs/itemseldlg.py) without
// reusing any of its widgets. Opened from WeaponsSection:
//     addWeaponDlg.present()
//
// A two-pane brushed scroll, kakemono-aspect (taller than wide). The
// left column is the searchable catalogue -- each row carries a crimson
// category dot, the weapon name, and its governing skill as a subtitle
// (the legacy dialog's primary axis). The right column is the chosen
// weapon's plate: a category chip, the damage rating(s), range /
// strength figures, cost, and the effect prose. The footer plaque names
// the weapon; the Add button enables once one is chosen (there is no
// eligibility gate -- a samurai may carry whatever they can lay hands
// on).
//
// Catalogue entry shape (from appCtrl.availableWeapons()):
//   { name, skill,
//     categories: ["melee"],   // melee / ranged / arrow
//     dr, drAlt, range, strength, minStr, cost, effect }
// On accept the dialog calls appCtrl.addWeapon(name).
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
    property string _categoryFilter: ""   // "" = all; else melee/ranged/arrow

    // Category-filter options for the dropdown beside the search box.
    readonly property var _categoryOptions: [{
            "key": "",
            "label": qsTr("All Weapons")
        }, {
            "key": "melee",
            "label": qsTr("Melee")
        }, {
            "key": "ranged",
            "label": qsTr("Ranged")
        }, {
            "key": "arrow",
            "label": qsTr("Arrows")
        }]

    // --- derived --------------------------------------------------
    // Crimson is the warrior's accent -- the blade, the active choice.
    readonly property color _accent: Theme.accent
    readonly property color _accentSoft: Theme.accentSoft

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 880, 880)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 640, 640)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "刀"
    title: qsTr("Add a Weapon")
    tagline: qsTr("draw from the armoury what your hand can hold")
    accent: _accent
    accentDark: Theme.accentMuted
    acceptText: qsTr("Add Weapon")
    acceptGlyph: "刀"
    acceptEnabled: dlg._selected !== null
    statusText: dlg._selected ? qsTr("Add the %1 to your weapons.").arg(dlg._selected.name || "") : qsTr("Choose a weapon from the armoury.")
    onAccepted: {
        if (dlg._selected && appCtrl)
            appCtrl.addWeapon(dlg._selected.name);
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        dlg._refreshCatalogue();
        dlg._selected = null;
        dlg._search = "";
        dlg._categoryFilter = "";
        categoryCombo.currentIndex = 0;
        dlg.open();
    }

    function _refreshCatalogue() {
        dlg._catalogue = (appCtrl && appCtrl.availableWeapons) ? (appCtrl.availableWeapons() || []) : [];
    }

    // Applies both the category dropdown and the search box. A weapon
    // matches a category filter if that category is among its tags, so a
    // throwable melee weapon (melee+ranged) is discoverable under both
    // the Melee and the Ranged filter.
    function _filteredCatalogue() {
        var needle = (dlg._search || "").toLowerCase();
        var cat = dlg._categoryFilter;
        var out = [];
        for (var i = 0; i < dlg._catalogue.length; ++i) {
            var c = dlg._catalogue[i];
            if (cat.length > 0 && (!c.categories || c.categories.indexOf(cat) < 0))
                continue;
            if (needle.length > 0) {
                var hay = ((c.name || "") + " " + (c.skill || "")).toLowerCase();
                if (hay.indexOf(needle) < 0)
                    continue;
            }
            out.push(c);
        }
        return out;
    }

    function _catLabelForKey(k) {
        if (k === "melee")
            return qsTr("Melee");
        if (k === "ranged")
            return qsTr("Ranged");
        if (k === "arrow")
            return qsTr("Arrow");
        return "";
    }

    // Every category the weapon names, joined -- honest for a throwable
    // weapon that turns up under both the Melee and Ranged filters.
    function _categoryTag(c) {
        if (!c || !c.categories)
            return "";
        var labels = [];
        for (var i = 0; i < c.categories.length; ++i) {
            var l = dlg._catLabelForKey(c.categories[i]);
            if (l.length > 0)
                labels.push(l);
        }
        return labels.join(" · ");
    }

    // A representative hue for colour-coding the row: a throwable melee
    // weapon reads crimson (melee), a bow blue (ranged), an arrow amber.
    function _catColor(c) {
        if (!c || !c.categories)
            return dlg._accent;
        if (c.categories.indexOf("melee") >= 0)
            return Theme.weaponCategoryColor("melee");
        if (c.categories.indexOf("ranged") >= 0)
            return Theme.weaponCategoryColor("ranged");
        if (c.categories.indexOf("arrow") >= 0)
            return Theme.weaponCategoryColor("arrow");
        return dlg._accent;
    }

    padding: Theme.s1   // thin inset so the opaque two-pane body reveals the gold frame

    contentItem: ColumnLayout {
        spacing: 0

        // =============================================================
        // FILTER BAND -- search field spanning both panes.
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
                spacing: 12

                Widgets.L5RSearchField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholder: qsTr("seek a weapon by name or skill…")
                    onTextChanged: dlg._search = text
                }
                Widgets.L5RComboBox {
                    id: categoryCombo
                    Layout.preferredWidth: 170
                    accent: dlg._accent
                    model: dlg._categoryOptions
                    textRole: "label"
                    onActivated: index => dlg._categoryFilter = dlg._categoryOptions[index].key
                }
            }
        }

        // =============================================================
        // The body row -- catalogue list, divider, detail plate.
        // =============================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // =========================================================
            // LEFT PANE -- the catalogue list.
            // =========================================================
            Pane {
                id: catalogPane
                Layout.fillHeight: true
                Layout.preferredWidth: 340
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
                    id: catalogView
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
                        width: catalogView.width
                        implicitHeight: 52
                        readonly property bool _active: dlg._selected && dlg._selected.name === modelData.name && dlg._selected.skill === modelData.skill

                        onClicked: dlg._selected = modelData

                        background: Rectangle {
                            color: row._active ? dlg._accentSoft : (row.hovered ? Qt.lighter(Theme.parchmentSidebar, 1.04) : "transparent")
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

                            // Category dot -- colour-codes the weapon's
                            // kind (melee crimson / ranged blue / arrow amber).
                            Rectangle {
                                Layout.leftMargin: row._active ? 13 : 11
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 8
                                implicitHeight: 8
                                radius: 4
                                color: dlg._catColor(modelData)
                                opacity: 0.9
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: modelData.name || qsTr("(unnamed)")
                                    font.pixelSize: Theme.fsBody
                                    font.weight: row._active ? Theme.wSemiBold : Theme.wRegular
                                    color: Theme.ink
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    visible: (modelData.skill || "").length > 0
                                    text: (modelData.skill || "").toUpperCase()
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsCaption - 1
                                    font.weight: Theme.wSemiBold
                                    font.letterSpacing: 1.2
                                    color: Theme.inkMuted
                                    elide: Text.ElideRight
                                }
                            }
                            // Category tag -- all categories the weapon
                            // names (e.g. "MELEE · RANGED" for a thrown blade).
                            Label {
                                Layout.rightMargin: 12
                                Layout.alignment: Qt.AlignVCenter
                                text: dlg._categoryTag(modelData).toUpperCase()
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsCaption - 1
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.0
                                color: dlg._catColor(modelData)
                                opacity: 0.85
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: catalogView.count === 0
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

            // =========================================================
            // VERTICAL DIVIDER.
            // =========================================================
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.heading
                opacity: 0.35
            }

            // =========================================================
            // RIGHT PANE -- the chosen weapon's plate.
            // =========================================================
            Pane {
                id: detailPane
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
                palette.alternateBase: Theme.parchmentInset
                palette.placeholderText: Theme.inkFaint
                palette.buttonText: Theme.ink

                // ---- Unselected state ----------------------------------
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
                        text: "刀"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose a weapon from the armoury at your left.")
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
                        Layout.maximumWidth: 380
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("Its attack and damage rolls are figured from your traits and the weapon's skill once it is on your rack.")
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

                // ---- Selected state ------------------------------------
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 22
                    visible: dlg._selected !== null
                    spacing: 10

                    // Title.
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

                    // Meta row -- skill + cost.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Label {
                            visible: dlg._selected && (dlg._selected.skill || "").length > 0
                            text: dlg._selected ? (dlg._selected.skill || "") : ""
                            font.italic: true
                            font.pixelSize: Theme.fsBody
                            color: Theme.ink
                            opacity: 0.7
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Label {
                            visible: dlg._selected && (dlg._selected.cost || "").length > 0
                            text: dlg._selected ? qsTr("Cost: %1").arg(dlg._selected.cost) : ""
                            font.italic: true
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.55
                        }
                    }

                    // Tag badges -- the weapon's full tag set (category
                    // tags tinted to their hue, descriptors in neutral ink).
                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        visible: dlg._selected && dlg._selected.tags && dlg._selected.tags.length > 0
                        Repeater {
                            model: dlg._selected ? (dlg._selected.tags || []) : []
                            delegate: TagBadge {
                                tag: modelData
                            }
                        }
                    }

                    // Stat plate -- the figures the weapon carries on its own.
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: statBody.implicitHeight + 22
                        color: Theme.parchmentInset
                        border.color: Theme.borderSubtle
                        border.width: 1
                        radius: 2

                        Flow {
                            id: statBody
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 28

                            StatItem {
                                label: qsTr("Primary DR")
                                value: dlg._selected ? dlg._selected.dr : ""
                            }
                            StatItem {
                                label: qsTr("Secondary DR")
                                value: dlg._selected ? dlg._selected.drAlt : ""
                            }
                            StatItem {
                                label: qsTr("Range")
                                value: dlg._selected ? dlg._selected.range : ""
                            }
                            StatItem {
                                label: qsTr("Strength")
                                value: dlg._selected ? dlg._selected.strength : ""
                            }
                            StatItem {
                                label: qsTr("Min. Strength")
                                value: dlg._selected ? dlg._selected.minStr : ""
                            }
                        }
                    }

                    // Effect prose -- scrolls if long.
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
        }   // body RowLayout
    }

    // =================================================================
    // TagBadge -- one weapon tag as a small outlined chip. Category tags
    // (melee/ranged/arrow) take their hue; descriptors (small, large,
    // samurai, peasant, ninja…) read in neutral ink.
    // =================================================================
    component TagBadge: Rectangle {
        id: badge
        property string tag: ""
        readonly property bool _isCat: tag === "melee" || tag === "ranged" || tag === "arrow"
        readonly property color _c: _isCat ? Theme.weaponCategoryColor(tag) : Theme.inkMuted
        radius: 3
        color: "transparent"
        border.width: 1
        border.color: _c
        opacity: _isCat ? 0.9 : 0.55
        implicitWidth: badgeLabel.implicitWidth + 12
        implicitHeight: badgeLabel.implicitHeight + 4
        Label {
            id: badgeLabel
            anchors.centerIn: parent
            text: badge.tag.toUpperCase()
            font.family: Theme.fontDisplay
            font.pixelSize: 9
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.0
            color: badge._c
        }
    }

    // =================================================================
    // StatItem -- one captioned figure on the weapon plate. Hidden when
    // its value is absent or a sentinel ("N/A" / "0k0").
    // =================================================================
    component StatItem: ColumnLayout {
        property string label: ""
        property string value: ""
        spacing: 0
        visible: value && value.length > 0 && value !== "N/A" && value !== "0k0"

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
