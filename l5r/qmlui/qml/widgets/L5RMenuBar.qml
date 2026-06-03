// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system menu bar -- the window's top MenuBar, in the §6.1 nav
// language. Replaces the bare QtQuick Controls MenuBar: under the Fusion
// style (forced in l5r.qmlui.app) that paints as a flat grey OS strip,
// alien to the parchment sheet. Here the bar is a darker-parchment band
// carrying the same rice-paper fibre as the sidebar, and each top-level
// title (File, Tools, ...) reads like a sidebar nav item -- Cinzel SemiBold
// ink, tinting to the clan accent with a soft wash when its menu is open.
//
// Pair with L5RMenu (the parchment dropdown), L5RMenuItem (rows) and
// L5RMenuSeparator (dividers). Mnemonics (&File) are preserved: the `&` is
// stripped only from the *displayed* label; the item keeps its text, so
// Alt-navigation still works.
//
// Usage (in ApplicationWindow):
//   menuBar: Widgets.L5RMenuBar {
//       Widgets.L5RMenu {
//           title: qsTr("&File")
//           Widgets.L5RMenuItem { text: qsTr("&New"); onTriggered: appCtrl.fileNew() }
//           ...
//       }
//   }
import QtQuick
import QtQuick.Controls
import Theme 1.0
import ClanTheme 1.0

MenuBar {
    id: bar

    background: Rectangle {
        color: ClanTheme.paperSidebar
        RicePaperOverlay {}
        // Bottom hairline tying the bar to the sheet below (§8.3 -- never a
        // solid black line; parchment-border at the divider opacity).
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: Theme.divider
            opacity: Theme.dividerOpacity
        }
    }

    delegate: MenuBarItem {
        id: barItem
        // `&File` -> "FILE": drop the mnemonic marker for display (the item
        // keeps its `&` so Alt+F still opens the menu), then uppercase per
        // the Cinzel all-caps policy (§3.4).
        readonly property string label: barItem.text.replace("&", "").toUpperCase()
        padding: Theme.s2
        leftPadding: Theme.s3
        rightPadding: Theme.s3
        hoverEnabled: true

        contentItem: Label {
            text: barItem.label
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsLabel
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.0          // ~0.08em at 13px (§3.4)
            color: (barItem.highlighted || barItem.down || barItem.hovered) ? ClanTheme.primary : Theme.ink
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }

        background: Rectangle {
            color: (barItem.highlighted || barItem.down || barItem.hovered) ? ClanTheme.selectedBg : "transparent"
            // §9: hover/press feedback 120 ms ease-out.
            Behavior on color {
                ColorAnimation {
                    duration: Theme.durHover
                    easing.type: Easing.OutQuad
                }
            }
        }
    }
}
