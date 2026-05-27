// Copyright (C) 2014-2026 Daniele Simonetti
// A section block for the scrollable-sheet layout. Unlike TabPlaceholder
// (which centres in a tab pane), this one is a horizontal strip with a
// header line on top and inline body content, sized to give the sheet
// visible bulk during scrolling.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "sections" as Sections

Item {
    id: section
    property string tabId: ""
    property string title: ""
    property string icon: ""

    implicitHeight: column.implicitHeight + 32
    Layout.fillWidth: true

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 12

        // Header strip
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Label {
                text: section.icon
                font.pixelSize: 26
                opacity: 0.6
            }

            Label {
                text: section.title || section.tabId
                font.pixelSize: 20
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }

            Label {
                text: "#" + section.tabId
                font.pixelSize: 11
                opacity: 0.4
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: palette.mid
            opacity: 0.35
        }

        // Body -- per-tab content if we have a section QML for this id,
        // otherwise a neutral "coming soon" card. The Loader sizes
        // itself to its content's implicit height so the surrounding
        // sheetColumn (in MainSheet) sees an accurate y for each
        // sibling SectionBlock, which the TOC needs.
        Loader {
            id: body
            Layout.fillWidth: true
            sourceComponent: {
                switch (section.tabId) {
                case "about": return aboutBody
                default:      return placeholderBody
                }
            }

            Component {
                id: aboutBody
                Sections.AboutSection {}
            }

            Component {
                id: placeholderBody
                Rectangle {
                    implicitHeight: 220
                    color: "transparent"
                    radius: 6
                    border.width: 1
                    border.color: palette.mid

                    Label {
                        anchors.centerIn: parent
                        text: qsTr("Section '%1' content coming soon").arg(section.tabId)
                        opacity: 0.7
                        font.pixelSize: 13
                    }
                }
            }
        }
    }
}
