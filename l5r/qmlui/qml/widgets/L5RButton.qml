// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system action button (§6.2 primary / §6.3 secondary). Replaces
// the per-dialog hand-rolled AbstractButton footers, which all repeated
// the same parchment-pill + Cinzel-label shape.
//
//   primary (default) -- filled accent, white-wash UPPERCASE Cinzel label,
//                        optional kanji glyph left of the text. `accent` /
//                        `accentDark` set the fill and its hover/pressed
//                        shade -- crimson by default; pass Theme.secondary /
//                        Theme.secondaryDark for the blue Blessing variant.
//   secondary (primary:false) -- transparent with a parchment-border
//                        outline and ink-muted label; the Cancel shape.
//
// Disabled is rendered per spec (disabledBg / disabledText) rather than
// by dimming opacity. Uppercasing happens here so call sites pass normal
// qsTr() strings.
//
// Usage:
//   Widgets.L5RButton { text: qsTr("Cancel"); primary: false; onClicked: ... }
//   Widgets.L5RButton {
//       text: qsTr("Inscribe"); glyph: "縁"
//       accent: Theme.secondary; accentDark: Theme.secondaryDark
//       enabled: canAccept; onClicked: accept()
//   }
import QtQuick
import QtQuick.Controls
import Theme 1.0

Button {
    id: control

    // --- API ------------------------------------------------------
    property bool primary: true
    property string glyph: ""                 // optional kanji, primary only
    property color accent: Theme.accent       // primary fill
    property color accentDark: Theme.accentMuted  // primary hover/pressed

    // --- metrics (§6.2 / §6.3) ------------------------------------
    implicitHeight: 40
    leftPadding: 20
    rightPadding: 20
    hoverEnabled: true

    background: Rectangle {
        radius: 3
        color: {
            if (control.primary) {
                if (!control.enabled)
                    return Theme.disabledBg;
                if (control.down)
                    return Qt.darker(control.accentDark, 1.1);
                if (control.hovered || control.focus)
                    return control.accentDark;
                return control.accent;
            }
            // secondary
            if (control.down)
                return Theme.parchmentSidebar;   // paper-dark pressed
            if (control.hovered || control.focus)
                return Theme.parchment;          // paper hover
            return "transparent";
        }
        border.width: control.primary ? 0 : 1
        border.color: control.primary ? "transparent" : (control.hovered || control.focus ? Theme.inkMuted : Theme.borderSubtle)
        // §9: button hover/press 120 ms ease-out.
        Behavior on color {
            ColorAnimation {
                duration: 120
                easing.type: Easing.OutQuad
            }
        }
    }

    contentItem: Item {
        implicitWidth: row.implicitWidth
        implicitHeight: row.implicitHeight
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 8
            Label {
                visible: control.primary && control.glyph.length > 0
                anchors.verticalCenter: parent.verticalCenter
                text: control.glyph
                font.family: Theme.fontKanji
                font.pixelSize: 16
                color: Theme.whiteWash
                opacity: 0.95
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: control.text.toUpperCase()
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsLabel
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.0   // ~0.08em at 13px
                color: control.primary ? (control.enabled ? Theme.whiteWash : Theme.disabledText) : Theme.inkMuted
            }
        }
    }
}
