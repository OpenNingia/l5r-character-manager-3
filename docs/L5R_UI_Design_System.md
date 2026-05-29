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

| Role | Font | Fallback | Notes |
|---|---|---|---|
| Display / Section titles | `Cinzel` | `Trajan Pro`, serif | ALL-CAPS spaced headings (`letter-spacing: 0.08em`) |
| Body / Labels | `IM Fell English` | `Palatino Linotype`, `Book Antiqua`, serif | Slightly calligraphic; use regular weight for body |
| Monospace / Stat numbers | `EB Garamond` | `Garamond`, serif | Large ring/stat numbers |
| Kanji decorations | `KouzanBrushFontOTF` | `Source Han Serif`, serif | Semi-transparent overlays only |
| UI utility (placeholders, hints) | `IM Fell English` italic | same | Italic variant for placeholder strings |

> **Embedding:** Bundle `Cinzel-Regular.ttf`, `Cinzel-Bold.ttf`, `IMFellEnglish-Regular.ttf`, `IMFellEnglish-Italic.ttf`, and `EBGaramond-Regular.ttf` in `/assets/fonts/`. Register them at application startup with `QFontDatabase::addApplicationFont`.

### 3.2 Type Scale

| Token | Size (px) | Weight | Family | Usage |
|---|---|---|---|---|
| `--text-display` | 22 | Bold | Cinzel | Page/section title (e.g. "Character", "Skills") |
| `--text-heading-1` | 18 | Bold | Cinzel | Dialog title (e.g. "Antisocial", "Wealthy") |
| `--text-heading-2` | 15 | Bold | Cinzel | Sub-section header (e.g. "Rings and Attributes") |
| `--text-label` | 13 | Regular | Cinzel | Field label, column header |
| `--text-body` | 13 | Regular | IM Fell English | Description paragraphs, notes |
| `--text-caption` | 11 | Regular | IM Fell English | Hints, metadata, "Core book p.156" |
| `--text-caption-italic` | 11 | Italic | IM Fell English | Taglines under dialog titles |
| `--text-stat-large` | 36 | Regular | EB Garamond | Ring number inside coloured card |
| `--text-stat-medium` | 22 | Regular | EB Garamond | Attribute value, Insight, Rank |
| `--text-stat-small` | 15 | Regular | EB Garamond | Skill rank, XP cost labels |
| `--text-xp-value` | 28 | Bold | EB Garamond | "+2 XP" cost display in dialogs |

### 3.3 Kanji Decoration

Large kanji characters are placed as **decorative background elements** (not interactive):
- Colour: `--color-ink` at **8–12 % opacity**
- Size: 120–200 px depending on context
- Position: top-right or bottom-right of a panel/card, clipped to the panel bounds
- Each major section has a dedicated kanji (see Section 7 — Section Kanji Map)

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
Text:            --color-white-wash, --text-label, uppercase, letter-spacing 0.08em
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
Text:            --color-ink-muted, --text-label, uppercase, letter-spacing 0.08em
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
                 border transparent; text --color-white-wash; font-weight bold
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
Popup selected:  background --color-paper-dark; font-weight bold
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
Gap between:     4 px
Row layout:      dots left-aligned; –/value/+ controls right-aligned; "rank N.N" far right
```

### 6.13 Section Divider / Horizontal Rule

```
Height:          1 px
Background:      linear-gradient(to right, transparent, --color-parchment-border 20%, --color-parchment-border 80%, transparent)
Vertical margin: --space-5 top and bottom
```

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

- Asset: `/assets/textures/rice_paper_light.png` — a 512 × 512 px seamless tileable PNG
- Blend mode: `Multiply` at **8–12 %** opacity over the solid colour
- In QML: use a `ShaderEffectSource` or a `BorderImage`/`Image` with `fillMode: Image.Tile`

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

Create `/qml/Style.qml` as a `QtObject` singleton exposing all tokens as properties:

```qml
// Style.qml
pragma Singleton
import QtQuick 2.15

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

Register it in `main.cpp`:
```cpp
qmlRegisterSingletonType(QUrl("qrc:/qml/Style.qml"), "App", 1, 0, "Style");
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
| Use tokens from `Style.qml` for every colour and spacing value | Hard-code hex values or pixel values inline |
| Apply rice-paper texture via `RicePaperOverlay` | Use pure `#FFFFFF` or `#000000` anywhere |
| Use Cinzel for all section/dialog titles | Use system sans-serif fonts for UI headings |
| Use IM Fell English for body and labels | Use Arial, Helvetica, or Roboto anywhere |
| Use kanji as decorative watermarks only | Display kanji as the primary label for an action |
| Keep ring card text white regardless of content | Use dark text inside coloured ring cards |
| Override clan accent via `ClanTheme.qml` | Duplicate accent colour definitions per-component |
| Show XP values in `--color-accent-gold` | Show XP values in red/green unless it is an error/success state |
| Use 3 px left border + background wash for active list items | Use underline or bold alone for selection |

---

*End of design specification — v1.0 — Light Theme only*
