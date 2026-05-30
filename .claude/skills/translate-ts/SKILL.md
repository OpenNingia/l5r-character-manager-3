---
name: translate-ts
description: >-
  Translate the untranslated entries in the L5RCM Qt Linguist .ts files (the QML
  surface l5r/i18n/qml/*.ts and/or the Python surface l5r/i18n/*.ts), preserving
  placeholders, markup and mnemonics, staying consistent with the established L5R
  glossary, then compile to .qm. Use when asked to translate the UI, fill/complete
  a language, localise newly-extracted strings, or finish the unfinished entries
  of a .ts. Pairs with tools/scripts/update_translations.py (extract/compile) and
  tools/scripts/apply_ts_translations.py (dump/apply).
---

# Translate the L5RCM .ts files

This skill fills the **unfinished** translation entries of the project's Qt
Linguist `.ts` files and compiles them. The translation itself is your job (you
read each English source and write the target-language text); the tooling makes
it safe and reviewable.

## The shape of the i18n setup (read once)

Two independent translation surfaces, each with its own `.ts`/`.qm` (see the
`qml-i18n-pipeline` memory and `tools/scripts/update_translations.py`):

| Surface | sources | `.ts` | shipped `.qm` |
|---|---|---|---|
| **qml** | `qsTr()` in `l5r/qmlui/qml/**` | `l5r/i18n/qml/<locale>.ts` | `l5r/share/l5rcm/i18n/qml_<locale>.qm` |
| **python** | `tr()`/`api.tr()` in `l5r/**` | `l5r/i18n/<locale>.ts` | `l5r/share/l5rcm/i18n/<locale>.qm` |

Locales: `en es_ES fr fr_FR it_IT pt_BR ru_RU`. **`en` is the source language —
skip it** (qsTr falls back to English anyway). `fr` and `fr_FR` are duplicates;
translate one and copy, or translate both identically.

If new strings may have been added to the code, run the extractor first so the
`.ts` are current (see that script's help for tool requirements):

```bash
python tools/scripts/update_translations.py extract --surface qml   # or python / both
```

## Workflow per locale

Work **one `.ts` file at a time**. For each:

1. **Dump** the untranslated sources to a JSON template:
   ```bash
   python tools/scripts/apply_ts_translations.py dump l5r/i18n/qml/it_IT.ts -o /tmp/it.json
   ```
   The JSON is `{ "<english source>": "" }`, deduped, in document order. Keys are
   **literal** text (XML entities already decoded: you'll see `<p>` and `"`, not
   `&lt;p&gt;` / `&quot;`).

2. **Translate** — fill every value you can (this is the real work; follow the
   rules and glossary below). Leave a value as `""` only when the string must NOT
   be translated (see "Leave untranslated").

3. **Apply** the JSON back into the `.ts`:
   ```bash
   python tools/scripts/apply_ts_translations.py apply l5r/i18n/it_IT.ts /tmp/it.json
   ```

4. After all locales for a surface are done, **compile**:
   ```bash
   python tools/scripts/update_translations.py compile --surface qml
   ```

5. **Verify**: `apply` prints `filled / still untranslated / skipped`, and
   `compile`'s lrelease prints `Generated N (finished + unfinished)`. The `.ts`
   stays valid XML. Spot-check a few entries.

### What `apply` guarantees (so you can trust it)

- Touches **only** unfinished/empty entries; never overwrites a finished one
  (re-running is idempotent — safe to iterate in batches).
- Untouched `<message>` blocks stay **byte-identical** (clean git diffs); LF
  preserved on every platform.
- **Placeholder guard**: if a translation's `%1`/`%2`/… set differs from its
  source, that entry is skipped and reported — never written broken.
- Plural/numerus messages are skipped (can't be one string).

## Hard rules — correctness gate

These are about *not breaking the string*, independent of language quality:

- **Placeholders** `%1`, `%2`, `%L1`, … must appear in the translation with the
  exact same set (order may change to fit grammar). `apply` enforces this, but
  translate with them in place: `"Rank %1"` → `"Rango %1"`, never `"Rango"`.
- **Markup & URLs**: translate only the visible words. Keep every tag, attribute
  and URL verbatim — `<a href="%3">here</a>` → `<a href="%3">qui</a>`. Don't add
  or drop tags. (Write literal `<`/`"` in the JSON; `apply` re-escapes.)
- **`&` mnemonics**: keep exactly one `&` and place it before a letter that
  exists in your translation — `"&File"` → `"&File"`, `"&New"` → `"&Nuovo"`.
- **Special characters**: leave `©`, `–`, `…`, em-dashes and CJK glyphs as they
  are; translate the surrounding words only.
- **Whitespace**: preserve leading/trailing spaces and newlines in a source.

### Leave untranslated (value stays `""`)

- Pure-symbol / glyph strings: kanji icons (`技`, `侍`), `＋`, arrows, single
  punctuation. These are visual, not language.
- Proper nouns / brand names that aren't localised (`L5RCM`, `Fantasy Flight
  Games`, `GitHub`, person names).
- Anything you are not confident about — better an English fallback than a wrong
  translation. Note these back to the user.

## Terminology — be consistent and canonical

L5R has established translations. **Before inventing a term, look it up** in the
legacy per-locale `.ts`, which carries the historical glossary (including
`type="vanished"` entries — they still hold the canonical word):

```bash
grep -A1 '<source>Void</source>' l5r/i18n/it_IT.ts        # -> Vuoto
grep -A1 '<source>Insight</source>' l5r/i18n/it_IT.ts     # -> Introspezione
```

Use the **same** target term everywhere the same English term appears. Default
Italian glossary (override only if the legacy `.ts` says otherwise):

| EN | IT | EN | IT |
|----|----|----|----|
| Ring | Anello | Skill | Abilità |
| Earth / Air / Water / Fire / Void | Terra / Aria / Acqua / Fuoco / Vuoto | Emphasis | Enfasi |
| Trait | Tratto | Mastery | Maestria |
| Insight | Introspezione | School | Scuola |
| (Insight) Rank | Rango (di Introspezione) | Family | Famiglia |
| Honor / Glory / Status | Onore / Gloria | Clan | Clan |
| Taint | Corruzione | Spell | Incantesimo |
| Void Point | Punto del Vuoto | Technique | Tecnica |
| Wound | Ferita | Tattoo | Tatuaggio |
| Weapon | Arma | Kata / Kiho | Kata / Kiho |
| Melee / Ranged | Mischia / A distanza | Armor | Armatura |
| Advantage / Disadvantage | Vantaggio / Svantaggio | Experience (XP) | Esperienza (PE) |
| Buy | Compra | Add / Remove | Aggiungi / Rimuovi |
| Save / Open / Close | Salva / Apri / Chiudi | Cancel / OK | Annulla / OK |

For other languages, mine that locale's legacy `.ts` the same way; prefer its
established terms over a fresh guess.

## Scope & batching

- Confirm with the user **which locales** to do. `it_IT` is highest value (the
  maintainer can verify it). Western-European (`fr`, `fr_FR`, `es_ES`, `pt_BR`)
  are doable; flag `ru_RU` for native review.
- ~450 unique strings per file — translate in batches (e.g. context by context),
  applying each batch. `apply` is idempotent, so partial progress is safe.
- When done, report what you left untranslated and why, and remind that the
  `.qm` (and the `.ts`) are new/changed files to commit.
