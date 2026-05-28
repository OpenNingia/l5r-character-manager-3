// Copyright (C) 2014-2026 Daniele Simonetti
// Document-flavoured replacement for the stock GroupBox. The panel
// shares the surrounding window's parchment fill (Theme.parchment)
// and contributes only a 1px sepia border + a hairline burnt-gold
// title rule, so panels read as inked sections of one continuous
// sheet rather than separate cards floating on a desk. Crucially,
// the panel *does not* track the OS dark theme -- a character sheet
// is a document, and a document is paper regardless of what the desk
// underneath looks like.  The rice-paper texture is drawn at the
// window level (MainSheet) so it stays continuous across panels and
// gutters; SheetPanel itself does not own a per-panel overlay.
// Why Pane and not Rectangle: child Labels/TextFields read their
// text colour from the inherited `palette` group. A plain Rectangle
// does not propagate palette, so internal text on a dark OS would
// render OS-light (white) and disappear against the cream fill. A
// Pane is a Control with a real palette, and Qt Quick walks the
// visual parent chain to resolve `palette.windowText` on every
// descendant. Setting the palette here once forces ink-on-paper
// throughout the panel without consumers having to set colours.
// Usage:
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
        // Panels share the window-level parchment fill and have no
        // border -- separation comes from the title-band and the
        // heading rule below the title, so panels read as sections of
        // one continuous sheet rather than boxed cards.
        color: Theme.parchment
        radius: 0
    }

    // Force ink-on-paper. These palette overrides cascade to every
    // descendant Label / TextField / ComboBox that reads its colour
    // from the palette group (which is the default for plain Quick
    // Controls). Explicit per-Label `color: Theme.foo` overrides
    // still win, so the burnt-gold headings and ring-tinted flag
    // labels are unaffected.
    palette.windowText: Theme.ink
    palette.text: Theme.ink
    palette.buttonText: Theme.ink
    palette.base: Theme.parchmentBase
    palette.alternateBase: Theme.parchmentInset
    palette.placeholderText: "#8a7a65"
    palette.mid: "#a89580"

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
