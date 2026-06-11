# Legend of the Five Rings 4E — UI Design System
## Character Generator · PySide6 / QML · Light Theme

> **How to use this document**  
> Pass this file to Claude Code as the authoritative style reference.  
> Every component, dialog, form, and control in the application must derive from the tokens defined here. Do not introduce colours, fonts, or spacing values that are not in this spec without first adding them to the token tables.

---

## 1. Design Philosophy

The interface evokes a **feudal Japanese manuscript** — rice-paper pages, hand-brushed kanji, lacquered wood accents, and the muted ochres/crimsons of Rokugan heraldry. The aesthetic must feel *aged but legible*: ornate enough to evoke the setting, clean enough to serve as a functional character-management tool.

Key pillars:
- **Wabi-sabi warmth** — off-whites and warm tans instead of pure white; no harsh blacks.
- **Clan colour identity** — accent colours shift per clan (see Section 5) but the layout stays stable.
- **Kanji as decoration** — large semi-transparent kanji glyphs in section headers and sidebar icons; never primary information carriers.
- **Rice-paper texture** — subtle paper grain on all background surfaces.

---

## 2. Colour Palette

### 2.1 Base / Neutral Tokens

| Token | Hex | Usage |
|---|---|---|
| `--color-paper` | `#F5EDD6` | Primary background (all panels, cards) |
| `--color-paper-dark` | `#EDE0C0` | Secondary background (sidebar, alternating rows) |
| `--color-paper-light` | `#FAF4E4` | Input field fills, hover state backgrounds |
| `--color-parchment-border` | `#C8B89A` | Default border / divider colour |
| `--color-ink` | `#2C1A0E` | Primary text (body, labels) |
| `--color-ink-muted` | `#6B4F35` | Secondary text (captions, placeholders, metadata) |
| `--color-ink-faint` | `#A08060` | Tertiary text (disabled, hints) |
| `--color-white-wash` | `#FFFDF5` | Dialog overlays, modal surfaces |

### 2.2 Accent / Semantic Tokens

| Token | Hex | Usage |
|---|---|---|
| `--color-accent-crimson` | `#8B1A1A` | Primary action (Accept, Inscribe, Add buttons), active nav |
| `--color-accent-crimson-dark` | `#6B1010` | Hover/pressed state of crimson buttons |
| `--color-accent-crimson-bg` | `#F5E0E0` | Light wash behind selected list items (Burden screen) |
| `--color-accent-gold` | `#B8860B` | Headings, section titles, XP values, +N labels |
| `--color-accent-gold-light` | `#D4A017` | Highlighted numbers, active rank buttons |
| `--color-accent-blue` | `#4A6FA5` | Blessing/Advantage actions (Inscribe button) |
| `--color-accent-blue-dark` | `#3A5A8A` | Hover/pressed state of blue buttons |
| `--color-accent-blue-bg` | `#E0E8F5` | Selected list item wash on Blessing screen |

### 2.3 Ring Colours (Rings and Attributes panel)

| Ring | Token | Hex |
|---|---|---|
| Earth | `--color-ring-earth` | `#5C4A30` |
| Air | `--color-ring-air` | `#4A7A8A` |
| Water | `--color-ring-water` | `#2A4A7A` |
| Fire | `--color-ring-fire` | `#8B2A1A` |
| Void | `--color-ring-void` | `#4A2A6A` |

Each ring card uses its token as the card background. Text inside ring cards is always `#FFFFFF`.

### 2.4 Status / Feedback Colours

| Token | Hex | Usage |
|---|---|---|
| `--color-success` | `#3A7A3A` | Honor dot (filled), positive feedback |
| `--color-warning` | `#B87A1A` | Glory, costs warnings |
| `--color-error` | `#8B1A1A` | Validation errors (re-uses crimson) |
| `--color-error-border` | `#C03030` | Error-state input borders |
| `--color-disabled-bg` | `#DDD0B8` | Disabled control fills |
| `--color-disabled-text` | `#A08060` | Disabled control labels |

---

## 3. Typography

### 3.1 Font Stack

| Role | Font | Weights used | Fallback | Notes |
|---|---|---|---|---|
| Display / Section titles | `Cinzel` | SemiBold 600, Bold 700, Black 900 | `Trajan Pro`, serif | ALL-CAPS spaced headings (`letter-spacing: 0.08em`). **Never below 600**; Black 900 (`wBlack`) for the most prominent headers — see 3.4 |
| Body / Labels | `IM Fell English` | Regular 400 only | `Palatino Linotype`, `Book Antiqua`, serif | **Single-weight family — no bold variant exists**; see 3.4 |
| Stat numbers | `EB Garamond` | Regular 400, Medium 500, SemiBold 600 | `Garamond`, serif | Large ring/stat numbers |
| Kanji decorations | `KouzanBrushFontOTF` | as-shipped | `Source Han Serif`, serif | Semi-transparent overlays only; single weight |
| UI utility (placeholders, hints) | `IM Fell English` italic | Italic 400 | same | Italic variant for placeholder strings |

> **Embedding:** Cinzel and EB Garamond are variable/multi-weight families — bundle the specific static instances the spec uses (do **not** rely on Qt synthesising weights, which produces uneven stems at UI sizes). Place the following in `/assets/fonts/` and register each at startup with `QFontDatabase.addApplicationFont`:
> - `Cinzel-SemiBold.ttf` (600), `Cinzel-Bold.ttf` (700)
> - `IMFellEnglish-Regular.ttf` (400), `IMFellEnglish-Italic.ttf` (400 italic)
> - `EBGaramond-Regular.ttf` (400), `EBGaramond-Medium.ttf` (500), `EBGaramond-SemiBold.ttf` (600)
>
> After registering, always set `font.weight` explicitly (via the `Theme` weight tokens in 12.1) rather than `font.bold: true`. `font.bold` maps to weight 700 and will pick the wrong static instance for any element specced at 600.

### 3.2 Type Scale

| Token | Size (px) | Weight | Family | Usage |
|---|---|---|---|---|
| `--text-display` | 22 | 700 (Bold) | Cinzel | Page/section title (e.g. "Character", "Skills") |
| `--text-heading-1` | 18 | 700 (Bold) | Cinzel | Dialog title (e.g. "Antisocial", "Wealthy") |
| `--text-heading-2` | 15 | 600 (SemiBold) | Cinzel | Sub-section header (e.g. "Rings and Attributes") |
| `--text-label` | 13 | 600 (SemiBold) | Cinzel | Field label, column header — **600, not Regular**: Cinzel at 13 px loses legibility below SemiBold |
| `--text-body` | 13 | 400 (Regular) | IM Fell English | Description paragraphs, notes |
| `--text-caption` | 11 | 400 (Regular) | IM Fell English | Hints, metadata, "Core book p.156" |
| `--text-caption-italic` | 11 | 400 (Italic) | IM Fell English | Taglines under dialog titles |
| `--text-stat-large` | 36 | 600 (SemiBold) | EB Garamond | Ring number inside coloured card |
| `--text-stat-medium` | 22 | 500 (Medium) | EB Garamond | Attribute value, Insight, Rank |
| `--text-stat-small` | 15 | 400 (Regular) | EB Garamond | Skill rank, XP cost labels |
| `--text-xp-value` | 28 | 600 (SemiBold) | EB Garamond | "+2 XP" cost display in dialogs |

Weight values are the standard CSS/`QFont.Weight` numeric scale (400 = Normal, 500 = Medium, 600 = DemiBold, 700 = Bold).

### 3.3 Kanji Decoration

Large kanji characters are placed as **decorative background elements** (not interactive):
- Colour: `--color-ink` at **8–12 % opacity**
- Size: 120–200 px depending on context
- Position: top-right or bottom-right of a panel/card, clipped to the panel bounds
- Each major section has a dedicated kanji (see Section 7 — Section Kanji Map)

### 3.4 Font Weight Policy

Each family has different weight characteristics, and the wrong weight at UI sizes is the single most common way this theme reads as "off". Follow these per-family rules.

**Cinzel (titles, labels, buttons) — minimum weight 600.**
Cinzel is a high-contrast Trajan-style display face: its thin strokes and small counters disappear at UI sizes when set Regular (400) or Medium (500), exactly the legibility problem to avoid. Therefore:
- Never set Cinzel below **600 (SemiBold)** anywhere in the application, regardless of size.
- Use **600 (SemiBold)** for everything ≤ 15 px (labels, sub-headings, button text, the `OrnateDivider` fleuron).
- Use **700 (Bold)** for dialog titles and the *active* state of rank buttons, where extra presence reads as "selected".
- Use **900 (Black, `Theme.wBlack`)** for the most prominent display Cinzel — page/section headers, ring labels, the sidebar character name — where maximum presence on parchment is wanted. This is also the `Theme.headingWeight` convenience alias.
- **Variable-font caveat (current build).** The shipped *variable* Cinzel renders **600 / 700 / 800 identically** (one heavy bucket); only **900** is distinctly heavier. So with the current asset `wSemiBold` and `wBold` look the same on Cinzel, and `wBlack` is the only way to get a heavier display weight — which is why prominent headers use `wBlack`. The 600-vs-700 distinction above only becomes visible if the static `Cinzel-SemiBold`/`Cinzel-Bold` instances (§3.1) are ever bundled; keep setting the semantically-correct weight regardless so the UI is ready for that swap.
- ALL-CAPS + `letter-spacing: 0.08em` is mandatory on Cinzel; it compensates for the tight default spacing and improves caps legibility.

**IM Fell English (body, captions) — Regular 400 only; there is no bold.**
IM Fell English is effectively a single-weight family (Regular + matching Italic). There is no genuine bold cut.
- Do **not** request a bold weight or set `font.bold: true` on body text — Qt would synthesise a faux-bold with smeared, uneven stems that clashes with the period feel.
- For emphasis inside body text, in order of preference: (1) switch the emphasised run to **gold** (`--color-accent-gold`), (2) use the **Italic** variant, or (3) promote the phrase to **Cinzel SemiBold** if it is acting as a label rather than prose. Never fake-bold.

**EB Garamond (stat numbers) — weight scales with size.**
Garamond reads well across weights, so weight is used here to give numeric elements presence proportional to their size:
- 36 px ring numbers → **600 (SemiBold)** so they hold up against the saturated ring-card backgrounds.
- 22 px attribute/Insight/Rank values → **500 (Medium)**.
- ≤ 15 px stat labels → **400 (Regular)**.
- The 28 px XP value → **600 (SemiBold)** in gold; this replaces the earlier "Bold" call — 700 in gold over `--color-white-wash` clots optically, 600 stays crisp.

**Implementation rule.** Always set `font.weight` to one of the `Theme` weight tokens (12.1). Never use `font.bold: true` as a shortcut: it maps to 700 and will silently select the wrong bundled static instance for any 600-spec element, and triggers synthetic bolding for IM Fell English.

---

## 4. Spacing & Layout Grid

### 4.1 Base Unit

All spacing derives from an **8 px base unit**.

| Token | Value | Usage |
|---|---|---|
| `--space-1` | 4 px | Tight gaps (icon↔label, rank-button gap) |
| `--space-2` | 8 px | Default inner padding for small controls |
| `--space-3` | 12 px | List item vertical padding |
| `--space-4` | 16 px | Section padding, card inner padding |
| `--space-5` | 24 px | Between sections |
| `--space-6` | 32 px | Dialog internal sections |
| `--space-7` | 48 px | Top/bottom margins on major containers |

### 4.2 Main Window Layout

```
┌──────────────────────────────────────────────────────────┐
│  SIDEBAR  │              CONTENT AREA                    │
│  240 px   │              flex / 1                        │
│           │                                              │
│  Nav list │  Section header (kanji + title)              │
│           │  ─────────────────────────────────────────   │
│           │  Content panels                              │
│           │                                              │
└──────────────────────────────────────────────────────────┘
```

- **Sidebar width:** 240 px fixed
- **Content area:** fills remaining width; minimum 600 px
- **Content horizontal padding:** `--space-5` (24 px) left and right
- **Content vertical padding:** `--space-5` (24 px) top, `--space-4` (16 px) bottom

### 4.3 Dialog Layout

```
┌─────────────────────────────────────────────────────┐
│  HEADER BAR  (kanji icon 48×48 + title + tagline)   │  56 px
├──────────────┬──────────────────────────────────────┤
│  LIST PANEL  │  DETAIL PANEL                        │
│  280 px      │  flex / 1                            │
│              │                                      │
│  search bar  │  title + divider                     │
│  (optional)  │  description text                    │
│  list items  │  rank selector                       │
│              │  notes input                         │
│              │  cost box                            │
├──────────────┴──────────────────────────────────────┤
│  STATUS BAR (left: summary text)  │  Cancel  Accept │  48 px
└─────────────────────────────────────────────────────┘
```

- **Dialog minimum size:** 820 × 560 px
- **List panel width:** 280 px fixed
- **Header bar height:** 56 px; background `--color-accent-crimson-bg` (Burden) or `--color-accent-blue-bg` (Blessing)
- **Status/footer bar height:** 48 px; background `--color-paper-dark`; 1 px top border `--color-parchment-border`

---

## 5. Clan Accent Overrides

The sidebar header displays the active character's clan. The accent colour pair `--color-accent-primary` / `--color-accent-primary-dark` is overridden at runtime.

| Clan | Primary | Dark |
|---|---|---|
| Crab | `#5A5A2A` (olive) | `#404020` |
| Crane | `#4A6FA5` (blue) | `#3A5A8A` |
| Dragon | `#2A6A4A` (jade) | `#1A5A3A` |
| Lion | `#B8860B` (gold) | `#8A6208` |
| Mantis | `#2A7A5A` (teal) | `#1A6A4A` |
| Phoenix | `#8B4A1A` (rust) | `#6B3A10` |
| Scorpion | `#8B1A1A` (crimson) | `#6B1010` |
| Spider | `#3A2A4A` (dark purple) | `#2A1A3A` |
| Unicorn | `#6A2A6A` (purple) | `#5A1A5A` |
| Ronin / Other | `#5A4A3A` (dark tan) | `#4A3A2A` |

Apply overrides via QML dynamic properties or a QML `QtObject` singleton that other components bind to.

---

## 6. Component Specifications

### 6.1 Sidebar

```
Background:      --color-paper-dark
Width:           240 px fixed
Top block:       character name (--text-display), clan·rank (--text-caption),
                 school (--text-caption-italic); 16 px padding; bottom border 1px --color-parchment-border
Nav items:       height 44 px; horizontal padding 16 px
                 kanji glyph (24 px) left-aligned; label (--text-label) 12 px after glyph
Active item:     left border 3px solid --color-accent-crimson; background --color-paper; text --color-accent-crimson
Hover item:      background --color-paper; text --color-ink
Inactive:        text --color-ink-muted
Divider:         1 px --color-parchment-border; full width
```

### 6.2 Primary Button (Accept / Inscribe / Add)

```
Height:          40 px
Horizontal pad:  20 px
Border-radius:   3 px
Background:      --color-accent-crimson  (Burden/default) | --color-accent-blue (Blessing)
Text:            --color-white-wash, --text-label, weight 600 (Theme.wSemiBold), uppercase, letter-spacing 0.08em
Icon:            16 px kanji glyph left of text; gap 8 px
Hover:           background --color-accent-crimson-dark / --color-accent-blue-dark
Pressed:         background darkened 10 %; subtle inset shadow
Disabled:        background --color-disabled-bg; text --color-disabled-text; no shadow
```

### 6.3 Secondary Button (Cancel)

```
Height:          40 px
Horizontal pad:  20 px
Border-radius:   3 px
Background:      transparent
Border:          1px solid --color-parchment-border
Text:            --color-ink-muted, --text-label, weight 600 (Theme.wSemiBold), uppercase, letter-spacing 0.08em
Hover:           background --color-paper; border --color-ink-muted
Pressed:         background --color-paper-dark
```

### 6.4 Rank Selector (numbered buttons in a row)

Used for selecting rank 1–N on advantages, disadvantages, spells, etc.

```
Button size:     36 × 36 px
Border-radius:   2 px
Inactive:        background transparent; border 1px --color-parchment-border; text --color-ink-muted
Active/selected: background --color-accent-crimson (Burden) | --color-accent-blue (Blessing)
                 border transparent; text --color-white-wash; weight 700 (Theme.wBold)
Hover (inactive):background --color-paper; border --color-ink-muted
Gap between:     4 px
Font:            --text-stat-small
Overflow (>10):  wrap to second row; second-row buttons same size
```

### 6.5 Text Input / Notes Field

```
Height:          36 px (single-line) | auto (multi-line)
Background:      --color-paper-light
Border:          1px solid --color-parchment-border
Border-radius:   2 px
Padding:         8 px horizontal, 6 px vertical
Font:            --text-body (IM Fell English italic for placeholder)
Placeholder:     --color-ink-faint
Focus border:    1px solid --color-accent-gold
Error border:    1px solid --color-error-border; faint red wash background
```

### 6.6 Search Bar (in dialogs)

```
Same as Text Input but:
Leading icon:    14 px magnifying-glass SVG; colour --color-ink-faint; 10 px left of text
Height:          36 px
Background:      --color-paper-light
Full width within its container
```

### 6.7 Dropdown / ComboBox (category filter)

```
Height:          36 px
Padding:         10 px horizontal
Background:      --color-paper-light
Border:          1px solid --color-parchment-border
Border-radius:   2 px
Text:            --text-label; colour --color-ink
Arrow icon:      8 px triangle; right 10 px; colour --color-ink-muted
Popup:           background --color-white-wash; border 1px --color-parchment-border;
                 shadow 0 4px 12px rgba(0,0,0,0.18); border-radius 2 px
Popup item height: 32 px; horizontal padding 12 px
Popup hover:     background --color-accent-crimson-bg; text --color-ink
Popup selected:  background --color-paper-dark; weight 600 (Theme.wSemiBold)
```

### 6.8 Toggle Switch (Override cost)

```
Width:           44 px; Height: 24 px; Border-radius: 12 px
Off state:       track --color-disabled-bg; thumb --color-white-wash
On state:        track --color-accent-gold; thumb --color-white-wash
Transition:      200 ms ease
Label:           --text-caption; --color-ink-muted; 8 px left of switch
```

### 6.9 Cost / XP Box

The prominent "+N XP" box shown in the detail panel of dialogs.

```
Min-width:       100 px; Height: 56 px
Background:      --color-white-wash
Border:          1px solid --color-parchment-border
Border-radius:   3 px
Value text:      --text-xp-value; colour --color-accent-gold
Unit label:      --text-caption; colour --color-ink-faint; below or right of value
"SUGGESTED BY THE RULEBOOK" header: --text-caption; colour --color-accent-gold; uppercase; letter-spacing 0.1em
```

Manual cost variant (red border, Blessing screen):
```
Border:          1px solid --color-error-border
Value text:      colour --color-error
Spinner arrows:  right edge; 18 × 10 px each; colour --color-ink-muted
```

### 6.10 List Item (in dialog list panel)

```
Height:          44 px
Padding:         12 px horizontal, 0 vertical (text centred vertically)
Font:            --text-body; colour --color-ink
Hover:           background --color-paper
Active (selected):
  Burden:        background --color-accent-crimson-bg; left border 3px --color-accent-crimson; text --color-ink
  Blessing:      background --color-accent-blue-bg; left border 3px --color-accent-blue; text --color-ink
Divider:         0.5px --color-parchment-border between items (horizontal)
```

### 6.11 Ring / Attribute Card

```
Border-radius:   6 px
Background:      ring-specific colour (see 2.3)
Padding:         14 px
Ring value:      --text-stat-large; white; top-left
Ring name:       --text-heading-2; white; below value or right
Attribute rows:  --text-body; white; "Reflexes   4  +" layout
  Attribute name: 60 % left; value: right-aligned; "+" button: 20 px
  "+" button:    18 × 18 px; background rgba(255,255,255,0.2); border-radius 50 %;
                 colour white; font-size 14 px; hover background rgba(255,255,255,0.35)
Kanji watermark: see Section 3.3; placed bottom-right of each card, white at 12 % opacity
```

### 6.12 Honor / Glory Track

```
Dot size:        14 × 14 px; border-radius 50 %
Filled dot:      background --color-success (Honor) | --color-warning (Glory)
Empty dot:       background transparent; border 1.5px solid respective colour
Dot digit:       each dot carries its tenth value (1…9) centred inside, EB Garamond 9 px;
                 paper-coloured on a filled dot, track colour on an empty one — the digit
                 spells out that the dots are the DECIMAL part of the rank (issue #402)
Gap between:     4 px
Row layout:      header row = colour swatch + NAME + –/value/+ stepper;
                 track row underneath = "N.N" score (EB Garamond, --font-size-stat-medium,
                 tabular figures, track colour) left of the dots
Scrolling:       wheel over the track fine-tunes ±0.1 and ROLLS OVER at the rank
                 boundary: up from N.9 → (N+1).0, down from N.0 → (N−1).9
```

### 6.13 Section Divider / Horizontal Rule

Two variants. Use the **plain rule** for tight, in-panel separations (under a panel title band, between table rows); use the **ornate divider** to mark *structural* breaks between major blocks (sidebar identity block ↔ nav, between stacked sheet sections). The ornament marks structure — do not use it for every horizontal line.

**Plain rule**
```
Height:          1 px
Background:      linear-gradient(to right, transparent, --color-parchment-border 20%, --color-parchment-border 80%, transparent)
Vertical margin: --space-5 top and bottom
```

**Ornate divider** (`OrnateDivider`, `l5r/qmlui/qml/widgets/OrnateDivider.qml`)

Two faded sepia hairlines flanking a centred fleuron glyph in burnt-gold Cinzel — the document-as-character-sheet flavour.
```
Layout:          [ hairline ⟶ fill ]  glyph  [ fill ⟵ hairline ]   (gap 10 px each side)
Hairline:        1 px; colour --color-parchment-border (Theme.divider); opacity ~0.6 (Theme.dividerOpacity)
Glyph:           default fleuron "❖" (overridable via `glyph`)
                 font Cinzel (Theme.fontDisplay), weight 600 (Theme.wSemiBold); size --text-body (13)
                 colour --color-accent-gold (Theme.heading); opacity ~0.55
```
Parameters `glyph`, `ruleColor`, `ruleOpacity`, `glyphColor`, `glyphOpacity`, `glyphSize` are all overridable so the same widget covers crimson/blue accent contexts without forking.

### 6.14 Status Bar (dialog footer)

```
Height:          48 px
Background:      --color-paper-dark
Top border:      1px solid --color-parchment-border
Left text:       "This burden will grant +N XP." / "This blessing will require N XP." | --text-caption | --color-ink-muted | 16 px left
Right controls:  Cancel button + Primary button; gap 8 px; 16 px right
```

### 6.15 Header Bar (dialog top)

```
Height:          56 px
Background:      Burden → --color-accent-crimson-bg | Blessing → --color-accent-blue-bg
Left:            48 × 48 px kanji tile (background clan/action colour; kanji white; border-radius 4 px); 12 px gap
Title:           --text-heading-1 | colour --color-accent-crimson (Burden) or --color-accent-blue (Blessing)
Tagline:         --text-caption-italic | colour --color-ink-muted; directly below title
Horizontal pad:  16 px
```

### 6.16 "Add a new skill" Banner

```
Height:          56 px
Background:      --color-accent-blue-bg
Left kanji tile: same as 6.15 but smaller (36 × 36 px)
Title:           --text-heading-2; colour --color-accent-blue; uppercase
Tagline:         --text-caption-italic; colour --color-ink-muted
```

### 6.17 Scrollbars

```
Width:           6 px
Track:           transparent
Thumb:           --color-parchment-border at 70 % opacity; border-radius 3 px
Thumb hover:     --color-ink-muted at 70 % opacity
```

---

## 7. Section Kanji Map

Each section of the main navigation uses a dedicated kanji as both the sidebar icon and the section watermark.

| Section | Kanji | Unicode | Meaning |
|---|---|---|---|
| Character | 侍 | U+4F8D | Samurai |
| Skills | 技 | U+6280 | Technique/Skill |
| Merits/Flaws | 縁 | U+7E01 | Blessing/Karma |
| Techniques | 流 | U+6D41 | School / Flow |
| Spells | 呪 | U+546A | Spell |
| Kata | 型 | U+578B | Form/Kata |
| Kiho | 気 | U+6C17 | Ki/Spirit |
| Tattoos | 彫 | U+5F6B | Carve/Engrave (irezumi) |
| Advancements | 道 | U+9053 | Path/Way |
| Weapons | 刀 | U+5200 | Blade |
| Miscellanea | 雑 | U+96D1 | Miscellaneous |
| Notes | 記 | U+8A18 | Record |
| Settings | 設 | U+8A2D | Configure |

The **Burden dialog** uses 修 (U+4FEE, "endure/discipline") in its header tile.  
The **Blessing dialog** uses 縁 (U+7E01, "blessing/connection") in its header tile.

---

## 8. Texture & Background Treatment

### 8.1 Rice-Paper Texture

Apply a subtle paper-grain texture to all `--color-paper` and `--color-paper-dark` surfaces.

The texture is generated **procedurally**, not shipped as a PNG. This keeps the cxfreeze `package-data` manifest clean (no binary texture asset to bundle and track) and lets the grain scale to any panel size without tiling seams. Use the `RicePaperOverlay` widget (`l5r/qmlui/qml/widgets/RicePaperOverlay.qml`):

- Implementation: a `Canvas` that paints short ink-coloured fibre marks (1 px dots + a few short directional strokes) using a fixed-seed linear-congruential PRNG, so every surface renders the **same** stable fibre pattern (consistent fibres read as "this is the paper"; per-paint random ones read as noise that won't sit still).
- Colour & opacity: ink marks (`--color-ink`) at **~6 %** overall opacity — texture without dirtying ink contrast. Exposed as `Theme.paperTextureOpacity`.
- Placement: draw the overlay **once at the window level** so the grain stays continuous across panels and gutters (the sheet reads as one piece of paper). Panels do not own a per-panel overlay; dialogs/popups that detach from the window get their own.
- Repaint only on resize (`onWidthChanged`/`onHeightChanged`), not on scroll.

> Rationale for not using a PNG: a `ShaderEffectSource` / tiled `BorderImage` was the original plan, but the procedural `Canvas` removes a bundled asset, avoids tiling artefacts, and renders identically on every install. The PNG approach is acceptable only if the procedural path ever proves too costly on low-end hardware.

### 8.2 Worn Edges (Dialog/Panel borders)

For dialogs and prominent panels, a faint inner shadow simulates worn paper edges:
```
box-shadow (inset): 0 0 20px rgba(139, 100, 60, 0.12)
```

### 8.3 Dividing Lines

Never use solid black lines. Always use `--color-parchment-border` or the gradient described in 6.13.

---

## 9. Motion & Transitions

Keep animations subtle and functional. The setting is meditative — no playful bounces.

| Interaction | Duration | Easing |
|---|---|---|
| Button hover/press | 120 ms | `ease-out` |
| List item selection | 150 ms | `ease-out` |
| Dialog open | 200 ms | `ease-out` (opacity + slight scale from 0.97 → 1.0) |
| Dialog close | 150 ms | `ease-in` |
| Dropdown open | 150 ms | `ease-out` |
| Toggle switch | 200 ms | `ease` |
| Rank button select | 100 ms | `ease-out` |

---

## 10. Iconography

- Use only simple, flat SVG icons — no filled-style icons that look too modern.
- Icon colour is always inherited from the parent text colour token unless specified.
- Standard sizes: 12, 16, 20, 24 px.
- Kanji tiles (sidebar + dialog headers) are **text glyphs**, not images.

Core icon set needed (SVG, 20 × 20 px):

| Name | Usage |
|---|---|
| `icon-search.svg` | Search bars |
| `icon-chevron-down.svg` | Dropdown arrows |
| `icon-chevron-up.svg` | Spinner up |
| `icon-chevron-down-sm.svg` | Spinner down |
| `icon-plus.svg` | Attribute "+", stat increase |
| `icon-minus.svg` | Stat decrease |
| `icon-note.svg` | Notes tab |
| `icon-pen.svg` | Edit inline |
| `icon-trash.svg` | Remove item |
| `icon-lock.svg` | School-granted traits (non-removable) |

---

## 11. Accessibility

- All text must meet **WCAG AA contrast** against its background at the specified sizes.
- Interactive elements must have a **visible focus ring**: `outline: 2px solid --color-accent-gold; outline-offset: 2px`.
- Minimum touch target size: **36 × 36 px** (already met by the rank selector buttons).
- Do not convey information by colour alone — pair colour cues with text or iconography.
- Placeholder text must not be relied on as the sole label — always pair with a visible `<Label>`.

---

## 12. QML Implementation Notes

### 12.1 Token Singleton

The token singleton is named **`Theme`** and lives in a **`Theme` module** at `l5r/qmlui/qml/Theme/Theme.qml`, consumed everywhere via `import Theme 1.0` (e.g. `Label { color: Theme.accentCrimson }`). It is *not* named `Style`, and the module is *not* `App` — earlier drafts of this spec used those names; the implementation settled on `Theme`/`Theme` and that is authoritative. It exposes all tokens as `readonly property` values:

```qml
// l5r/qmlui/qml/Theme/Theme.qml
pragma Singleton
import QtQuick

QtObject {
    // --- Colours ---
    readonly property color paper:           "#F5EDD6"
    readonly property color paperDark:       "#EDE0C0"
    readonly property color paperLight:      "#FAF4E4"
    readonly property color parchmentBorder: "#C8B89A"
    readonly property color ink:             "#2C1A0E"
    readonly property color inkMuted:        "#6B4F35"
    readonly property color inkFaint:        "#A08060"
    readonly property color whiteWash:       "#FFFDF5"

    readonly property color accentCrimson:   "#8B1A1A"
    readonly property color accentCrimsonDk: "#6B1010"
    readonly property color accentCrimsonBg: "#F5E0E0"
    readonly property color accentGold:      "#B8860B"
    readonly property color accentGoldLight: "#D4A017"
    readonly property color accentBlue:      "#4A6FA5"
    readonly property color accentBlueDk:    "#3A5A8A"
    readonly property color accentBlueBg:    "#E0E8F5"

    // Ring colours
    readonly property color ringEarth: "#5C4A30"
    readonly property color ringAir:   "#4A7A8A"
    readonly property color ringWater: "#2A4A7A"
    readonly property color ringFire:  "#8B2A1A"
    readonly property color ringVoid:  "#4A2A6A"

    // --- Spacing ---
    readonly property int s1: 4
    readonly property int s2: 8
    readonly property int s3: 12
    readonly property int s4: 16
    readonly property int s5: 24
    readonly property int s6: 32
    readonly property int s7: 48

    // --- Fonts ---
    readonly property string fontDisplay:  "Cinzel"
    readonly property string fontBody:     "IM Fell English"
    readonly property string fontStat:     "EB Garamond"

    // Font weights (QFont.Weight numeric scale)
    readonly property int wRegular:  400   // Font.Normal
    readonly property int wMedium:   500   // Font.Medium
    readonly property int wSemiBold: 600   // Font.DemiBold
    readonly property int wBold:     700   // Font.Bold
    readonly property int wBlack:    900   // Font.Black -- Cinzel display only

    // Font sizes
    readonly property int fsDisplay:     22
    readonly property int fsHeading1:    18
    readonly property int fsHeading2:    15
    readonly property int fsLabel:       13
    readonly property int fsBody:        13
    readonly property int fsCaption:     11
    readonly property int fsStatLarge:   36
    readonly property int fsStatMedium:  22
    readonly property int fsStatSmall:   15
    readonly property int fsXpValue:     28
}
```

Register it as a QML module via a `qmldir` next to the file, not via C++ `qmlRegisterSingletonType` (this is a Python / `qtpy` app, no C++ entry point):

```
// l5r/qmlui/qml/Theme/qmldir
module Theme
singleton Theme 1.0 Theme.qml
```

The engine resolves `import Theme 1.0` because the bootstrap adds the *parent* of the module directory to the import path (see `l5r/qmlui/app.py:run_qml_app`):

```python
qml_dir = Path(__file__).parent / "qml"
engine.addImportPath(str(qml_dir))   # makes `import Theme 1.0` resolvable
```

### 12.2 Clan Accent Runtime Override

```qml
// ClanTheme.qml — writable singleton
pragma Singleton
import QtQuick 2.15

QtObject {
    property color primary:     "#4A6FA5"  // default: Crane
    property color primaryDark: "#3A5A8A"
    property color selectedBg:  "#E0E8F5"

    function setClan(clan) {
        // Set the three properties based on Section 5 lookup table
    }
}
```

### 12.3 Paper Texture

Use `RicePaperOverlay` as the background of every `Page`, `Dialog`, and panel `Rectangle`.
Example:

```qml
    background: Rectangle {
        color: Theme.parchment
        border.color: Theme.borderStrong
        border.width: 1
        radius: 2
        Widgets.RicePaperOverlay {
        }
    }
```

### 12.4 Naming Conventions

| Element type | QML file name | Example |
|---|---|---|
| Reusable control | `L5R<Name>.qml` | `L5RButton.qml`, `L5RRankSelector.qml` |
| Screen/page | `<Section>Page.qml` | `CharacterPage.qml`, `SkillsPage.qml` |
| Dialog | `<Action>Dialog.qml` | `AcceptBurdenDialog.qml` |
| Partial/sub-component | `<Parent><Part>.qml` | `RingCard.qml`, `HonorTrack.qml` |

---

## 13. Do's and Don'ts

| ✅ Do | ❌ Don't |
|---|---|
| Use tokens from `Theme.qml` for every colour and spacing value | Hard-code hex values or pixel values inline |
| Apply rice-paper texture via `RicePaperOverlay` | Use pure `#FFFFFF` or `#000000` anywhere |
| Use Cinzel for all section/dialog titles | Use system sans-serif fonts for UI headings |
| Set Cinzel at weight 600+ always (Theme.wSemiBold / wBold) | Set Cinzel at Regular/Medium — it goes spindly at UI sizes |
| Set `font.weight` from a `Theme` weight token | Use `font.bold: true` (picks weight 700, breaks 600-spec elements) |
| Emphasise body text with gold or italic | Fake-bold IM Fell English (no real bold cut exists — Qt smears it) |
| Use IM Fell English for body and labels | Use Arial, Helvetica, or Roboto anywhere |
| Use kanji as decorative watermarks only | Display kanji as the primary label for an action |
| Keep ring card text white regardless of content | Use dark text inside coloured ring cards |
| Override clan accent via `ClanTheme.qml` | Duplicate accent colour definitions per-component |
| Show XP values in `--color-accent-gold` | Show XP values in red/green unless it is an error/success state |
| Use 3 px left border + background wash for active list items | Use underline or bold alone for selection |

---

*End of design specification — v1.0 — Light Theme only*
