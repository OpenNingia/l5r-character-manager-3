// Copyright (C) 2014-2026 Daniele Simonetti
// Replacement for the plain `Rectangle { height: 1; color: divider }`
// horizontal rule. Two faded sepia hairlines flank a centred fleuron
// glyph in burnt-gold Cinzel -- the document-as-character-sheet flavor.
//
// Drop-in: anywhere a section divider is wanted, swap the Rectangle
// for this. Keep the plain rule for tight in-panel separations (under
// a SheetPanel banner, between table rows) -- the ornament is meant
// to mark structural breaks, not every horizontal line.
//
// Usage:
//     Widgets.OrnateDivider {
//         Layout.fillWidth: true
//         glyph: "❖"          // optional; defaults to a fleuron
//     }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Theme 1.0

RowLayout {
    id: rule
    Layout.fillWidth: true
    spacing: 10

    // Public ----------------------------------------------------------
    property string glyph: "❖"
    property color  ruleColor: Theme.divider
    property real   ruleOpacity: Theme.dividerOpacity
    property color  glyphColor: Theme.heading
    property real   glyphOpacity: 0.55
    property int    glyphSize: Theme.bodyFont

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: rule.ruleColor
        opacity: rule.ruleOpacity
    }
    Label {
        text: rule.glyph
        color: rule.glyphColor
        opacity: rule.glyphOpacity
        font.family: Theme.fontDisplay
        font.pixelSize: rule.glyphSize
        font.weight: Font.DemiBold
    }
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: rule.ruleColor
        opacity: rule.ruleOpacity
    }
}
