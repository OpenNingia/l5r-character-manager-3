// Copyright (C) 2014-2026 Daniele Simonetti
// Document-flavoured replacement for the stock GroupBox. The panel
// IS the parchment: a fixed cream surface with a hairline burnt-gold
// title rule and a sharp 1px sepia border. Crucially, the panel
// *does not* track the OS dark theme -- a character sheet is a
// document, and a document is paper regardless of what the desk
// underneath looks like. The window chrome, TOC, and menubar still
// follow the OS theme so the app feels native; the sheet inside
// commits to its own world.
//
// Why Pane and not Rectangle: child Labels/TextFields read their
// text colour from the inherited `palette` group. A plain Rectangle
// does not propagate palette, so internal text on a dark OS would
// render OS-light (white) and disappear against the cream fill. A
// Pane is a Control with a real palette, and Qt Quick walks the
// visual parent chain to resolve `palette.windowText` on every
// descendant. Setting the palette here once forces ink-on-paper
// throughout the panel without consumers having to set colours.
//
// Usage:
//
//     import "../widgets" as Widgets
//     Widgets.SheetPanel {
//         Layout.fillWidth: true
//         title: qsTr("Rings and Attributes")
//         ColumnLayout {
//             width: parent.width
//             spacing: 10
//             // ... content; Label colours inherit from panel.palette
//         }
//     }
//
// Child layouts must use `width: parent.width` (or equivalent
// left/right anchors), NOT `anchors.fill: parent`, to avoid a
// cycle between bodyHolder.implicitHeight (driven by child) and
// child.height (which anchors.fill would tie back to bodyHolder).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Theme 1.0

Pane {
    id: panel
    property string title: ""
    default property alias content: bodyHolder.data

    background: Rectangle {
        // Aged parchment. Hand-picked rather than computed so the
        // sheet has the same character on every install.
        color: "#f4ead5"
        border.width: 1
        border.color: Theme.borderStrong
        radius: 0
    }

    // Force ink-on-paper. These palette overrides cascade to every
    // descendant Label / TextField / ComboBox that reads its colour
    // from the palette group (which is the default for plain Quick
    // Controls). Explicit per-Label `color: Theme.foo` overrides
    // still win, so the burnt-gold headings and ring-tinted flag
    // labels are unaffected.
    palette.windowText: "#2a221b"
    palette.text:       "#2a221b"
    palette.buttonText: "#2a221b"
    palette.base:       "#fdf6e3"
    palette.alternateBase: "#ece1c4"
    palette.placeholderText: "#8a7a65"
    palette.mid:        "#a89580"

    padding: 12
    spacing: 0

    contentItem: ColumnLayout {
        spacing: 8

        Label {
            visible: panel.title.length > 0
            Layout.fillWidth: true
            text: panel.title
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.titleFont
            font.weight: Theme.headingWeight
            // The letterSpacing nudge turns Cinzel into a proper
            // section banner -- without it the all-caps reads
            // crowded against itself at 18px.
            font.letterSpacing: 1.5
            color: Theme.heading
        }
        Rectangle {
            visible: panel.title.length > 0
            Layout.fillWidth: true
            Layout.topMargin: -2
            Layout.preferredHeight: 1
            color: Theme.heading
            opacity: 0.45
        }
        Item {
            id: bodyHolder
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            Layout.topMargin: 4
        }
    }
}
