// Copyright (C) 2014-2026 Daniele Simonetti
// App-wide style constants for the QML UI. Used everywhere via
//     import Theme 1.0
//     Label { color: Theme.accent }
// The import path is registered in l5r.qmlui.app.run_qml_app(). Most
// colours are fixed L5R-themed hues that read on both light and dark
// system palettes; semantic neutrals fall back to `palette.*` at call
// sites so they still respect the OS theme.
pragma Singleton
import QtQuick

QtObject {
    // ===============================================================
    // COLOUR PALETTE -- hex values per design system §2. Token NAMES
    // are kept as the existing *semantic* names (heading, divider,
    // parchment, flagHonor…) rather than the spec's literal-colour
    // names (accentGold, parchmentBorder, paper…): the semantic names
    // survive a re-theme better, and renaming would risk substring
    // collisions (accent ⊂ accentMuted/accentSoft). Genuinely-new spec
    // tokens that had no existing equivalent are added below with
    // spec-style names (inkMuted, whiteWash, secondaryDark/Soft,
    // warning, errorBorder, disabled*). Mapping of name → spec token is
    // noted per line.
    // ===============================================================

    // --- brand accents (design system §2.2) ------------------------
    readonly property color accent: "#8B1A1A"          // accent-crimson: primary action, active nav
    readonly property color accentMuted: "#6B1010"     // accent-crimson-dark: hover/pressed
    readonly property color accentSoft: "#F5E0E0"      // accent-crimson-bg: selected-item wash (Burden)
    readonly property color secondary: "#4A6FA5"       // accent-blue: blessing / advantage actions
    readonly property color secondaryDark: "#3A5A8A"   // accent-blue-dark: blue hover/pressed (NEW)
    readonly property color secondarySoft: "#E0E8F5"   // accent-blue-bg: selected-item wash, Blessing (NEW)
    readonly property color heading: "#B8860B"         // accent-gold: headings, titles, XP values, +N
    readonly property color highlight: "#D4A017"       // accent-gold-light: highlighted numbers, active rank
    readonly property color positive: "#3A7A3A"        // success: positive feedback
    readonly property color warning: "#B87A1A"         // warning: glory, cost warnings (NEW)
    readonly property color negative: "#8B1A1A"        // error (reuses crimson)
    readonly property color errorBorder: "#C03030"     // error-state input borders (NEW)

    // --- ink / text (design system §2.1) ---------------------------
    readonly property color ink: "#2C1A0E"             // primary text (body, labels)
    readonly property color inkMuted: "#6B4F35"        // secondary text: captions, placeholders, metadata (NEW)
    readonly property color inkFaint: "#A08060"        // tertiary text: disabled, hints (NEW)

    // --- ring / element palette (design system §2.3) ---------------
    readonly property color ringEarth: "#5C4A30"
    readonly property color ringAir: "#4A7A8A"
    readonly property color ringWater: "#2A4A7A"
    readonly property color ringFire: "#8B2A1A"
    readonly property color ringVoid: "#4A2A6A"

    // --- flag palette (honor / glory / status / taint / infamy) ----
    // Mapped onto §2.4 status hues where the spec defines one; taint
    // keeps its domain purple (no spec token).
    readonly property color flagHonor: "#3A7A3A"       // = success
    readonly property color flagGlory: "#B87A1A"       // = warning
    readonly property color flagStatus: "#4A6FA5"      // = accent-blue
    readonly property color flagTaint: "#5c3a82"       // domain purple (extra, no spec token)
    readonly property color flagInfamy: "#8B1A1A"      // = error/crimson

    // --- structure / borders (design system §2.1) ------------------
    readonly property color divider: "#C8B89A"         // parchment-border: default divider
    readonly property real dividerOpacity: 0.8
    readonly property color borderSubtle: "#C8B89A"    // parchment-border
    readonly property color borderStrong: "#5a4a3a"    // strong sepia border (extra, no spec token)

    // --- parchment surfaces (design system §2.1) -------------------
    // The sheet IS the app: window bg, sidebar, and panels all share
    // these warm cream tones. `parchment` is the main field (paper);
    // `parchmentSidebar` the darker TOC / alternating-row tone
    // (paper-dark); `parchmentBase` the input-fill / hover tone
    // (paper-light); `whiteWash` the dialog/modal overlay. `ink` is the
    // body text colour applied via palette overrides so descendants
    // render dark-on-cream. `parchmentInset` is a mid cell tone kept as
    // an extra (sits between paper and paper-dark; no exact spec token).
    readonly property color parchment: "#F5EDD6"       // paper: primary background
    readonly property color parchmentSidebar: "#EDE0C0"// paper-dark: sidebar, alternating rows
    readonly property color parchmentBase: "#FAF4E4"   // paper-light: input fills, hover backgrounds
    readonly property color whiteWash: "#FFFDF5"       // dialog overlays / modal surfaces (NEW)
    readonly property color parchmentInset: "#ece1c4"  // mid cell tone (extra, between paper & paper-dark)

    // --- disabled (design system §2.4) -----------------------------
    readonly property color disabledBg: "#DDD0B8"      // disabled control fills (NEW)
    readonly property color disabledText: "#A08060"    // disabled control labels (NEW)

    // --- spacing scale (8px base grid, design system §4.1) --------
    // Names mirror the design-system tokens s1..s7 so call sites read
    // straight off the spec. 8px is the base unit; s1 is the only
    // sub-base step (tight icon/label gaps).
    readonly property int s1: 4    // tight gaps (icon<->label, rank-button gap)
    readonly property int s2: 8    // default inner padding for small controls
    readonly property int s3: 12   // list-item vertical padding
    readonly property int s4: 16   // section / card inner padding
    readonly property int s5: 24   // between sections
    readonly property int s6: 32   // dialog internal sections
    readonly property int s7: 48   // top/bottom margins on major containers

    // Component-local metrics, NOT part of the global scale: the
    // social / void point-track dots (design §6.12 fixes the dot at
    // 14px with a 4px gap).
    readonly property int pointDotSize: 14
    readonly property int pointDotSpacing: 4
    // Tenth-digit rendered inside each dot on the social tracks
    // (design §6.12: the digit spells out that dots are tenths of a
    // rank). Sized to sit inside the 14px dot with breathing room.
    readonly property int pointDotDigitSize: 9

    // --- font families (design system §3.1) ------------------------
    // Each face is bundled in l5r/share/fonts/ and registered at qmlui
    // bootstrap via QFontDatabase.addApplicationFont(), so the names
    // below resolve on every OS without a user-side install. QML's
    // `font.family` takes a single family name (no CSS-style fallback
    // chain), so shipping the asset is the only guarantee of identity.
    //
    //   fontDisplay -- Cinzel. Section/dialog titles, headings, ring
    //                  LABELS (not the numerals); ALL-CAPS banners.
    //   fontBody    -- IM Fell English. Body copy, field labels,
    //                  captions. Also set app-wide as the default QFont
    //                  in l5r.qmlui.app._apply_body_font so plain
    //                  Labels/controls inherit it; this token is the
    //                  explicit handle for places that set a family.
    //                  NB: the .ttf's internal family is the ALL-CAPS
    //                  "IM FELL English". Qt matches case-insensitively
    //                  but we pin the exact name so QFont.exactMatch()
    //                  is true and style selection is unambiguous.
    //   fontStat    -- EB Garamond. ALL numeric stat displays: ring
    //                  ranks, attribute/insight/rank values, initiative
    //                  & armor TN, skill ranks, XP cost figures. Keeps
    //                  the figures visually distinct from Cinzel heads.
    readonly property string fontDisplay: "Cinzel"
    readonly property string fontBody: "IM FELL English"
    readonly property string fontStat: "EB Garamond"
    // Brush-style kanji face (Kōzan Mōhitsu / 衡山毛筆) bundled in
    // l5r/share/fonts/KouzanMouhituFontOTF.otf. Used wherever a CJK
    // glyph appears on the sheet -- the TOC icon column, the
    // section-header icon, and the large watermark behind each
    // section. Cinzel/EB Garamond have zero CJK coverage so kanji on
    // those slots would otherwise fall back to the OS system font;
    // pinning a bundled brush face here makes the aesthetic identical
    // across every install. The family name below (KouzanBrushFontOTF)
    // is the OTF's internal family, NOT the file stem -- Qt registers
    // by metadata, not by filename. (Not in the design-system token
    // table, which omits the kanji face, but required by §3.3 / §7.)
    readonly property string fontKanji: "KouzanBrushFontOTF"

    // --- font weights (design system §3.1 / §3.4) ------------------
    // QFont.Weight numeric scale. ALWAYS set font.weight from one of
    // these -- never font.bold (which forces 700 and faux-bolds the
    // single-weight body face). Per-family policy (§3.4):
    //   Cinzel  -- never below wSemiBold. The *variable* Cinzel we ship
    //              renders 600/700/800 IDENTICALLY (one heavy bucket);
    //              only 900 (wBlack) is distinctly heavier. So use
    //              wBlack for prominent display (titles, section headers,
    //              ring labels) and wSemiBold/wBold for smaller labels &
    //              buttons -- the latter two are cosmetically identical
    //              in the variable face but stay semantically correct
    //              (and ready for static instances per §3.1).
    //   IM Fell -- wRegular only; it has no real bold cut.
    //   EB Gar. -- wSemiBold@36, wMedium@22, wRegular@<=15 (the shipped
    //              variable EB Garamond renders all four weights).
    readonly property int wRegular: 400     // Font.Normal
    readonly property int wMedium: 500      // Font.Medium
    readonly property int wSemiBold: 600    // Font.DemiBold
    readonly property int wBold: 700        // Font.Bold
    readonly property int wBlack: 900       // Font.Black -- Cinzel display only

    // --- type scale (design system §3.2) ---------------------------
    // fs* = "font size", keyed to the spec's named roles. Display /
    // heading / label / caption pair with fontDisplay or fontBody;
    // the stat* + xpValue sizes pair with fontStat.
    readonly property int fsDisplay: 22     // page / section title (Cinzel)
    readonly property int fsHeading1: 18    // dialog title (Cinzel)
    readonly property int fsHeading2: 15    // sub-section header (Cinzel)
    readonly property int fsLabel: 13       // field label, column header (Cinzel)
    readonly property int fsBody: 13        // description paragraphs, notes (IM Fell)
    readonly property int fsCaption: 11     // hints, metadata, taglines (IM Fell)
    readonly property int fsStatLarge: 36   // ring numeral / hero stat (EB Garamond)
    readonly property int fsStatMedium: 20  // attribute value, insight, rank
    readonly property int fsStatSmall: 15   // skill rank, xp-cost labels
    readonly property int fsXpValue: 28     // "+N XP" cost figure (EB Garamond bold)

    // Convenience alias for the Cinzel display weight: wBlack (900).
    // This is the ONLY weight the shipped variable Cinzel renders
    // heavier than the 600/700/800 bucket, so it's what gives titles,
    // section headers and ring labels their presence on parchment (and
    // restores the original Font.Black look). New call sites may read
    // this for any prominent Cinzel heading; smaller Cinzel labels &
    // buttons should use wSemiBold / wBold directly per §3.4.
    readonly property int headingWeight: wBlack
    // OpenType tabular-figures feature. Apply via `font.features` on
    // any Label that holds a number stacked above/below another -- ring
    // ranks, XP totals, skill ranks, wound thresholds. Without this,
    // a column of "1 / 5 / 3 / 8" dances horizontally row-to-row as the
    // proportional figures shift. Both Cinzel and EB Garamond ship the
    // feature. Requires Qt 6.6+.
    readonly property var tabularNumbers: ({
            "tnum": 1
        })
    // --- motion (design system §9) ---------------------------------
    // Subtle, functional durations (ms). The setting is meditative --
    // no playful bounces. Easing *type* is chosen per call site
    // (Easing.OutQuad for entrances, InQuad for exits, InOutQuad for
    // the symmetric toggle) since QML easing is an enum, not a value.
    //   durHover -- button hover/press feedback (§9: 120 ms)
    //   durFast  -- list-item / dropdown / dialog-close (§9: 150 ms)
    //   durBase  -- dialog open, toggle switch, toast (§9: 200 ms)
    readonly property int durHover: 120
    readonly property int durFast: 150
    readonly property int durBase: 200

    readonly property real watermarkOpacity: 0.06
    // Rice-paper fibre noise drawn on top of the parchment fill in
    // RicePaperOverlay. 0.06 reads as texture without dirtying the
    // ink contrast underneath.
    readonly property real paperTextureOpacity: 0.06

    // Helper: pick the matching flag colour by key.
    function flagColor(key) {
        switch (key) {
        case "honor":
            return flagHonor;
        case "glory":
            return flagGlory;
        case "status":
            return flagStatus;
        case "taint":
            return flagTaint;
        case "infamy":
            return flagInfamy;
        default:
            return accent;
        }
    }

    // Helper: pick a recognizable hue per weapon category so the rack
    // rails and the Add-Weapon catalogue colour-code at a glance. Reuses
    // existing palette tokens (no new hues): the warrior's crimson for
    // melee, distance-blue for ranged, an amber for arrows.
    function weaponCategoryColor(key) {
        switch (key) {
        case "melee":
            return accent;
        case "ranged":
            return secondary;
        case "arrow":
            return warning;
        default:
            return accent;
        }
    }

    // Helper: pick the matching ring colour by key.
    function ringColor(key) {
        switch (key) {
        case "earth":
            return ringEarth;
        case "air":
            return ringAir;
        case "water":
            return ringWater;
        case "fire":
            return ringFire;
        case "void":
            return ringVoid;
        default:
            return accent;
        }
    }
}
