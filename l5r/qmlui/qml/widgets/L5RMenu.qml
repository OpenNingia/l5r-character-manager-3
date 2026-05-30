// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system dropdown for the window menu bar (§6.7 popup). The popup
// detaches from the window, so -- like every L5R modal/popup -- it carries
// its own parchment surface and rice-paper fibre rather than inheriting the
// sheet's. whiteWash fill + parchment-border hairline + radius 2 mirror the
// ComboBox popup, so the two dropdown surfaces read identically.
//
// Rows are L5RMenuItem; dividers are L5RMenuSeparator. `accent` (default the
// clan accent) tints the row hover wash + stripe, echoing the sidebar nav --
// so the menu re-tints with the active character's clan.
import QtQuick
import QtQuick.Controls
import Theme 1.0
import ClanTheme 1.0

Menu {
    id: menu

    // Clan accent by default so the menu re-tints with the character's clan,
    // like the sidebar. Overridable for a fixed-accent menu if ever needed.
    property color accent: ClanTheme.primary
    property color accentWash: ClanTheme.selectedBg

    implicitWidth: 240
    padding: 2

    background: Rectangle {
        implicitWidth: 240
        color: Theme.whiteWash
        border.color: Theme.borderSubtle
        border.width: 1
        radius: 2
        RicePaperOverlay {}
    }
}
