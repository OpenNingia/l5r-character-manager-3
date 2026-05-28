// Copyright (C) 2014-2026 Daniele Simonetti
// App-wide style constants for the QML UI. Used everywhere via
//
//     import Theme 1.0
//     Label { color: Theme.accent }
//
// The import path is registered in l5r.qmlui.app.run_qml_app(). Most
// colours are fixed L5R-themed hues that read on both light and dark
// system palettes; semantic neutrals fall back to `palette.*` at call
// sites so they still respect the OS theme.
pragma Singleton
import QtQuick

QtObject {
    // --- brand accents (work on light + dark backgrounds) ----------
    readonly property color accent:        "#b03030"  // samurai crimson
    readonly property color accentMuted:   "#7a2424"
    readonly property color accentSoft:    "#e8b4b4"
    readonly property color secondary:     "#3949ab"  // indigo
    readonly property color highlight:     "#c89a3c"  // amber/gold
    readonly property color positive:      "#2a8a2a"
    readonly property color negative:      "#a83232"
    readonly property color heading:       "#8a5a1a"  // burnt-gold for titles

    // --- ring / element palette ------------------------------------
    readonly property color ringEarth:     "#8d6e63"
    readonly property color ringAir:       "#5d8aa8"
    readonly property color ringWater:     "#2f6ea5"
    readonly property color ringFire:      "#c0392b"
    readonly property color ringVoid:      "#6b4f9e"

    // --- flag palette (honor / glory / status / taint / infamy) ----
    readonly property color flagHonor:     "#2a8a2a"
    readonly property color flagGlory:     "#c89a3c"
    readonly property color flagStatus:    "#3949ab"
    readonly property color flagTaint:     "#5c3a82"
    readonly property color flagInfamy:    "#a83232"

    // --- structure -------------------------------------------------
    // Stronger than palette.mid so dividers/borders read on both
    // light and dark themes without looking washed-out.
    readonly property color divider:       "#9c8e80"
    readonly property real  dividerOpacity: 0.6
    readonly property color borderStrong:  "#5a4a3a"
    readonly property color borderSubtle:  "#9c8e80"

    // --- parchment surfaces ---------------------------------------
    // The sheet IS the app: window bg, sidebar, and panels all share
    // these warm cream tones rather than living on the OS theme bg.
    // `parchment` is the main field; `parchmentSidebar` is a clearly
    // darker shade for the TOC so the navigation reads as a separate
    // zone without breaking the "one document" illusion.
    // `parchmentInset` is the alternate-row / cell tone used by tables
    // and lighter input wells.  `ink` is the body text colour applied
    // via palette overrides so descendants render dark-on-cream
    // regardless of the OS theme.
    readonly property color parchment:        "#f4ead5"
    readonly property color parchmentSidebar: "#e6d4ac"
    readonly property color parchmentInset:   "#ece1c4"
    readonly property color parchmentBase:    "#fdf6e3"
    readonly property color ink:              "#2a221b"

    // --- layout / typography --------------------------------------
    readonly property int   sectionSpacing: 14
    readonly property int   groupSpacing:   10
    readonly property int   formSpacing:    8
    readonly property int   pointDotSize:   14
    readonly property int   pointDotSpacing: 4
    readonly property int   smallFont:      11
    readonly property int   bodyFont:       13
    readonly property int   titleFont:      18
    readonly property int   headerFont:     20

    // Display face for section headers, ring labels, derived stats,
    // dialog titles -- anything that should feel like a character
    // sheet rather than a system dialog. The .ttf is bundled in
    // l5r/share/fonts/ and registered at qmlui bootstrap via
    // QFontDatabase.addApplicationFont(), so this name resolves on
    // every OS without any user-side install. QML's `font.family`
    // takes a single family name (no CSS-style fallback chain), so
    // shipping the asset is the only way to guarantee identity.
    // Body text intentionally inherits the OS UI font.
    readonly property string fontDisplay: "Cinzel"
    // Cinzel has thin strokes below ~22px and reads anaemic at any
    // weight under 900 on the parchment surface. Headers use this
    // semantic token so a single bump here lifts every banner / title
    // / ring label without hunting through call sites.
    readonly property int headingWeight: Font.Black
    // OpenType tabular-figures feature. Apply via `font.features` on
    // any Label that holds a number stacked above/below another -- ring
    // ranks, XP totals, skill ranks, wound thresholds. Without this,
    // Cinzel uses proportional figures and a column of "1 / 5 / 3 / 8"
    // dances horizontally row-to-row. Requires Qt 6.6+.
    readonly property var tabularNumbers: ({ "tnum": 1 })
    readonly property real watermarkOpacity: 0.06
    // Rice-paper fibre noise drawn on top of the parchment fill in
    // RicePaperOverlay. 0.06 reads as texture without dirtying the
    // ink contrast underneath.
    readonly property real paperTextureOpacity: 0.06

    // Helper: pick the matching flag colour by key.
    function flagColor(key) {
        switch (key) {
        case "honor":  return flagHonor
        case "glory":  return flagGlory
        case "status": return flagStatus
        case "taint":  return flagTaint
        case "infamy": return flagInfamy
        default:       return accent
        }
    }

    // Helper: pick the matching ring colour by key.
    function ringColor(key) {
        switch (key) {
        case "earth": return ringEarth
        case "air":   return ringAir
        case "water": return ringWater
        case "fire":  return ringFire
        case "void":  return ringVoid
        default:      return accent
        }
    }
}
