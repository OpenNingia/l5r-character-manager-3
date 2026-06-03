// Copyright (C) 2014-2026 Daniele Simonetti
// ChooseElementDialog -- QML-native picker for the elemental AFFINITY or
// DEFICIENCY a shugenja school grants the player to choose (the school's
// affinity/deficiency spec is `any` or `nonvoid`). Replaces the legacy bare
// QInputDialog.getItem in AdvanceMixin.show_select_affinity /
// show_select_deficiency (l5r/ui/advance.py) without reusing it. Opened from
// the Spells section's §6.16 callouts:
//     chooseElementDlg.present("affinity")   // or "deficiency"
//
// One dialog serves both choices -- the `kind` parameter switches the title,
// tagline and which controller setter is called. The options come from
// appCtrl.elementChoice(kind), which already drops Void when the school's
// spec is `nonvoid`. Blue accent keeps it in the shared "you unlocked
// something" opportunity language (the elemental hue lives on the per-ring
// tiles, not the dialog chrome).
//
// Data shape (from appCtrl.elementChoice(kind)):
//   { pending: bool, kind: "affinity"|"deficiency",
//     options: [{ id: "fire", name: "Fire" }, ...] }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 460, 460)
    padding: Theme.s5

    // --- state ----------------------------------------------------
    property string _kind: "affinity"          // "affinity" | "deficiency"
    property var _options: []                    // [{ id, name }]
    property string _selected: ""                // chosen ring key
    readonly property bool _isAffinity: _kind === "affinity"

    // --- chrome (via L5RDialog) -----------------------------------
    // Blue (the shared opportunity-surface accent). 氣 (ki) -- elemental
    // spirit/energy -- is the seal for the elemental-leaning choice; the
    // five ring hues carry the actual element identity on the tiles below.
    seal: "氣"
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    title: root._isAffinity ? qsTr("Awaken an Affinity") : qsTr("Embrace a Deficiency")
    tagline: root._isAffinity ? qsTr("the element your prayers command with ease") : qsTr("the element whose kami resist your call")
    acceptText: qsTr("Choose")
    acceptGlyph: "氣"
    acceptEnabled: root._selected.length > 0
    statusText: {
        if (root._selected.length === 0)
            return root._isAffinity ? qsTr("Choose the element you resonate with.") : qsTr("Choose the element that resists you.");
        return root._isAffinity ? qsTr("This element's spells come more readily — Mastery within reach rises by one.") : qsTr("This element's spells come harder — Mastery within reach falls by one.");
    }
    onAccepted: {
        if (!root._selected || !appCtrl)
            return;
        if (root._isAffinity)
            appCtrl.chooseAffinity(root._selected);
        else
            appCtrl.chooseDeficiency(root._selected);
    }

    // --- entrypoint -----------------------------------------------
    function present(kind) {
        root._kind = (kind === "deficiency") ? "deficiency" : "affinity";
        var info = (appCtrl && appCtrl.elementChoice) ? (appCtrl.elementChoice(root._kind) || {}) : {};
        root._options = info.options || [];
        root._selected = "";
        root.open();
    }

    // Decorative ring kanji (地風水火空) -- a glyph cue on each tile, never
    // the tile's label (the ring name is). Falls back to empty for unknown
    // keys so a non-ring option still renders cleanly.
    function _ringKanji(key) {
        switch (key) {
        case "earth":
            return "地";
        case "air":
            return "風";
        case "water":
            return "水";
        case "fire":
            return "火";
        case "void":
            return "空";
        default:
            return "";
        }
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: Theme.s4

        // Empty-state guard (opened with nothing pending).
        Label {
            visible: root._options.length === 0
            Layout.fillWidth: true
            Layout.topMargin: Theme.s3
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("There is no elemental choice to make.")
            font.italic: true
            font.pixelSize: Theme.fsBody
            color: Theme.ink
            opacity: 0.7
        }

        // ---- Ring tiles ------------------------------------------
        // A wrapping row of element tiles, each in its §2.3 ring hue: the
        // selected one fills with that hue (white glyph), the rest are
        // outlined (ink glyph) with a faint wash on hover. `_selected` is the
        // single source of truth, so the tiles are mutually exclusive without
        // a ButtonGroup (same shape as the JoinSchoolDialog category row).
        Flow {
            Layout.fillWidth: true
            visible: root._options.length > 0
            spacing: Theme.s2

            Repeater {
                model: root._options
                delegate: AbstractButton {
                    id: tile
                    required property var modelData
                    readonly property color _ring: Theme.ringColor(modelData.id)
                    readonly property bool _on: root._selected === modelData.id

                    implicitWidth: 96
                    implicitHeight: 84
                    onClicked: root._selected = modelData.id

                    background: Rectangle {
                        radius: 4
                        color: tile._on ? tile._ring : (tile.hovered ? Qt.rgba(tile._ring.r, tile._ring.g, tile._ring.b, 0.12) : "transparent")
                        border.color: tile._ring
                        border.width: tile._on ? 0 : 1
                        Behavior on color {
                            ColorAnimation {
                                duration: Theme.durHover
                            }
                        }
                    }

                    contentItem: ColumnLayout {
                        spacing: 2
                        Label {
                            Layout.alignment: Qt.AlignHCenter
                            text: root._ringKanji(tile.modelData.id)
                            font.family: Theme.fontKanji
                            font.pixelSize: 30
                            color: tile._on ? Theme.whiteWash : tile._ring
                        }
                        Label {
                            Layout.alignment: Qt.AlignHCenter
                            text: (tile.modelData.name || "").toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.weight: Theme.wSemiBold
                            font.letterSpacing: 1.2
                            color: tile._on ? Theme.whiteWash : Theme.ink
                        }
                    }
                }
            }
        }
    }
}
