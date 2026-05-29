// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system rank selector (§6.4): a wrapping row of 36×36 numbered
// pills for picking rank 1..N on advantages / disadvantages / spells.
// Replaces the hand-rolled Flow-of-AbstractButton rank picker in the
// perk dialog.
//
//   model       -- array of items (or plain numbers)
//   numberRole  -- field on each item holding the rank number (e.g.
//                  "rank"); leave "" if the model items ARE the numbers
//   currentValue-- the selected rank number
//   accent      -- active-pill fill (crimson default; Theme.secondary for blue)
//   picked(int) -- emitted with the chosen rank; the parent owns the
//                  selection state and feeds it back via currentValue
//
// Usage:
//   Widgets.L5RRankSelector {
//       model: entry.ranks; numberRole: "rank"
//       currentValue: selectedRank; accent: Theme.secondary
//       onPicked: (v) => selectedRank = v
//   }
import QtQuick
import QtQuick.Controls
import Theme 1.0

Flow {
    id: selector
    property var model: []
    property string numberRole: ""
    property int currentValue: -1
    property color accent: Theme.accent
    signal picked(int value)

    spacing: 4   // §6.4 gap

    Repeater {
        model: selector.model
        delegate: Rectangle {
            id: pip
            readonly property int _value: selector.numberRole.length > 0 ? modelData[selector.numberRole] : modelData
            readonly property bool _active: selector.currentValue === _value
            width: 36
            height: 36
            radius: 2
            // Active: accent fill. Inactive: transparent + parchment
            // border; hover lifts onto paper with an ink-muted border.
            color: _active ? selector.accent : (pipMa.containsMouse ? Theme.parchment : "transparent")
            border.width: 1
            border.color: _active ? selector.accent : (pipMa.containsMouse ? Theme.inkMuted : Theme.borderSubtle)
            Behavior on color {
                ColorAnimation {
                    duration: 100
                    easing.type: Easing.OutQuad
                }
            }

            Label {
                anchors.centerIn: parent
                text: pip._value
                font.family: Theme.fontStat
                font.pixelSize: Theme.fsStatSmall
                font.weight: pip._active ? Theme.wBold : Theme.wRegular
                font.features: Theme.tabularNumbers
                color: pip._active ? Theme.whiteWash : Theme.inkMuted
            }
            MouseArea {
                id: pipMa
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: selector.picked(pip._value)
            }
        }
    }
}
