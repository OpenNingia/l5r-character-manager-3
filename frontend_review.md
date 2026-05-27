# QML UI design review — L5RCM

Scope: every file under `l5r/qmlui/qml/` plus the `Theme.qml` singleton. The goal is design feedback on what's been built so far — visual quality, layout, hierarchy, polish, consistency. Critique and concrete suggestions, not a rewrite.

## What's already working

A few decisions are genuinely good and worth defending:

- **`Theme.qml` as a singleton with semantic tokens** (`ringEarth`, `flagGlory`, `heading`) is the right backbone. Most "AI-generated" QML is one-off hex codes scattered everywhere — you don't have that problem.
- **`RingCard.qml`'s big-numeral-left + label-stack-right composition** is the only piece of the UI that has real *character*. The bold 36px black numeral with raised `styleColor` over a darkened element-tinted fill is doing real work.
- **Per-flag accent on the `PointTrack`** (honor in green, infamy in red, etc.) is a strong, table-anchored signal — that's the L5R sheet talking, not Material Design.
- **Scrollable-sheet + left TOC** is the right pick for this document type. The accent left-stripe on the active TOC item is restrained and correct.
- **Null-guarding `pcProxy`/`appCtrl` in bindings** — not a design point, but it tells me you sweat the details.

## The core problem: it screams "Qt Quick Controls default style"

Right now the app looks like every other "I built a QML LOB form" demo: `GroupBox` + `GridLayout` + `TextField` + `ComboBox`, native Fusion-style chrome, a tasteful red accent floating in a sea of system grey. The samurai theme exists only in the *colours*, not in the *shapes, materials, typography, or rhythm*. A user couldn't tell this was an L5R tool from a 5-meter screenshot — they'd guess "internal admin console."

The Rings & Attributes block proves the app *can* have an identity. Everything around it is undoing that work.

### Specific things that read as generic

1. **Typography is the system default.** There is not a single `font.family` set anywhere. `Theme` defines pixel sizes but no families. So every label is rendering in Segoe UI / system-ui / whatever the OS hands Qt. For an L5R sheet, that's a wasted opportunity — this is exactly the product type where a distinctive display face transforms perception. The only meaningfully styled text in the whole UI is the section header (`headerFont: 20`, `Font.DemiBold`, `Theme.heading` burnt-gold). That's not a typographic system, that's one styled label.

2. **`GroupBox` everywhere.** "Rings and Attributes", "Social / Spiritual", "Initiative", "Armor TN", "Health / Wounds", "Personal Informations". Stock `GroupBox` chrome (thin border + title overlap) is the most "Qt Designer 2005" element in the toolkit. Six of them stacked vertically is the visual signature of a CRUD app.

3. **The combat strip (Initiative / Armor TN / Wounds) is the weakest section.** Three side-by-side `GroupBox`es full of `readOnly: true` `TextField`s rendering numbers — there is zero reason a derived stat like "Current Initiative" should look like a text input. It's not editable. Using a `TextField` for a computed value isn't just stylistically generic, it actively lies to the user about affordance.

4. **`SectionBlock`'s `"#" + tabId`** in the top-right of every section header is debug UI that leaked into production styling. Either remove it or convert it to a real anchor link / chip.

5. **`AboutSection`'s rich-text link block** is a literal `<p><a>` HTML dump rendered through `Text.RichText`. It works, but it's the visual equivalent of a `README.md` glued into the app. The same content as a 4-tile link grid (project, bugs, datapacks, AEG) with iconography would feel like part of the product.

6. **`NotesSection`'s "Personal Informations"** uses `Repeater` over `RowLayout`s inside a `GridLayout` — fine mechanically, but the form ends up as two parallel stacks of `Label · TextField` with a vertical divider. That divider plus the stock chrome is the most generic-form-on-the-internet shape there is. The L5R character sheet has a *very specific* "ID-card with portrait + family bracket" layout in the books; the QML version threw that away.

7. **Spacing is uniform.** `sectionSpacing: 14`, `groupSpacing: 10`, `formSpacing: 8` — gradient is too gentle. There's no rhythmic contrast between dense data zones and breathing rooms. Everything is at "medium". A character sheet should feel like a *document*, with hierarchy that pulls the eye.

8. **No texture or atmosphere anywhere.** The app uses one of the most thematically rich visual languages on earth (sumi-e ink, mon crests, parchment, kanji-as-art) and ships a flat grey background. Even one subtle paper-texture overlay or a low-opacity mon watermark behind the section title would do more for identity than a dozen accent-colour tweaks.

9. **Dialogs use the stock `Dialog` chrome** with `standardButtons: Dialog.Ok | Dialog.Cancel`. `FamilyChooserDialog` even has the lovely flavor line *"a Samurai should serve its clan first and foremost"* — and then frames it with two off-the-shelf `ComboBox`es. The copy is doing the work the visual design isn't.

## Concrete suggestions (ordered by effort vs. impact)

### Low effort, high impact

1. **Pick two fonts and bake them into `Theme`.** Add `Theme.fontDisplay` (something with character — *Cormorant Garamond*, *EB Garamond*, *Cinzel* for headers; *IM Fell English* if you want overt period feel) and `Theme.fontBody` (a refined serif or a humanist sans like *Inter Tight* / *Public Sans* — but pick *one* and own it). Ship the .ttf in `share/` and register with `FontLoader` in `MainSheet.qml`. Apply `font.family: Theme.fontDisplay` to: section headers, RingCard ring labels, dialog titles, the About app-title. Body fields stay on `fontBody`. This single change will do more for "doesn't look AI-generated" than any other suggestion below.

2. **Kill the `"#" + tabId` chip** in `SectionBlock.qml:50-55`. Replace it with nothing, or with a small contextual action (e.g. a "Reset section" / "Collapse" / overflow menu).

3. **Stop using `TextField readOnly: true` for derived numbers.** In `CharacterSection.qml` the Initiative, Armor TN, and Wound rows all use it. Replace with a `Label` styled distinctly — large display number, label below, no input chrome. Wounds in particular should look like the real L5R wound ladder (Healthy → Out), not a form.

4. **Use the section icon as a watermark.** `SectionBlock` already receives an `icon` glyph. Render a second copy at huge size (~180px), low opacity (~0.06), absolutely positioned in the section's top-right behind the content. Costs ~6 lines, transforms the page.

### Medium effort, high impact

5. **Replace `GroupBox` with a custom `SheetPanel` component.** A `Rectangle` with: subtle paper-tinted fill (`#f6f0e3` on light theme, `#1b1714` on dark), 1px `Theme.borderStrong` border, optional top-aligned title rendered in `fontDisplay` with a hairline underline (not the GroupBox's title-overlapping-border trick). Drop it in everywhere a `GroupBox` is used today. Five-minute swap, immediate identity gain.

6. **Redesign the combat strip as a single horizontal "Combat Bar".** Three numbers (Initiative current, Armor TN current, current wound level) at display-font size, with the secondary breakdown (base/mod, base/armor/reduction, the wound ladder) as small caption rows beneath each. Currently it's three boxes of equal weight giving equal visual prominence to "Reduction" and "Current TN" — they aren't equally important in play.

7. **Render the wound ladder as a vertical track, not a grid.** The L5R wound system *is* a ladder — Healthy at top, Out at bottom, with the "currently at" position highlighted. The current 4-column `GridLayout` doesn't communicate that. A column of 8 rows with a left-side accent stripe indicating current position would be both more readable and more thematic.

8. **TOC: replace the emoji icons with proper glyphs.** Right now `modelData.icon` is a unicode character. Either commit to an icon font (FontAwesome, Lucide, or a custom L5R-themed one based on the clan mon assets) or render `Image` from SVG. The mixed emoji-rendering across OSes is one of the strongest "AI demo" tells.

### Higher effort, biggest payoff

9. **Pick an aesthetic direction and commit.** Right now the design is "neutral form UI with a red accent." Decide between, say:
   - **Edo-period ledger** — cream/parchment, brush-stroke dividers, Cinzel-style display face, mon watermarks per section, no rounded corners (`radius: 0` everywhere), hairline rules, generous margins.
   - **Modern fantasy reference tome** — deep ink-black background, gold leaf accents, two-column dense layout with marginalia (page numbers, book refs sit in a true margin column the way a real RPG book does it).
   - **Bauhaus character sheet** — flat colour blocks, strict grid, the rings as full-height vertical bars with the numeral baked in. Plays well with the existing `RingCard` direction.

   All three are coherent. The current design isn't a fourth direction — it's the absence of a choice.

10. **The identity row is the front door — treat it.** The first thing the user sees is `Name [ ] Rank [ ]` / `Clan [ ] XP [ ]` / `Family [ ] Insight [ ]` / `School [ ] [empty]`. Four columns of label-field in a `GridLayout`. This is *the character's identity* and it looks like a job application. Consider: a 2/3-width "name plate" on the left with the character name in display font + clan/family/school as a single byline ("Doji Reiko · Crane Clan · Doji Family · Kakita Bushi School"), and on the right a vertical XP/Insight/Rank metric strip with each value at display size. The "edit family/school" pencil buttons become rollover affordances on the byline.

## What to touch first if you only do one thing

Add the two fonts and apply them. Add the icon-watermark to `SectionBlock`. Replace `GroupBox` with a `SheetPanel`. Those three changes — maybe a day of work — will shift the perceived quality dramatically without rewriting any logic.

The bones are sound. The flesh is generic.
