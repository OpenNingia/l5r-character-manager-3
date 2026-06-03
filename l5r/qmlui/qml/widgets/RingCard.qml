// Copyright (C) 2014-2026 Daniele Simonetti
// One colored card for the Rings & Attributes block. Shows the ring's
// rank as a big numeral on the left, then on the right side a stack
// containing the ring name and (for the four elemental rings) two
// attribute rows -- each "Attribute  value  +". The Void card uses
// the same shape but has no attribute rows; only the increase-ring
// button on the right.
// Card background is the ring's brand colour, darkened slightly so
// white text on top stays comfortably above the WCAG-AA threshold
// for all five rings (Air at #5d8aa8 was borderline at full
// strength).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

Rectangle {
    id: card

    // External API ----------------------------------------------------
    property string ringKey: "earth"
    property string ringLabel: "Earth"
    property int ringValue: 0
    // attrs: array of attribute keys, e.g. ["stamina", "willpower"].
    // attrLabels: map from key -> translated display name.
    // attrValues: map from key -> current rank int.
    property var attrs: []
    property var attrLabels: ({})
    property var attrValues: ({})
    property bool isVoid: false

    signal increaseTrait(string traitKey)
    signal increaseVoid

    // Visual ----------------------------------------------------------
    color: Qt.darker(Theme.ringColor(ringKey), 1.1)
    radius: 6
    border.width: 1
    border.color: Qt.darker(color, 1.35)
    // 200px fits the longest L5R 4e attribute names ("Intelligence",
    // "Awareness", "Perception") at the card's 12pt body size without
    // forcing the elide-tooltip fallback.
    implicitWidth: 200
    implicitHeight: layout.implicitHeight + 18

    RowLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 9
        spacing: 10

        // Big numeral ------------------------------------------------
        Label {
            text: card.ringValue
            color: "white"
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatLarge
            font.weight: Theme.wSemiBold
            font.features: Theme.tabularNumbers
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: 40
            horizontalAlignment: Text.AlignHCenter
            // Subtle drop-shadow effect via styleColor.
            style: Text.Raised
            styleColor: Qt.darker(card.color, 1.3)
        }

        // Right column ----------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: card.ringLabel
                    color: "white"
                    font.family: Theme.fontDisplay
                    font.weight: Theme.headingWeight
                    font.pixelSize: 15
                    font.letterSpacing: 1.2
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
                // Void has no attributes, so we surface the "+" inline
                // with the ring name to keep the layout balanced.
                ToolButton {
                    visible: card.isVoid
                    text: "+"
                    flat: true
                    implicitWidth: 24
                    implicitHeight: 22
                    padding: 0
                    palette.buttonText: "white"
                    font.weight: Font.Bold
                    font.pixelSize: 15
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Buy the next rank of Void")
                    onClicked: card.increaseVoid()
                }
            }

            // Attribute rows (elemental rings only)
            Repeater {
                model: card.isVoid ? [] : card.attrs
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label {
                        id: attrLabel
                        text: card.attrLabels[modelData] || modelData
                        color: "white"
                        opacity: 0.92
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fsLabel
                        HoverHandler {
                            id: attrHover
                        }
                        ToolTip.visible: attrHover.hovered && attrLabel.truncated
                        ToolTip.text: card.attrLabels[modelData] || modelData
                    }
                    Label {
                        text: card.attrValues[modelData] !== undefined ? card.attrValues[modelData] : "0"
                        color: "white"
                        font.pixelSize: Theme.fsStatSmall
                        font.weight: Font.DemiBold
                        font.features: Theme.tabularNumbers
                        Layout.preferredWidth: 18
                        horizontalAlignment: Text.AlignRight
                    }
                    ToolButton {
                        text: "+"
                        flat: true
                        implicitWidth: 22
                        implicitHeight: 20
                        padding: 0
                        palette.buttonText: "white"
                        font.weight: Font.Bold
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Buy the next rank in %1").arg(card.attrLabels[modelData] || modelData)
                        onClicked: card.increaseTrait(modelData)
                    }
                }
            }
        }
    }
}
