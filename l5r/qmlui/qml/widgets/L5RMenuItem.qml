// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system menu row for L5RMenu. Renders like a sidebar nav / list
// item (§6.1 / §6.10): an IM Fell English body label on parchment, with a
// soft clan-accent wash + 3px accent stripe when highlighted. Handles
// checkable items (a brush tick in the accent) and submenus (a brush
// caret), so it also covers the future Tools/Export menus.
//
// Mnemonics: the `&` is stripped from the displayed label only; the item's
// text keeps it, so Alt-navigation still works.
import QtQuick
import QtQuick.Controls
import Theme 1.0
import ClanTheme 1.0

MenuItem {
    id: control
    property color accent: ClanTheme.primary
    property color accentWash: ClanTheme.selectedBg

    implicitHeight: 32

    // Checkmark for checkable items (e.g. future toggles). Reserves its slot
    // only when checkable, so plain rows stay flush-left.
    indicator: Label {
        visible: control.checkable
        x: Theme.s3
        y: (control.height - height) / 2
        text: control.checked ? "✓" : ""
        font.family: Theme.fontKanji
        font.pixelSize: 14
        color: control.accent
    }

    // Submenu caret (brush triangle), inkMuted, right-aligned.
    arrow: Label {
        visible: control.subMenu !== null
        x: control.width - width - Theme.s3
        y: (control.height - height) / 2
        text: "▸"
        font.pixelSize: 12
        color: Theme.inkMuted
    }

    contentItem: Label {
        // Indent past the checkmark slot when checkable; leave room for the
        // caret when this row opens a submenu.
        leftPadding: control.checkable ? Theme.s5 : Theme.s3
        rightPadding: control.subMenu !== null ? Theme.s5 : Theme.s3
        text: control.text.replace("&", "")
        font.family: Theme.fontBody
        font.pixelSize: Theme.fsBody
        color: Theme.ink
        opacity: control.enabled ? 1.0 : 0.45
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: control.highlighted ? control.accentWash : "transparent"
        // 3px accent stripe on the active row (§6.1 / §6.10).
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: control.accent
            visible: control.highlighted
        }
        Behavior on color {
            ColorAnimation {
                duration: Theme.durFast
                easing.type: Easing.OutQuad
            }
        }
    }
}
