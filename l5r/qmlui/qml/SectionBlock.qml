// Copyright (C) 2014-2026 Daniele Simonetti
// A section block for the scrollable-sheet layout. Unlike TabPlaceholder
// (which centres in a tab pane), this one is a horizontal strip with a
// header line on top and inline body content, sized to give the sheet
// visible bulk during scrolling.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "sections" as Sections
import Theme 1.0

Item {
    id: section
    property string tabId: ""
    property string title: ""
    property string icon: ""

    implicitHeight: column.implicitHeight + 32
    Layout.fillWidth: true

    // Section-icon watermark. Declared first so it paints behind the
    // body. At ~6% opacity the L5R glyph (clan-mon stand-in) reads
    // as atmosphere; the user's gaze still lands on the actual data.
    Label {
        id: watermark
        text: section.icon
        visible: section.icon.length > 0
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: 16
        anchors.topMargin: -8
        font.pixelSize: 180
        font.family: Theme.fontDisplay
        color: Theme.heading
        opacity: Theme.watermarkOpacity
        // Watermark must never steal hits from the content above.
        enabled: false
    }

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
                color: Theme.accent
                opacity: 0.85
            }

            Label {
                text: section.title || section.tabId
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.headerFont
                font.weight: Font.DemiBold
                color: Theme.heading
                Layout.fillWidth: true
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.divider
            opacity: Theme.dividerOpacity
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
                case "about":   return aboutBody
                case "notes":   return notesBody
                case "pc_info": return characterBody
                default:        return placeholderBody
                }
            }

            Component {
                id: aboutBody
                Sections.AboutSection {}
            }

            Component {
                id: notesBody
                Sections.NotesSection {}
            }

            Component {
                id: characterBody
                Sections.CharacterSection {}
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
