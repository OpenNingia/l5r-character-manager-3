// Copyright (C) 2014-2026 Daniele Simonetti
// Compact -/+ stepper styled as a parchment pill. Replacement for the
// stock SpinBox on the social/spiritual flag rows (honor, glory,
// status), where the OS-themed SpinBox chrome fights the document
// surface of SheetPanel. Emits `valueModified(int)` only on user
// click -- bound values do NOT round-trip, so this is safe to drive
// from a model property without a feedback loop.
//
// Usage:
//
//     Widgets.RankStepper {
//         value: rank
//         from: 0; to: 10
//         onValueModified: function(v) { appCtrl.setFlag(key, v) }
//     }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Theme 1.0

Rectangle {
    id: stepper
    property int value: 0
    property int from: 0
    property int to: 10
    signal valueModified(int newValue)

    implicitWidth: 82
    implicitHeight: 26
    color: "#fbf6e8"
    border.color: Theme.borderSubtle
    border.width: 1
    radius: 3

    function _clamp(v) {
        return Math.max(stepper.from, Math.min(stepper.to, v))
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // --- minus button -------------------------------------------
        Item {
            Layout.fillHeight: true
            Layout.preferredWidth: 24
            Label {
                anchors.centerIn: parent
                text: "−"  // U+2212 minus
                font.pixelSize: 14
                color: minusMa.enabled ? "#6b5b3f" : "#bdb09c"
            }
            Rectangle {
                anchors { right: parent.right; top: parent.top; bottom: parent.bottom }
                width: 1
                color: Theme.borderSubtle
                opacity: 0.55
            }
            MouseArea {
                id: minusMa
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                enabled: stepper.value > stepper.from
                onClicked: stepper.valueModified(stepper._clamp(stepper.value - 1))
            }
        }

        // --- value readout ------------------------------------------
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Label {
                anchors.centerIn: parent
                text: stepper.value
                font.family: Theme.fontDisplay
                font.pixelSize: 13
                font.weight: Font.DemiBold
                font.features: Theme.tabularNumbers
                color: "#3a3a3a"
            }
        }

        // --- plus button --------------------------------------------
        Item {
            Layout.fillHeight: true
            Layout.preferredWidth: 24
            Label {
                anchors.centerIn: parent
                text: "+"
                font.pixelSize: 14
                color: plusMa.enabled ? "#6b5b3f" : "#bdb09c"
            }
            Rectangle {
                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                width: 1
                color: Theme.borderSubtle
                opacity: 0.55
            }
            MouseArea {
                id: plusMa
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                enabled: stepper.value < stepper.to
                onClicked: stepper.valueModified(stepper._clamp(stepper.value + 1))
            }
        }
    }
}
