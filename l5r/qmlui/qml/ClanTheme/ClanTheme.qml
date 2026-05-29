// Copyright (C) 2014-2026 Daniele Simonetti
// Writable singleton holding the ACTIVE CLAN's accent pair (design
// system §5). Unlike Theme (fixed brand tokens), this one is mutated at
// runtime: MainSheet calls ClanTheme.setClan(pcProxy.clanId) whenever
// the character's clan changes, and accent consumers (the sidebar's
// active-nav stripe / label / icon) bind to ClanTheme.primary so the
// accent shifts per clan while the layout stays put. The action buttons
// stay crimson/blue by burden/blessing (§6.2) -- only the clan-identity
// accent lives here.
//   primary      -- the clan's accent (active nav, clan-themed highlights)
//   primaryDark  -- hover / pressed shade of primary
//   selectedBg   -- light clan-tinted wash for selected items in
//                   clan-themed contexts (derived from primary over paper)
//   clanKey      -- the resolved clan id ("crane" .. "ronin")
// setClan(key) looks the §5 table up case-insensitively and falls back
// to the Ronin / Other dark-tan pair for unknown or empty ids.
// Registered as the `ClanTheme` module via the sibling qmldir; the qml
// dir is already on the import path (see l5r.qmlui.app.run_qml_app), so
// `import ClanTheme 1.0` resolves everywhere alongside `import Theme 1.0`.
pragma Singleton
import QtQuick
import Theme 1.0

QtObject {
    id: clan

    property string clanKey: "crane"
    property color primary: "#4A6FA5"       // default: Crane
    property color primaryDark: "#3A5A8A"

    // Light clan wash: paper tinted with ~16% of the clan accent. The
    // spec gives explicit bg washes only for crimson/blue (§2.2), so we
    // derive a consistent one for every clan rather than inventing a
    // ten-row table. Binds to `primary`, so it re-derives on setClan.
    readonly property color selectedBg: Qt.tint(Theme.parchment, Qt.rgba(primary.r, primary.g, primary.b, 0.16))

    // §5 clan -> [primary, primaryDark]. Keys are the lowercase clan ids
    // returned by api.character.get_clan() (family_.clanid).
    readonly property var _table: ({
            "crab": ["#5A5A2A", "#404020"],
            "crane": ["#4A6FA5", "#3A5A8A"],
            "dragon": ["#2A6A4A", "#1A5A3A"],
            "lion": ["#B8860B", "#8A6208"],
            "mantis": ["#2A7A5A", "#1A6A4A"],
            "phoenix": ["#8B4A1A", "#6B3A10"],
            "scorpion": ["#8B1A1A", "#6B1010"],
            "spider": ["#3A2A4A", "#2A1A3A"],
            "unicorn": ["#6A2A6A", "#5A1A5A"],
            "ronin": ["#5A4A3A", "#4A3A2A"]
        })

    function setClan(key) {
        var k = (key || "").toLowerCase();
        var row = _table[k];
        if (!row) {
            k = "ronin";
            row = _table[k];
        }
        clan.clanKey = k;
        clan.primary = row[0];
        clan.primaryDark = row[1];
    }
}
