// Copyright (C) 2014-2026 Daniele Simonetti
// Arms & Armor section (刀 -- tō, "blade") -- replaces the legacy
// three-table l5r/ui/tabs/weapons.py (melee / ranged / arrows) and folds
// in the armour worn (the legacy "Outfit" menu's Wear Armor / Custom
// Armor), since the QML taxonomy groups all combat gear here.
//
// Design intent: "The Weapon Rack." A samurai's arms are laid out by
// the way they are used -- the armour worn, then the blades drawn in
// close, the bows loosed at range, and the arrows that feed them. So the
// page reads as a rack with labelled rails. Each weapon is a card: the
// crimson rail of the warrior down its left edge, the name and its
// governing skill at the top, and on the right the figures the player
// actually shouts at the table -- the attack and damage rolls (in gold,
// recomputed live from traits + skill + modifiers), the damage rating,
// range and strength. Arrows carry a quantity stepper instead. Click a
// card to read its effect text inline.
//
// The armour rail heads the rack: a character wears at most one armour,
// shown as an earth-toned card with its TN bonus and reduction, an edit
// handle, and a take-off (remove) handle (issue #379). When unarmoured the
// rail shows a quiet hint.
//
// Affordances mirror the legacy toolbar/menu:
//   "＋ Wear" / "＋ Custom"  (armour rail) -> AddArmorDialog / CustomArmorDialog
//   "＋ Add Weapon"          -> AddWeaponDialog   (browse the armoury catalogue)
//   "＋ Custom"              -> CustomWeaponDialog (forge / re-stat a weapon)
// Each non-arrow weapon card carries a hover-revealed edit handle (re-opens
// the custom dialog seeded with that weapon) and every card a remove handle.
//
// Data contract expected from the proxy (degrades to the empty-state):
//   pcProxy.weapons: [
//     { id:          "0x...",      // session-stable; keys edit/remove/qty
//       name:        "Katana",
//       skill:       "Kenjutsu",   // weapon-skill display name
//       categories:  ["melee"],         // every rail its tags name
//       dr:          "3k2",  drAlt: "2k2",
//       range:       "",  strength: "",  minStr: "2",
//       qty:         1,
//       baseAtk:     "5k3",  modAtk: "6k3",
//       baseDmg:     "7k2",  modDmg: "7k2",
//       description: "…" },        // effect / notes; may be ""
//     ...
//   ]
// Required controller methods on appCtrl:
//   addWeapon(name)                       (AddWeaponDialog)
//   addCustomWeapon({base,name,dr,drAlt,range,strength,minStr,notes})
//   editWeapon(id, {name,dr,drAlt,range,strength,minStr,notes})
//   removeWeapon(id)
//   changeWeaponQty(id, delta)
//   availableWeapons() -> [{ name, skill, categories, dr, drAlt, range,
//                            strength, minStr, cost, effect }]  (dialogs)
// Armour contract:
//   pcProxy.armor: { worn: bool, name, tn:int, rd:int, desc }
//   availableArmors() -> [{ name, tn, rd, cost, effect }]  (dialogs)
//   wearArmor(name)   wearCustomArmor({name,tn,rd,notes})
//   editArmor({name,tn,rd,notes})   removeArmor()
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../dialogs" as Dialogs
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // -----------------------------------------------------------------
    // Defensive binding -- proxy may be absent on first paint or under
    // the offscreen preview tool (which binds a null pcProxy).
    // -----------------------------------------------------------------
    // Read pcProxy.weapons once: the getter rebuilds the whole list (and
    // recomputes every weapon's attack/damage roll) on each call, so the
    // old `(pcProxy && pcProxy.weapons) ? pcProxy.weapons : []` form paid
    // for it twice per re-projection.
    readonly property var _weapons: pcProxy ? pcProxy.weapons : []
    readonly property bool _hasWeapons: _weapons.length > 0

    // The worn armour (at most one). Earth-toned, heads the rack.
    readonly property var _armor: (pcProxy && pcProxy.armor) ? pcProxy.armor : ({
                                                                                    "worn": false,
                                                                                    "name": "",
                                                                                    "tn": 0,
                                                                                    "rd": 0,
                                                                                    "desc": ""
                                                                                })
    property bool _armorExpanded: false

    // The three combat rails, in reading order. A weapon appears on every
    // rail whose key is in its `categories` (faithful to the legacy, where
    // a weapon showed in each table it was tagged for).
    readonly property var _categoryDefs: [{
            "key": "melee",
            "label": qsTr("Melee")
        }, {
            "key": "ranged",
            "label": qsTr("Ranged")
        }, {
            "key": "arrow",
            "label": qsTr("Arrows")
        }]

    // Id of the currently-expanded weapon, or "" for none. A single id
    // (not per-card toggles) so opening one collapses the previous --
    // mirrors Skills / Kata.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    // Weapons on one rail: every weapon whose tags name this category. A
    // throwable weapon (tagged melee+ranged) shows on both the Melee rail
    // (with its DR/ATK/DMG) and the Ranged rail (with its thrown range/
    // ATK) -- the same weapon in two combat modes, as the legacy UI did.
    function _forCategory(cat) {
        var out = [];
        for (var i = 0; i < _weapons.length; ++i) {
            var w = _weapons[i];
            if (w.categories && w.categories.indexOf(cat) >= 0)
                out.push(w);
        }
        out.sort(function (a, b) {
                return (a.name || "").localeCompare(b.name || "");
            });
        return out;
    }

    // "N/A" / "0k0" are the sentinels weapon_outfit_from_db and the custom
    // parser leave behind for an absent secondary DR -- don't show a chip
    // for a rating the weapon doesn't have.
    function _meaningful(v) {
        return v && v.length > 0 && v !== "N/A" && v !== "0k0";
    }

    function _requestRemove(item) {
        if (item && appCtrl)
            appCtrl.removeWeapon(item.id);
    }

    function _requestEdit(item) {
        if (item)
            customWeaponDlg.presentEdit(item);
    }

    function _requestRemoveArmor() {
        if (appCtrl)
            appCtrl.removeArmor();
    }
    function _requestEditArmor() {
        customArmorDlg.presentEdit(section._armor);
    }

    // -----------------------------------------------------------------
    // Dialogs -- all authored fresh in QML (no QWidget reuse).
    // -----------------------------------------------------------------
    Dialogs.AddWeaponDialog {
        id: addWeaponDlg
    }
    Dialogs.CustomWeaponDialog {
        id: customWeaponDlg
    }
    Dialogs.AddArmorDialog {
        id: addArmorDlg
    }
    Dialogs.CustomArmorDialog {
        id: customArmorDlg
    }

    // -----------------------------------------------------------------
    // The whole rack lives on one parchment SheetPanel. Being a Pane it
    // forces ink-on-paper palette onto every descendant Label, so the
    // cards stay legible even on a dark OS theme.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Arms & Armor")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ===== ARMOR section. Its Wear / Custom actions ride the rail
            // banner, directly above the worn-armour card. =====
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                // Earth-toned rail banner + Wear / Custom affordances.
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.s2
                    Rectangle {
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 10
                        color: Theme.ringEarth
                    }
                    Label {
                        text: qsTr("Armor").toUpperCase()
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsBody
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 2.4
                        color: Theme.ringEarth
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: Theme.ringEarth
                        opacity: 0.30
                    }
                    AddAffordance {
                        text: qsTr("＋  Wear")
                        onTriggered: addArmorDlg.present()
                    }
                    AddAffordance {
                        text: qsTr("＋  Custom")
                        onTriggered: customArmorDlg.presentAdd()
                    }
                }

                // Worn armour card.
                ArmorCard {
                    Layout.fillWidth: true
                    visible: section._armor.worn
                }

                // Unarmoured hint.
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    visible: !section._armor.worn
                    color: Theme.parchmentInset
                    border.color: Theme.borderSubtle
                    border.width: 1
                    radius: 2
                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 3
                        color: Theme.ringEarth
                        opacity: 0.45
                    }
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 14
                        text: qsTr("No armour worn — you fight unarmored.")
                        font.italic: true
                        font.pixelSize: Theme.fsBody
                        color: Theme.ink
                        opacity: 0.6
                    }
                }
            }

            // ---- Separator between the armour and weapons sections ---
            Widgets.OrnateDivider {
                Layout.fillWidth: true
                Layout.topMargin: 6
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }

            // ===== WEAPONS section. Its Add Weapon / Custom actions sit
            // on the header row above the rails. =====
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s2

                Label {
                    text: qsTr("the arms you carry, ready to be drawn")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasWeapons
                    text: section._weapons.length === 1 ? qsTr("1 weapon") : qsTr("%1 weapons").arg(section._weapons.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }
                AddAffordance {
                    text: qsTr("＋  Add Weapon")
                    onTriggered: addWeaponDlg.present()
                }
                AddAffordance {
                    text: qsTr("＋  Custom")
                    onTriggered: customWeaponDlg.presentAdd()
                }
            }

            // ---- Empty state -----------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 180
                Layout.topMargin: 4
                visible: !section._hasWeapons
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    Label {
                        anchors.centerIn: parent
                        text: "刀"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: Theme.accent
                        opacity: 0.14
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Your weapon rack stands empty.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading1
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.4
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 460
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("Draw a blade from the armoury, or forge one of your own. Its attack and damage rolls are figured from your traits and skill.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The three rails -------------------------------------
            Repeater {
                model: section._categoryDefs
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    spacing: 4

                    readonly property string _catKey: modelData.key
                    readonly property color _catColor: Theme.weaponCategoryColor(_catKey)
                    readonly property var _rows: section._forCategory(_catKey)
                    readonly property bool _hasRows: _rows.length > 0

                    // Only render a rail that bears weapons -- weapons
                    // categories are not canonical the way the five rings
                    // are, so an empty rail is just noise.
                    visible: _hasRows

                    // Category-coloured rail banner.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.s2
                        Rectangle {
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 10
                            color: _catColor
                        }
                        Label {
                            text: modelData.label.toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsBody
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 2.4
                            color: _catColor
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: _catColor
                            opacity: 0.30
                        }
                        Label {
                            text: _rows.length
                            font.family: Theme.fontStat
                            font.pixelSize: Theme.fsCaption
                            font.features: Theme.tabularNumbers
                            color: _catColor
                            opacity: 0.85
                        }
                    }

                    // Cards.
                    Repeater {
                        model: _rows
                        delegate: WeaponCard {
                            Layout.fillWidth: true
                            item: modelData
                            category: _catKey
                        }
                    }
                }
            }

            // ---- Footer coda -----------------------------------------
            Widgets.OrnateDivider {
                visible: section._hasWeapons
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                visible: section._hasWeapons
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: section._weapons.length === 1 ? qsTr("one weapon at the ready") : qsTr("%1 weapons at the ready").arg(section._weapons.length)
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 2.0
                color: Theme.heading
                opacity: 0.70
            }
        }
    }

    // =================================================================
    // AddAffordance -- the gold-outlined ink-on-paper button shared by
    // the two rack actions. Same vocabulary as Skills' "+ New Skill" and
    // Kata's "+ Learn a Kata".
    // =================================================================
    component AddAffordance: Button {
        id: addBtn
        signal triggered
        onClicked: addBtn.triggered()
        topPadding: 5
        bottomPadding: 5
        leftPadding: 14
        rightPadding: 14

        contentItem: Label {
            text: addBtn.text
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsBody
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.6
            color: Theme.heading
            opacity: addBtn.hovered ? 1.0 : 0.88
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            // Gold wash derived from the heading token (not a free hex) --
            // warms on hover, deepens on press.
            color: addBtn.down ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.18) : addBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.10) : "transparent"
            border.width: 1
            border.color: Theme.heading
            radius: 1
        }
    }

    // =================================================================
    // TagBadge -- one weapon tag as a small outlined chip. Category tags
    // (melee/ranged/arrow) take their rail hue; descriptors (small,
    // large, samurai, peasant, ninja…) read in neutral ink.
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
            font.pixelSize: Theme.fsMicro
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.0
            color: badge._c
        }
    }

    // =================================================================
    // StatCell -- a captioned figure (DR, ATK, DMG, Range, Strength…).
    // Caption in small-caps Cinzel, value in EB Garamond. Roll-and-keep
    // values are gold (the dice you shout); plain numbers stay ink.
    // =================================================================
    component StatCell: ColumnLayout {
        property string label: ""
        property string value: ""
        property bool roll: false
        property string tip: ""
        spacing: 0
        visible: value.length > 0

        Label {
            text: label.toUpperCase()
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsMicro
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.2
            color: Theme.inkMuted
            horizontalAlignment: Text.AlignRight
            Layout.fillWidth: true
        }
        Label {
            text: value
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatSmall
            font.weight: Theme.wRegular
            font.features: Theme.tabularNumbers
            color: roll ? Theme.heading : Theme.ink
            horizontalAlignment: Text.AlignRight
            Layout.fillWidth: true
            HoverHandler {
                id: cellHover
                enabled: tip.length > 0
            }
            ToolTip.visible: tip.length > 0 && cellHover.hovered
            ToolTip.text: tip
        }
    }

    // =================================================================
    // ArmorCard -- the single worn armour. Earth-toned to set it apart
    // from the weapon rails; shows its TN bonus + reduction, a
    // hover-revealed edit handle (re-stat), and a take-off handle that
    // returns the character to unarmoured (issue #379). Click to read its
    // notes inline.
    // =================================================================
    component ArmorCard: Rectangle {
        id: acard
        readonly property color _c: Theme.ringEarth
        readonly property string _name: section._armor.name && section._armor.name.length > 0 ? section._armor.name : qsTr("(unnamed armour)")
        readonly property string _desc: section._armor.desc || ""
        readonly property bool _hasDesc: _desc.length > 0
        readonly property bool _expanded: section._armorExpanded

        implicitHeight: acardBody.implicitHeight + 18
        color: acHover.hovered || _expanded ? Theme.parchmentBase : Theme.parchmentInset
        border.color: acHover.hovered || _expanded ? Qt.darker(_c, 1.2) : Theme.borderSubtle
        border.width: 1
        radius: 2

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: 120
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: acard._c
            opacity: 0.9
        }

        HoverHandler {
            id: acHover
            cursorShape: acard._hasDesc ? Qt.PointingHandCursor : Qt.ArrowCursor
        }
        TapHandler {
            enabled: acard._hasDesc
            onTapped: section._armorExpanded = !section._armorExpanded
        }

        ColumnLayout {
            id: acardBody
            anchors.fill: parent
            anchors.margins: 9
            anchors.leftMargin: 13
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s4

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: acard._name
                        font.pixelSize: Theme.fsBody + 2
                        font.weight: Theme.wRegular
                        color: Theme.ink
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        text: qsTr("Worn").toUpperCase()
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsCaption
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.4
                        color: acard._c
                        opacity: 0.9
                    }
                }

                // TN + reduction figures.
                RowLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: Theme.s4
                    StatCell {
                        label: qsTr("Armor TN")
                        value: "+" + (section._armor.tn || 0)
                        roll: false
                        Layout.minimumWidth: 34
                    }
                    StatCell {
                        label: qsTr("Reduction")
                        value: "" + (section._armor.rd || 0)
                        roll: false
                        Layout.minimumWidth: 34
                    }
                }

                // Expand chevron.
                Label {
                    visible: acard._hasDesc
                    Layout.alignment: Qt.AlignVCenter
                    text: acard._expanded ? "▲" : "▼"
                    font.pixelSize: 9
                    color: Theme.ink
                    opacity: 0.45
                }

                // Edit handle.
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter
                    AbstractButton {
                        id: armorEditBtn
                        anchors.fill: parent
                        visible: acHover.hovered || armorEditBtn.hovered
                        onClicked: section._requestEditArmor()
                        background: Rectangle {
                            radius: 11
                            color: armorEditBtn.hovered ? Theme.heading : "transparent"
                            border.color: Theme.heading
                            border.width: 1
                            opacity: armorEditBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "✎"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: armorEditBtn.hovered ? Theme.whiteWash : Theme.heading
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: qsTr("Edit this armour")
                    }
                }

                // Take-off handle (issue #379).
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter
                    AbstractButton {
                        id: armorRemoveBtn
                        anchors.fill: parent
                        visible: acHover.hovered || armorRemoveBtn.hovered
                        onClicked: section._requestRemoveArmor()
                        background: Rectangle {
                            radius: 11
                            color: armorRemoveBtn.hovered ? Theme.accent : "transparent"
                            border.color: Theme.accent
                            border.width: 1
                            opacity: armorRemoveBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "✕"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: armorRemoveBtn.hovered ? Theme.whiteWash : Theme.accent
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: qsTr("Take off this armour")
                    }
                }
            }

            // Expanded notes.
            ColumnLayout {
                Layout.fillWidth: true
                visible: acard._expanded && acard._hasDesc
                spacing: 4
                Rectangle {
                    Layout.fillWidth: true
                    Layout.leftMargin: 4
                    Layout.preferredHeight: 1
                    color: acard._c
                    opacity: 0.25
                }
                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 4
                    Layout.bottomMargin: 2
                    text: acard._desc
                    textFormat: Text.PlainText
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    wrapMode: Text.WordWrap
                    opacity: 0.92
                }
            }
        }
    }

    // =================================================================
    // WeaponCard -- one weapon on one rail. Renders the stat figures
    // appropriate to its category; arrows get a quantity stepper, melee
    // and ranged get a hover-revealed edit handle, all get remove.
    // =================================================================
    component WeaponCard: Rectangle {
        id: card
        property var item: null
        property string category: "melee"

        // The rail's hue -- this card colour-codes to the category it is
        // shown under (a throwable on the Ranged rail reads blue there,
        // crimson on the Melee rail).
        readonly property color _catColor: Theme.weaponCategoryColor(category)
        readonly property string _name: (item && item.name) ? item.name : qsTr("(unnamed weapon)")
        readonly property string _skill: (item && item.skill) ? item.skill : ""
        readonly property string _desc: (item && item.description) ? item.description : ""
        readonly property bool _hasDesc: _desc.length > 0
        readonly property bool _expanded: !!(item && section._expandedId === item.id)
        readonly property bool _isArrow: category === "arrow"

        // The captioned figures for this card's category.
        readonly property var _cells: {
            if (!item)
                return [];
            if (category === "ranged") {
                var rc = [];
                if (section._meaningful(item.range))
                    rc.push({
                                "label": qsTr("Range"),
                                "value": item.range,
                                "roll": false,
                                "tip": ""
                            });
                if (section._meaningful(item.strength))
                    rc.push({
                                "label": qsTr("Str"),
                                "value": item.strength,
                                "roll": false,
                                "tip": ""
                            });
                if (section._meaningful(item.minStr))
                    rc.push({
                                "label": qsTr("Min Str"),
                                "value": item.minStr,
                                "roll": false,
                                "tip": ""
                            });
                rc.push({
                            "label": qsTr("Atk"),
                            "value": item.modAtk,
                            "roll": true,
                            "tip": qsTr("Base %1  ·  Mod %2").arg(item.baseAtk || "—").arg(item.modAtk || "—")
                        });
                return rc;
            }
            if (category === "arrow")
                return [{
                            "label": qsTr("DR"),
                            "value": item.dr,
                            "roll": true,
                            "tip": ""
                        }];
            // melee
            var mc = [{
                    "label": qsTr("DR"),
                    "value": item.dr,
                    "roll": true,
                    "tip": ""
                }];
            if (section._meaningful(item.drAlt))
                mc.push({
                            "label": qsTr("Sec. DR"),
                            "value": item.drAlt,
                            "roll": true,
                            "tip": ""
                        });
            mc.push({
                        "label": qsTr("Atk"),
                        "value": item.modAtk,
                        "roll": true,
                        "tip": qsTr("Base %1  ·  Mod %2").arg(item.baseAtk || "—").arg(item.modAtk || "—")
                    });
            mc.push({
                        "label": qsTr("Dmg"),
                        "value": item.modDmg,
                        "roll": true,
                        "tip": qsTr("Base %1  ·  Mod %2").arg(item.baseDmg || "—").arg(item.modDmg || "—")
                    });
            return mc;
        }

        implicitHeight: cardBody.implicitHeight + 18
        color: cardHover.hovered || _expanded ? Theme.parchmentBase : Theme.parchmentInset
        border.color: cardHover.hovered || _expanded ? Qt.darker(_catColor, 1.2) : Theme.borderSubtle
        border.width: 1
        radius: 2

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: 120
            }
        }

        // Category-coloured left rail.
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: card._catColor
            opacity: 0.9
        }

        HoverHandler {
            id: cardHover
            cursorShape: card._hasDesc ? Qt.PointingHandCursor : Qt.ArrowCursor
        }
        TapHandler {
            enabled: card._hasDesc
            onTapped: section._toggleExpand(card.item.id)
        }

        ColumnLayout {
            id: cardBody
            anchors.fill: parent
            anchors.margins: 9
            anchors.leftMargin: 13
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s4

                // ---- Name + skill·category subtitle -----------------
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 2

                    Label {
                        Layout.fillWidth: true
                        text: card._name
                        // Body face, regular weight, slightly enlarged --
                        // a proper-name title carries by size, not a faux-
                        // bold of the single-weight body face (§3.4).
                        font.pixelSize: Theme.fsBody + 2
                        font.weight: Theme.wRegular
                        color: Theme.ink
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        text: card._skill.toUpperCase()
                        visible: text.length > 0
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsCaption
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.4
                        color: card._catColor
                        opacity: 0.9
                        elide: Text.ElideRight
                    }

                    // Full tag set as badges -- the category tags
                    // (melee/ranged/arrow) tinted to their rail hue, the
                    // descriptors (small/large/samurai/peasant/…) in
                    // neutral ink. Carries the data the rail + skill line
                    // don't.
                    Flow {
                        Layout.fillWidth: true
                        Layout.topMargin: 2
                        spacing: 4
                        visible: card.item && card.item.tags && card.item.tags.length > 0
                        Repeater {
                            model: card.item ? (card.item.tags || []) : []
                            delegate: TagBadge {
                                tag: modelData
                            }
                        }
                    }
                }

                // ---- Stat figures -----------------------------------
                RowLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: Theme.s4
                    Repeater {
                        model: card._cells
                        delegate: StatCell {
                            label: modelData.label
                            value: modelData.value || ""
                            roll: modelData.roll
                            tip: modelData.tip
                            Layout.minimumWidth: 34
                        }
                    }
                }

                // ---- Quantity stepper (arrows only) -----------------
                ColumnLayout {
                    visible: card._isArrow
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 0
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("QUANTITY")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsMicro
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.2
                        color: Theme.inkMuted
                    }
                    Widgets.RankStepper {
                        Layout.alignment: Qt.AlignHCenter
                        value: card.item ? card.item.qty : 1
                        from: 1
                        to: 9999
                        onValueModified: function (v) {
                            if (card.item && appCtrl)
                                appCtrl.changeWeaponQty(card.item.id, v - card.item.qty);
                        }
                    }
                }

                // ---- Expand chevron ---------------------------------
                Label {
                    visible: card._hasDesc
                    Layout.alignment: Qt.AlignVCenter
                    text: card._expanded ? "▲" : "▼"
                    font.pixelSize: 9
                    color: Theme.ink
                    opacity: 0.45
                }

                // ---- Edit handle (melee / ranged) -------------------
                // Holder is fixed-width so the row doesn't dance as the
                // affordance fades in on hover.
                Item {
                    visible: !card._isArrow
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter

                    AbstractButton {
                        id: editBtn
                        anchors.fill: parent
                        visible: cardHover.hovered || editBtn.hovered
                        onClicked: section._requestEdit(card.item)

                        background: Rectangle {
                            radius: 11
                            color: editBtn.hovered ? Theme.heading : "transparent"
                            border.color: Theme.heading
                            border.width: 1
                            opacity: editBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "✎"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: editBtn.hovered ? Theme.whiteWash : Theme.heading
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: qsTr("Edit this weapon")
                    }
                }

                // ---- Remove handle ----------------------------------
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter

                    AbstractButton {
                        id: removeBtn
                        anchors.fill: parent
                        visible: cardHover.hovered || removeBtn.hovered
                        onClicked: section._requestRemove(card.item)

                        background: Rectangle {
                            radius: 11
                            color: removeBtn.hovered ? Theme.accent : "transparent"
                            border.color: Theme.accent
                            border.width: 1
                            opacity: removeBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "✕"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: removeBtn.hovered ? Theme.whiteWash : Theme.accent
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: qsTr("Discard this weapon")
                    }
                }
            }

            // ---- Expanded effect / notes ----------------------------
            ColumnLayout {
                Layout.fillWidth: true
                visible: card._expanded && card._hasDesc
                spacing: 4

                Rectangle {
                    Layout.fillWidth: true
                    Layout.leftMargin: 4
                    Layout.preferredHeight: 1
                    color: card._catColor
                    opacity: 0.25
                }
                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 4
                    Layout.bottomMargin: 2
                    text: card._desc
                    textFormat: Text.PlainText
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    wrapMode: Text.WordWrap
                    opacity: 0.92
                }
            }
        }
    }
}
