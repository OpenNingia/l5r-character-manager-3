# Datapack Format

> **Audience.** Implementers of external tooling — in particular the **Android companion app** — that must *read* L5RCM datapacks natively (without running the Python `l5rdal` data-access layer).
>
> **Why a companion needs this.** The `.l5r` save file stores most character state by **reference** (school ids, skill ids, technique coordinates, spell ids…) — see [`FILE_FORMAT_L5R.md`](FILE_FORMAT_L5R.md). To turn those references into names, descriptions, traits, techniques, ring bonuses, etc., a reader must load the same datapacks the desktop app used (listed in the save's `pack_refs`).
>
> **Source of truth.** `l5rdal/` (the `l5rcm-data-access` package): `dataimport.py`, `xmlutils.py`, and the per-entity modules (`clan.py`, `family.py`, `school.py`, `skill.py`, `spell.py`, `powers.py`, `perk.py`, `weapon.py`, `modifier.py`, `requirements.py`, `generic.py`). If this doc and the code disagree, the code wins — please update this doc.

---

## 1. On-disk layout

A **datapack is a directory**, not an archive. (Packs are *distributed* as archives and imported via *Gear menu → Import datapack…*, but on disk at load time they are plain folders.)

Packs live under the user's config directory:

- **Windows:** `%APPDATA%\openningia\l5rcm\core.data\` and `%APPDATA%\openningia\l5rcm\data\`
- **Linux:** `$XDG_CONFIG_HOME/openningia/l5rcm/core.data` and `.../data`

Layout:

```
<data dir>/
└── <pack_id>/
    ├── manifest                 # JSON (no extension) — REQUIRED, marks a valid pack
    └── <pack_id>/               # nested folder with the same id holds the XML
        ├── clans.xml
        ├── skills.xml
        ├── skill_categories.xml
        ├── spells.xml
        ├── katas.xml
        ├── kihos.xml
        ├── tattoos.xml
        ├── merits.xml
        ├── flaws.xml
        ├── weapons.xml
        ├── armors.xml
        ├── weapon_effects.xml
        ├── rings.xml
        ├── modifiers.xml
        ├── perk_categories.xml
        ├── families/            # one file per clan, e.g. Crane_families.xml
        ├── schools/             # one file per clan, e.g. Crane_schools.xml
        └── ...
```

**The file names and folder split are *not* significant.** The loader scans recursively for `*.xml` and dispatches each element by its **tag name** (§2), so any entity may live in any file. Discovery rule: a subdirectory is a pack **iff it contains a `manifest` file**.

### 1.1 `manifest` (JSON)

```json
{
  "id": "core",
  "display_name": "Core book",
  "language": "en_US",
  "authors": ["Author Name"],
  "version": "5.1",
  "update-uri": "",
  "download-uri": "",
  "min-cm-version": "3.9.5"
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | ✅ | Unique pack id. Matches `pack_refs[].id` in the save file. |
| `display_name` | string | | Human-readable pack name. |
| `language` | string | | Locale, e.g. `en_US`. |
| `authors` | string[] | | Authors. |
| `version` | string | | Pack version (matches `pack_refs[].version`). |
| `update-uri` / `download-uri` | string | | Update/download URLs. |
| `min-cm-version` | string | | Minimum L5RCM version required. |

Packs the user has blacklisted are marked inactive and skipped.

---

## 2. XML model

Every XML file has root `<L5RCM>`. Its direct children are entity elements, dispatched by **tag name** to a parser. A reader should iterate all `*.xml` in a pack, and for each child of `<L5RCM>` switch on the tag.

| Tag | Entity | Section |
|---|---|---|
| `<Clan>` | Clan | [2.1](#21-clan) |
| `<Family>` | Family | [2.2](#22-family) |
| `<School>` | School | [2.3](#23-school) |
| `<SkillDef>` | Skill | [2.4](#24-skill-skilldef) |
| `<SkillCateg>` | Skill category | [2.5](#25-id--name-entries) |
| `<SpellDef>` | Spell | [2.6](#26-spell-spelldef) |
| `<KataDef>` | Kata | [2.7](#27-kata-katadef--kiho-kihodef) |
| `<KihoDef>` | Kiho | [2.7](#27-kata-katadef--kiho-kihodef) |
| `<Merit>` / `<Flaw>` | Perk | [2.8](#28-merit--flaw-perk) |
| `<PerkCateg>` | Perk category | [2.5](#25-id--name-entries) |
| `<Weapon>` | Weapon | [2.9](#29-weapon--armor--weapon-effect) |
| `<Armor>` | Armor | [2.9](#29-weapon--armor--weapon-effect) |
| `<EffectDef>` | Weapon/armor effect | [2.9](#29-weapon--armor--weapon-effect) |
| `<RingDef>` / `<TraitDef>` | Ring / trait name | [2.5](#25-id--name-entries) |
| `<ModifierDef>` | Declarative stat modifier | [2.10](#210-modifierdef-declarative-stat-effects) |

**Common conventions** (`xmlutils.py`): attributes are read as string/int/bool; an optional `page` attribute on most entities supplies a book-page reference. A `<Tags>` container holds zero or more `<Tag>text</Tag>` children. Missing optional attributes fall back to documented defaults.

> **Companion priority.** A play-at-the-table companion most needs: **Skill** (name, trait, type), **School** (trait, techniques, honor, granted skills), **Spell**, **Kata/Kiho**, **Merit/Flaw** (name + descriptions), **Weapon/Armor/EffectDef** (combat stats), and the **Ring/Trait** display names. `ModifierDef` matters only if the companion reproduces derived combat math (armor TN, attack rolls); it can be deferred.

### 2.1 Clan

`<Clan>` — attributes only.

| Attribute | Type | Field | Notes |
|---|---|---|---|
| `id` | string | `id` | Unique. Referenced by `clanid` elsewhere and by `clan` in the save. |
| `name` | string | `name` | |
| `page` | string | `book_page` | optional |

```xml
<Clan name="Crane" id="crane" page="100"/>
```

### 2.2 Family

`<Family>` + one `<Trait>` child.

| Attribute / child | Type | Field | Notes |
|---|---|---|---|
| `@id` | string | `id` | matches save `family` |
| `@name` | string | `name` | |
| `@clanid` | string | `clanid` | → `<Clan id>` |
| `@page` | string | `book_page` | optional |
| `<Trait>` | text | `trait` | the +1 trait this family grants (trait id) |

```xml
<Family name="Doji" id="crane_doji" clanid="crane" page="101">
  <Trait>awareness</Trait>
</Family>
```

> The family `<Trait>` is the family's +1 trait bonus — needed to derive current trait/ring ranks (see save spec §4.2).

### 2.3 School

`<School>` is the richest entity. Attributes:

| Attribute | Type | Field | Notes |
|---|---|---|---|
| `id` | string | `id` | matches the `school` field of `rank` advancements |
| `name` | string | `name` | |
| `clanid` | string | `clanid` | → `<Clan id>` |
| `page` | string | `book_page` | optional |

Children:

| Tag | Cardinality | Field | Notes |
|---|---|---|---|
| `<Trait>` | 1 | `trait` | school's +1 trait (trait id) |
| `<Honor>` | 1 | `honor` | starting honor (float) |
| `<Tags>`/`<Tag>` | 1 | `tags[]` | school tags (e.g. `bushi`, `crane_bushi`) — used by requirements |
| `<Affinity>` | 0–1 | `affinity` | spell element affinity (shugenja) |
| `<Deficiency>` | 0–1 | `deficiency` | spell element deficiency |
| `<Skills>` | 1 | `skills[]`, `skills_pc[]` | granted + player-choice skills (below) |
| `<Spells>` | 1 | `spells[]`, `spells_pc[]` | granted + player-choice spells (below) |
| `<Techs>` | 1 | `techs[]` | **techniques per school rank** (below) |
| `<Outfit>` | 0–1 | `outfit[]`, `money[]` | starting gear + money |
| `<Requirements>` | 0–1 | `require[]` | entry requirements ([2.11](#211-requirements)) |
| `<Kihos>` / `<Tattoos>` / `<Perks>` | 0–1 | resp. | granted powers/perks |

**`<Skills>`** — `<Skill id rank emphases?>` for fixed grants; `<PlayerChoose rank>` with `<Wildcard>tag</Wildcard>` children for "choose N skills from {tags}".

```xml
<Skills>
  <Skill id="kenjutsu" rank="1"/>
  <Skill id="iaijutsu" rank="1" emphases="Focus"/>
  <PlayerChoose rank="1"><Wildcard>bugei</Wildcard></PlayerChoose>
</Skills>
```

**`<Spells>`** — `<Spell id>` for fixed grants; `<PlayerChoose count element?>` for "choose N spells of element".

**`<Techs>`** — the technique granted at each school rank. **This is how a save's `rank.school` + `rank.school_rank` resolve to a technique** (save spec §4.4).

```xml
<Techs>
  <Tech id="crane_way" name="The Way Of The Crane" rank="1">
    <Description>…</Description>
  </Tech>
</Techs>
```

| `<Tech>` attr/child | Type | Field |
|---|---|---|
| `@id` | string | `id` (unique within the school) |
| `@name` | string | `name` |
| `@rank` | int | `rank` (school rank, 1-based) |
| `<Description>` | text | description |

**`<Outfit koku bu zeni>`** with `<Item>text</Item>` children → `money = [koku, bu, zeni]`, `outfit = [item, …]`.

### 2.4 Skill (`<SkillDef>`)

| Attribute | Type | Field | Notes |
|---|---|---|---|
| `id` | string | `id` | matches skill ids in save (`SkillAdv.skill`, `rank.skills[]`) |
| `name` | string | `name` | |
| `trait` | string | `trait` | the trait the skill rolls with (trait id) |
| `type` | string | `type` | category id (→ `<SkillCateg>`), e.g. `bugei` |
| `page` | string | `book_page` | optional |

Children: `<Tags>/<Tag>` (`tags[]`); `<Description>` (`desc`); `<MasteryAbilities>` with `<MasteryAbility rank rule?>text</MasteryAbility>` (mastery-ability text per skill rank).

```xml
<SkillDef trait="strength" type="bugei" id="athletics" name="Athletics" page="139">
  <MasteryAbilities>
    <MasteryAbility rank="3">No impediments on Moderate Terrain</MasteryAbility>
    <MasteryAbility rank="5">No impediments on any terrain</MasteryAbility>
  </MasteryAbilities>
  <Description>…</Description>
</SkillDef>
```

### 2.5 `id → name` entries

`<SkillCateg>`, `<PerkCateg>`, `<RingDef>`, `<TraitDef>` share the same trivial shape: an `id` attribute and the display name as **element text**.

```xml
<SkillCateg id="bugei">Bugei (Martial)</SkillCateg>
<RingDef id="earth">Earth</RingDef>
<TraitDef id="stamina">Stamina</TraitDef>
<PerkCateg id="material">Material</PerkCateg>
```

> These give the companion the human-readable names for the trait/ring ids used throughout the save (trait index → `TraitDef` name; ring id → `RingDef` name).

### 2.6 Spell (`<SpellDef>`)

| Attribute | Type | Field |
|---|---|---|
| `id` | string | `id` (matches `SpellAdv`/`MemoSpellAdv.spell`, `rank.spells[]`) |
| `name` | string | `name` |
| `element` | string | `element` (`air`/`earth`/`fire`/`water`/`void`) |
| `mastery` | int | `mastery` (also the XP cost of memorizing) |
| `area` | string | `area` |
| `range` | string | `range` |
| `duration` | string | `duration` |
| `page` | string | `book_page` (optional) |

Children: `<Tags>` with `<Tag school?>text</Tag>` (each tag may carry an optional `school` attribute → `SpellTag(name, school)`); `<Raises>`/`<Raise>` (`raises[]`); `<MultiElement>`/`<Element>` (`elements[]`); `<Requirements>`; `<Description>` (`desc`).

### 2.7 Kata (`<KataDef>`) & Kiho (`<KihoDef>`)

Shared attributes: `id`, `name`, `element`, `mastery` (int), `page` (optional). Kiho adds `type` (`internal`/`mystical`/`martial`/`kharmic`). Children: `<Description>` (required), `<Requirements>` (0–1), `<Tags>` (0–1).

```xml
<KihoDef mastery="3" element="air" type="internal" id="air_fist" name="Air Fist" page="262">
  <Description>…</Description>
</KihoDef>
```

> Match these ids against `KataAdv.kata` / `KihoAdv.kiho` in the save. Tattoos use `<Tattoos>` within schools and a parallel definition shape.

### 2.8 Merit & Flaw (`<Merit>` / `<Flaw>` → `Perk`)

Both tags build the same `Perk` class (the tag distinguishes merit vs flaw).

| Attribute | Type | Field |
|---|---|---|
| `id` | string | `id` (matches `PerkAdv.perk`) |
| `name` | string | `name` |
| `type` | string | `type` (category → `<PerkCateg>`: material/mental/physical/social/spiritual/varies) |
| `rule` | string | `rule` (optional rule id) |
| `page` | string | `book_page` (optional) |

Children: `<Description>` (required); one or more `<Rank id value>` giving the point cost per rank, each optionally containing `<Exception tag value/>` for clan/condition-specific cost overrides.

```xml
<Merit type="material" id="wealthy" name="Wealthy" page="155">
  <Rank id="1" value="1"><Exception tag="crane" value="0"/></Rank>
  <Rank id="2" value="2"><Exception tag="crane" value="1"/></Rank>
  <Description>…</Description>
</Merit>
```

### 2.9 Weapon, Armor & Weapon effect

**`<Weapon>`**

| Attribute | Type | Field | Notes |
|---|---|---|---|
| `name` | string | `name` | |
| `skill` | string | `skill` | skill id used to attack (optional) |
| `dr` | string | `dr` | damage roll, e.g. `3k2` |
| `dr_alt` | string | `dr2` | alternate damage roll (optional) |
| `range` | string | `range` | optional |
| `cost` | string | `cost` | free-text, e.g. `5k` (optional) |
| `strength` | int | `strength` | optional |
| `min_strength` | int | `min_strength` | optional |

Children: `<Tags>/<Tag>` (`tags[]`, e.g. `medium`, `melee`, `samurai`); `<Effect id>` → `effectid` referencing an `<EffectDef>`.

**`<Armor>`**: `name`, `tn` (int), `rd` (int), `cost` (string); optional `<Effect id>`.

**`<EffectDef id>text</EffectDef>**: an id + the effect description text. Weapons/armor reference these via `<Effect id>`.

```xml
<Weapon skill="kenjutsu" dr="3k2" name="Katana">
  <Tags><Tag>medium</Tag><Tag>melee</Tag><Tag>samurai</Tag></Tags>
  <Effect id="void_rise_dr_rule"/>
</Weapon>
<EffectDef id="void_rise_dr_rule">A character may spend one Void Point to increase…</EffectDef>
```

### 2.10 `<ModifierDef>` (declarative stat effects)

Declarative, datapack-driven stat modifiers (armor TN, attack/damage rolls, initiative, trait substitutions…) attached to a technique/kata/kiho/etc. **Optional for a companion** unless it reproduces derived combat math.

| Attribute | Type | Field | Notes |
|---|---|---|---|
| `target` | string | `target` | id of the entity this modifies (a tech/kata/kiho/… id) |
| `kind` | string | `kind` | `tech`/`kata`/`kiho`/`tattoo`/`merit`/`flaw`/`ancestor`/`path`/`mastery`/`weapon_effect`/`armor` |
| `rank` | int | `rank` | optional (mastery modifiers) |
| `partial` | bool | `partial` | optional flag: record has unmodeled clauses |

Children: `<Mod>` (a modifier entry), `<OneOf>` (exclusive group of `<Mod>`), `<Substitute>` (use trait X instead of Y for some stat), `<Param>` (named parameter).

`<Mod>` key attributes: `affects` (target statistic, e.g. `armor_tn`, `attack_roll`), `value` (expression, e.g. `rings.air`, `insight_rank + rings.air`), `roll`/`keep`/`bonus`, `op` (`add`/`set`/`min`/`max`, default `add`), `detail` (`skill:`/`weapon:`/`tag:`/`ring:`/`trait:` qualifier), `requires` (predicate), `when` (combat-state flag, default `auto`), `reason` (display label).

```xml
<ModifierDef target="soul_of_the_four_winds" kind="kiho">
  <Mod affects="armor_tn" value="insight_rank + rings.air"/>
</ModifierDef>
<ModifierDef target="balance_the_elements_style" kind="kata">
  <Substitute affects="initiative" use="void" instead_of="reflexes"/>
</ModifierDef>
```

> See also the in-progress declarative-modifier schema work in the `l5rcm-data-packs` repo (`MODIFIERS_SCHEMA.md`).

### 2.11 Requirements

A `<Requirements>` container appears inside School, Spell, Kata, Kiho, etc. It holds `<Requirement>` entries and `<RequirementOption>` groups (alternatives).

**`<Requirement>`**: `field` (target — a skill/ring/trait/school id, or special: `*any`, `*tag:<tag>`, `honor`, `status`, `glory`), `type` (`skill`/`ring`/`trait`/`tag`/`rule`/`school`/`rank`), `min` (int, default `-1`), `max` (int, default `999`), `trg` (optional, e.g. an emphasis). Element text is a human label.

**`<RequirementOption text?>`**: container of alternative `<Requirement>`s (satisfied if any one holds).

```xml
<Requirements>
  <Requirement field="crane_kakita_bushi_school" type="tag">Kakita Bushi School</Requirement>
  <RequirementOption text="OR">
    <Requirement field="*any" type="ring" min="2"/>
    <Requirement field="honor" type="school" min="3"/>
  </RequirementOption>
</Requirements>
```

---

## 3. Cross-reference summary

| Reference | From | To |
|---|---|---|
| `clanid` | Family, School | `<Clan id>` |
| `school` (save `rank` adv) | `.l5r` | `<School id>` |
| `school_rank` + school | `.l5r` | `<School><Techs><Tech rank>` |
| `<Skill id>` (in School) | School | `<SkillDef id>` |
| `<Spell id>` (in School) | School | `<SpellDef id>` |
| `<Effect id>` | Weapon, Armor | `<EffectDef id>` |
| `target` | `<ModifierDef>` | any entity `id` |
| skill `type` | `<SkillDef>` | `<SkillCateg id>` |
| perk `type` | `<Merit>`/`<Flaw>` | `<PerkCateg id>` |
| trait/ring ids | everywhere | `<TraitDef id>` / `<RingDef id>` |

---

## 4. Recommended load procedure for a native reader

1. From the save's `pack_refs`, determine which pack ids/versions are required; locate those folders (each has a `manifest`).
2. Parse `manifest` (JSON) for id/version/language.
3. Recursively collect every `*.xml` under the pack; for each, require root `<L5RCM>` and iterate children, dispatching by tag (§2) into typed collections keyed by `id`.
4. De-duplicate by `id` (the desktop loader dedups by entity equality and tags each record with its `source_pack`).
5. Resolve save references against these collections to display names, techniques (school+rank), spell/skill/perk details, and combat stats.
