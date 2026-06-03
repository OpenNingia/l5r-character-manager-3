---
name: port-tab-to-qml
description: >-
  Port a legacy QWidget tab (l5r/ui/tabs/*.py) to the new QML sheet UI
  (l5r/qmlui/qml/sections/), end-to-end and strictly compliant with the UI
  design system. Use when asked to port / implement a QML section (the
  remaining ones are techniques, spells, kata, kiho, weapons, misc, settings),
  to wire a new pcProxy/appCtrl surface for the QML UI, or to author any new
  QML section or dialog for the L5R character manager. Every artifact MUST
  derive its colours, fonts, spacing, sizing and motion from
  docs/L5R_UI_Design_System.md and the `Theme` singleton.
---

# Port a tab to the QML sheet UI

This skill drives the full port of one legacy QWidget tab to the in-progress
QML sheet, **with design-system compliance as a hard gate, not an afterthought.**
The QML UI lives in `l5r/qmlui/`; the legacy tabs it replaces live in
`l5r/ui/tabs/`.

## 0. The design system is the spec — read it first

[`docs/L5R_UI_Design_System.md`](../../../docs/L5R_UI_Design_System.md) is the
**authoritative** style reference (CLAUDE.md elevates it to a hard rule). Before
writing a single line of QML:

- **Skim the relevant component specs** (§6), the type scale (§3), the spacing
  grid (§4) and the kanji map (§7) for the section you are porting.
- **Every colour, spacing, font face/size/weight and motion value comes from
  the `Theme` singleton** (`l5r/qmlui/qml/Theme/Theme.qml`), imported everywhere
  via `import Theme 1.0`. **Never hard-code a hex colour or a pixel value
  inline.** If the spec needs a value `Theme` does not yet expose, add the token
  to `Theme.qml` first (reconciling it against the spec — when the spec and
  `Theme.qml` disagree, treat it as a gap to fix, not a free choice), then
  consume the token.
- **Clan accents** (§5) come from the writable `ClanTheme` singleton
  (`l5r/qmlui/qml/ClanTheme/ClanTheme.qml`) via `import ClanTheme 1.0` — never
  duplicate accent hexes per component.
- **Reuse the existing `L5R*` primitives** (see the mapping table in §3 below)
  rather than re-styling raw Qt controls. They already encode the spec.

If you only remember one thing: **derive from tokens + primitives, hard-code
nothing.**

## 1. The five steps

```
  ① study legacy tab  →  ② proxy plumbing  →  ③ author section QML
        →  ④ wire SectionBlock dispatch  →  ⑤ smoke-test + design review
```

### ① Study the legacy tab

Read `l5r/ui/tabs/<tab>.py` (and its `Sink`/mixin) to learn **what data it
shows and what mutations it offers** — not how it lays them out (the QML
re-imagines the layout per the design system). Trace each piece of data and each
action back to the `l5r.api.*` functions that produce/consume it
(`api.character.*`, `api.data.*`, `api.rules.*`). Those API functions are your
real contract; the QML talks to them through proxies, never to the widget.

Note the section's identity for later steps — `tabId`, title and kanji come from
`_TAB_DEFS` in `l5r/qmlui/proxies/app_controller.py` and the §7 kanji map:

| tabId | Title | Kanji | Legacy source |
|---|---|---|---|
| `techniques` | Techniques | 流 | `techniques.py` |
| `spells` | Spells | 呪 | `powers.py` (split) |
| `kata` | Kata | 型 | `powers.py` (split) |
| `kiho` | Kiho | 気 | `powers.py` (split) |
| `weapons` | Weapons | 刀 | `weapons.py` |
| `misc` | Miscellanea | 雑 | `modifiers.py` + `equipment.py` (merged) |
| `settings` | Settings | 設 | `settings_tab.py` |

> The QML taxonomy is **not** 1:1 with the legacy tabs: `powers` was split into
> `spells`/`kata`/`kiho`, and `modifiers`+`equipment` were merged into `misc`.

### ② Proxy plumbing

Two proxies bridge Python → QML; both are bound as context properties in
`l5r/qmlui/app.py` (`pcProxy`, `appCtrl`).

**Reads → a `PcProxy` slice.** Add a per-area mixin in `l5r/qmlui/proxies/pc/`
(model it on `pc/skills.py`) and compose it into `PcProxy`
(`l5r/qmlui/proxies/pc_proxy.py`): add to the base-class list **and** call its
`_wire_<area>(bus)` in `__init__`. The mixin:
- exposes data as `@Property("QVariantList"/"QVariantMap", notify=<area>Changed)`
  getters that read **live** from `api.character.model()` — hold no model
  reference (model swaps must not strand the proxy);
- bundles each row into a plain dict whose keys are exactly what the QML row
  template consumes (document the row shape in the QML header comment, as
  `SkillsSection.qml` does);
- subscribes to `api.signals.bus()` and re-emits a coarse `<area>Changed` on
  `character_refreshed` / `model_replaced`.

**Actions → `@Slot`s on `AppController`** (`l5r/qmlui/proxies/app_controller.py`,
model on `buySkillRank` / `setName`). Each slot delegates to the matching
`api.character.*` setter — which owns its own `set_dirty_flag(True)` per
CLAUDE.md. Do **not** mutate `pc` attributes directly from the proxy. Read-style
helpers the dialog needs (`availableSkillsToBuy()`) can also be slots/properties
on `AppController`.

### ③ Author the section QML — design-system compliant

Create `l5r/qmlui/qml/sections/<Section>Section.qml`. Model it on an existing
section (`SkillsSection.qml` is the richest; `PerksSection.qml` shows cards).
Structural rules:

- Imports: `QtQuick`, `QtQuick.Controls`, `QtQuick.Layouts`, then
  `import "../widgets" as Widgets`, `import "../dialogs" as Dialogs`,
  `import Theme 1.0`, and `import ClanTheme 1.0` if you use clan accent.
- Root is a `ColumnLayout` (the `SectionBlock` `Loader` sizes to its implicit
  height — keep it accurate so the TOC scroll math stays correct).
- Read data from `pcProxy.<area>`; guard for null
  (`pcProxy ? pcProxy.x : []`) — the preview tool binds null proxies.
- Header the file with a comment block documenting the expected row shape and
  the `appCtrl`/`pcProxy` members it depends on (consistency with the other
  sections).
- Player-facing copy stays plain — no mechanics jargon
  (queues/stacks/cascades); put rationale in code comments, wrap user strings in
  `qsTr(...)`.

**Reuse these primitives — each already implements its spec section. Do not
re-skin raw Qt controls.**

| Need | Use | Spec § |
|---|---|---|
| Primary / secondary button | `Widgets.L5RButton` | §6.2 / §6.3 |
| Category dropdown | `Widgets.L5RComboBox` | §6.7 |
| Search field | `Widgets.L5RSearchField` | §6.6 |
| Rank 1–N selector | `Widgets.L5RRankSelector` | §6.4 |
| Stat +/- stepper | `Widgets.RankStepper` | §6.11 buttons |
| Ring / attribute card | `Widgets.RingCard` | §6.11 |
| Honor / glory dots | `Widgets.PointTrack` | §6.12 |
| Wounds ladder | `Widgets.WoundsBlock` | — |
| Structural divider | `Widgets.OrnateDivider` | §6.13 |
| Panel surface (palette-safe) | `Widgets.SheetPanel` | §12.3 |
| Modal dialog shell | `Widgets.L5RDialog` | §4.3, §6.14, §6.15 |
| Paper grain | `Widgets.RicePaperOverlay` | §8.1 |

**Dialogs** are authored fresh in QML — never wrap or re-show a legacy
`l5r/dialogs/*.py` widget. Build on `Widgets.L5RDialog`, parent to
`Overlay.overlay`, give it a kakemono header (§6.15) with the section/action
kanji tile, parchment background + `RicePaperOverlay`, and footer buttons
(§6.14) — see `BuySkillDialog.qml` / `InscribePerkDialog.qml`.

### ④ Wire the SectionBlock dispatch

In `l5r/qmlui/qml/SectionBlock.qml`, add a `case "<tabId>":` to the `switch` that
returns a new `Component { Sections.<Section>Section {} }`. Without this the
section renders the neutral "content coming soon" placeholder. The `tabId` must
match the entry in `_TAB_DEFS`.

### ⑤ Smoke-test offscreen, then review against the spec

Render headless with the committed preview tool — **no display, datapacks or
full bootstrap needed**:

```powershell
# Windows (this machine)
tools\qml_preview.ps1 --qml <host>.qml --out section.png
tools\qml_preview.ps1 --dialog <YourDialog> --call 'present("...")' --size 980x720 --out dlg.png
```
```bash
# Linux / WSL: the .py sets the same QT_* env vars itself
python tools/qml_preview.py --dialog <YourDialog> --call open --out dlg.png
```

`tools/qml_preview.py` binds **null** `appCtrl`/`pcProxy` (chrome + layout
render; data is empty). For a data-bearing render, point `--qml` at a small host
`ApplicationWindow` that stubs the proxies as JS objects and instantiates your
section. Open the PNG and run the **design-review checklist** below.

## 2. Design-review checklist (gate before you call it done)

- [ ] **Zero hard-coded hex or px** — every colour/spacing/size/weight is a
      `Theme.*` token (or `ClanTheme.*` for accent). New tokens were added to
      `Theme.qml` to match the spec, not inlined.
- [ ] **Fonts:** Cinzel (`Theme.fontDisplay`) for titles/labels/buttons, **never
      below `Theme.wSemiBold` (600)**, ALL-CAPS + letter-spacing on headings;
      IM Fell English (`Theme.fontBody`) for body/captions, **Regular only — no
      `font.bold: true`** (emphasise with gold or italic); EB Garamond
      (`Theme.fontStat`) for numerals with size-scaled weight (§3.4). Always set
      `font.weight` from a `Theme` token; never `font.bold`. `font.family` is a
      single name — no comma fallback chains.
- [ ] **No pure `#000`/`#FFF`**; dividers use `Theme.divider`/parchment, never
      solid black (§8.3). Ring-card text stays white (§6.11).
- [ ] **Texture:** parchment surfaces carry `RicePaperOverlay`; the sheet reads
      as one continuous page (window-level), dialogs get their own (§8.1).
- [ ] **Palette-propagation trap:** any `Label`/`TextField` whose visual parent
      chain is only `Rectangle`s sets `color: Theme.ink` explicitly (and
      `placeholderTextColor` on inputs). `Rectangle` does **not** propagate
      `palette`, so on a dark OS theme uncoloured text vanishes against the
      cream. Prefer wrapping content in `SheetPanel`/`Pane` (a Control that sets
      palette), or set the colour explicitly. **Always smoke-test against a dark
      QPalette to catch this.**
- [ ] **Clan accent** comes from `ClanTheme`, never a per-component hex.
- [ ] Active list items use the 3px left border + wash (§6.10), not bold/underline.
- [ ] Motion durations/easing match §9 (subtle, no bounces).
- [ ] Section kanji watermark matches §7; kanji is decoration only, never the
      primary label for an action.

## 3. Invariants (from CLAUDE.md — do not break)

- Qt imported through **`qtpy`** only, never `PyQt6` directly.
- API layer reads context implicitly via `get_context()`; **don't thread `ctx`**
  through call chains.
- **Setters own the dirty flag** — proxy slots delegate to the
  `api.character.*` setter that calls `set_dirty_flag(True)`; never poke
  `self.pc.<attr>`.
- The QML UI forces the **Fusion** Quick Controls style (set in `app.py`); the
  preview tool sets `QT_QUICK_CONTROLS_STYLE=Fusion` too. Customised
  `background:`/`contentItem:` are silently ignored under the native Windows
  style.
- Run the existing tests after proxy changes: `python -m unittest discover -s l5r`
  (`QT_QPA_PLATFORM=offscreen` on headless).

## 4. Reference files

- Spec: `docs/L5R_UI_Design_System.md`
- Tokens: `l5r/qmlui/qml/Theme/Theme.qml` · accent: `l5r/qmlui/qml/ClanTheme/ClanTheme.qml`
- Dispatch: `l5r/qmlui/qml/SectionBlock.qml` · sheet host: `l5r/qmlui/qml/MainSheet.qml`
- Model section: `l5r/qmlui/qml/sections/SkillsSection.qml`
- Model proxy slice: `l5r/qmlui/proxies/pc/skills.py` · composed in `pc_proxy.py`
- Actions + tab defs: `l5r/qmlui/proxies/app_controller.py`
- Bootstrap / context properties / fonts: `l5r/qmlui/app.py`
- Preview tool: `tools/qml_preview.ps1` (Windows) / `tools/qml_preview.py`
