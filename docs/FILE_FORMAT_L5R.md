# `.l5r` Save File Format

> **Audience.** Implementers of external tooling — in particular the **Android companion app** — that must *read* L5RCM character files without running the Python codebase.
>
> **Scope.** This documents the on-disk format and, crucially, **how to derive the values a reader cares about** (skill ranks, traits/rings, merits/flaws, techniques, spells) from the data that is actually stored. The companion app does **not** create advancements, but it **must read `advans[]`** because that array is the source of truth for most derived character state.
>
> **Source of truth.** `l5r/models/chmodel.py` (`AdvancedPcModel`, `MyJsonEncoder`, `load_from`, `_load_advancement`), `l5r/models/advances.py`, `l5r/models/advancements/rank.py`, `l5r/models/outfit.py`, `l5r/models/modifiers.py`, and the derivation logic in `l5r/api/character/`. If this document and the code disagree, the code wins — please update this doc.

---

## 1. Encoding

A `.l5r` file is a **UTF-8 JSON document**, pretty-printed with `indent=2`. It is produced by:

```python
json.dump(pc_model, fp, cls=MyJsonEncoder, indent=2)
```

`MyJsonEncoder.default()` is trivial — it returns `obj.__dict__` for any object that has one:

```python
def default(self, obj):
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return json.JSONEncoder.default(self, obj)
```

**Consequences for a reader:**

- The JSON tree is a **direct mirror of the in-memory Python object graph**. Top-level keys are the attributes of `AdvancedPcModel`; nested objects (advancements, armor, weapons, modifiers) are their own `__dict__`s.
- **There is no schema versioning that matters in practice.** The `version` field exists but is effectively always `"0.0"`. Treat all fields as *optional* and supply defaults — old saves omit newer fields, and several fields are legacy/unused (flagged below).
- **Python tuples are serialized as JSON arrays.** `money = (koku, bu, zeni)` becomes `[koku, bu, zeni]`. `ModifierModel.value` and `Rank.money` are the same shape.
- Unknown/extra keys may appear (`properties` is an open key-value map). Ignore what you don't understand; never assume the key set is closed.

---

## 2. Top-level object (`AdvancedPcModel`)

### 2.1 Identity & metadata

| Key | Type | Default | Meaning |
|---|---|---|---|
| `name` | string | `""` | Character display name |
| `uuid` | string \| null | `null` | **Stable character identity** — a random UUID4 string (e.g. `"3f2a…"`), independent of `name` and file path. Assigned when the character is created; **back-filled on demand** for saves that predate this field (notably the first time a companion QR code is generated). Lets the Android companion keep its data overlay aligned with the same character across edits, renames and re-shares. May be `null`/absent in old saves that have never been re-shared or re-saved since the field was introduced — treat absence as "no stable id yet". Once present it is stable across saves. |
| `clan` | string \| null | `null` | Clan id (datapack reference) |
| `family` | string \| null | `null` | Family id (datapack reference) |
| `version` | string | `"0.0"` | Format version (not meaningful — see §1) |
| `unsaved` | bool | `false` | Dirty flag; ignore on read |
| `properties` | object(string→string) | `{}` | Open map of personal info. Canonical keys: `sex`, `age`, `height`, `weight`, `hair`, `eyes`, `father`, `mother`, `brothers`, `sisters`, `marsta`, `spouse`, `childr`. Any custom key may also appear. No schema; treat all values as plain strings. |
| `extra_notes` | string | `""` | Free-form character notes — **rich-text HTML** (Qt rich text), not plain text. |
| `pack_refs` | array(object) | `[]` | Datapacks loaded when the file was saved. Each: `{ "id": str, "name": str, "version": str }`. Use to warn if a required datapack is missing. |

### 2.2 Traits, rings, void — **read the advancements, not these fields**

| Key | Type | Default | Meaning |
|---|---|---|---|
| `starting_traits` | int[8] | `[2,2,2,2,2,2,2,2]` | **Base** trait ranks at creation, indexed by trait id (see §2.7). |
| `starting_void` | int | `2` | **Base** void rank at creation. |
| `attribs` | int[8] | `[0,…]` | ⚠️ **Legacy / unused.** Do **not** read for current trait ranks. |
| `void` | int | `0` | ⚠️ **Legacy / unused.** Do **not** read for current void rank. |

> The **current** trait/void/ring ranks are *derived* — see [§4.2](#42-traits-rings-and-void).

### 2.3 Experience & advancement

| Key | Type | Default | Meaning |
|---|---|---|---|
| `advans` | array(Advancement) | `[]` | **The heart of the file.** Ordered advancement history. See [§3](#3-the-advans-array). |
| `exp_limit` | int | `40` | XP budget cap (40 base; flaws raise the *available* total — see [§4.7](#47-experience)). |
| `insight` | int | `0` | ⚠️ Legacy/unused; insight is recomputed at runtime. |
| `insight_calculation` | int | `1` | Insight-rule selector. `1` = default. |

### 2.4 Reputation tracks — **stored as deltas**

| Key | Type | Default | Meaning |
|---|---|---|---|
| `honor` | float | `0.0` | Stored **delta** over the school's starting honor. |
| `glory` | float | `0.0` | Stored **delta** over starting glory (base `1.0`, +fame merit). |
| `status` | float | `0.0` | Stored **delta** over starting status (base `1.0`, `-1.0` if social-disadvantage). |
| `infamy` | float | `0.0` | Stored **delta** over starting infamy (base `0.0`). |
| `taint` | float | `0.0` | Stored **delta** over starting taint (base `0.0`). |

> These are **not** the final displayed values — they are the user-entered adjustment on top of the rules-derived starting value. A companion that doesn't compute the starting baseline can show these as adjustments, or approximate the final value as `starting + delta`.

### 2.5 Health & current play state (the values the companion mutates most)

| Key | Type | Default | Meaning |
|---|---|---|---|
| `wounds` | int | `0` | Current accumulated wounds (player-entered). |
| `void_points` | int | `0` | Current void points spent/remaining (player-entered). |
| `health_multiplier` | int | `2` | Ring-rank multiplier for the wound-rank table (RAW: 2). |
| `health_base_multiplier` | int | `5` | Base multiplier on Earth/Stamina for health (RAW: 5). |

> These four are exactly the kind of state the companion both reads and tracks live at the table. `wounds`/`void_points` are plain counters; the *capacity* (wound levels) is derived — see [§4.6](#46-wounds-and-health).

### 2.6 Equipment & wealth

| Key | Type | Default | Meaning |
|---|---|---|---|
| `armor` | ArmorOutfit \| null | `null` | At most one worn armor. See [§5.1](#51-armoroutfit). |
| `weapons` | array(WeaponOutfit) | `[]` | Carried weapons. See [§5.2](#52-weaponoutfit). |
| `modifiers` | array(ModifierModel) | `[]` | User-defined stat modifiers. See [§5.3](#53-modifiermodel). |
| `money` | int[3] | `[0,0,0]` | `[koku, bu, zeni]` (gold, silver, copper). |
| `outfit` | string[] | `[]` | ⚠️ Legacy/unused. |

### 2.7 Costs & spell config

| Key | Type | Default | Meaning |
|---|---|---|---|
| `attrib_costs` | int[8] | `[4,…]` | XP cost per trait rank, per trait. |
| `void_cost` | int | `6` | XP cost per void rank. |
| `spells_per_rank` | int | `3` | Bonus spells a shugenja gains per insight rank above 1. |

### Trait index ↔ ring mapping

Trait arrays (`starting_traits`, `attribs`, `attrib_costs`) and `AttribAdv.attrib` use this fixed index (from `chmodel.ATTRIBS`):

| Index | Trait | Ring |
|---|---|---|
| 0 | Stamina | **Earth** |
| 1 | Willpower | **Earth** |
| 2 | Reflexes | **Air** |
| 3 | Awareness | **Air** |
| 4 | Strength | **Water** |
| 5 | Perception | **Water** |
| 6 | Agility | **Fire** |
| 7 | Intelligence | **Fire** |

A ring's rank is `min` of its two traits' ranks (e.g. `earth = min(stamina, willpower)`). Void is its own ring (not derived from traits).

---

## 3. The `advans[]` array

Every entry is an object with a **common base** plus type-specific fields. The `type` string is the discriminator.

### 3.1 Common fields (all advancements)

| Key | Type | Meaning |
|---|---|---|
| `type` | string | Discriminator (table below). |
| `desc` | string | Human-readable audit description. |
| `cost` | int | XP spent. **Positive = XP spent, negative = XP gained (flaws), 0 = free** (starting grants, rank-ups). |
| `timestamp` | float | Unix time (with sub-second precision). Use for ordering/audit; not guaranteed unique. |
| `rule` | string \| null | Optional rule/effect id (merits, flaws, techniques, kata…). |

### 3.2 Discriminator table

| `type` | Class | Extra fields | Represents |
|---|---|---|---|
| `rank` | `Rank` | *(large — see [§3.3](#33-the-rank-advancement-type--rank))* | An insight-rank step: school, granted skills/spells/kiho/merits/flaws, choices. |
| `attrib` | `AttribAdv` | `attrib` (int, trait index) | One rank bought in a trait. |
| `void` | `VoidAdv` | — | One void rank bought. |
| `skill` | `SkillAdv` | `skill` (str id) | One rank bought in a skill. |
| `emph` | `SkillEmph` | `skill` (str id), `text` (str) | A skill emphasis acquired. |
| `kata` | `KataAdv` | `kata` (str id) | A kata learned. |
| `kiho` | `KihoAdv` | `kiho` (str id) | A kiho learned. |
| `spell` | `SpellAdv` | `spell` (str id) | A spell gained via rank/school (cost 0). |
| `memo_spell` | `MemoSpellAdv` | `spell` (str id) | A spell memorized/bought (cost = mastery). |
| `perk` | `PerkAdv` | `perk` (str id), `rank` (int), `tag` (str\|null), `extra` (str) | A merit (`tag="merit"`, cost > 0) or flaw (`tag="flaw"`, cost < 0). |

> **Reader rule of thumb:** to count "how many ranks does the character have in skill X / trait Y", you tally the matching `advans[]` entries **plus** the starting grants found inside `rank` advancements. See [§4](#4-deriving-character-state).

### 3.3 The `rank` advancement (`type: "rank"`)

`Rank` is the only advancement that nests **typed sub-objects**, and the only one the loader always rehydrates into a real class instance. Its fields:

| Key | Type | Meaning |
|---|---|---|
| `rank` | int | Insight rank (1, 2, 3, …). |
| `school` | string \| null | School id active at this rank. |
| `school_rank` | int | School rank within that school. *(Legacy saves may have `0`; back-filled to `rank` on load.)* |
| `replaced` | string \| null | Previous school id if an alternate path replaced the school. |
| `skills` | string[] | Skill ids **granted** by this rank's school (immutable). |
| `skills_to_choose` | array(SchoolSkillWildcardSet) | Pending "choose N skills from {…}" sets. Each set: `{ rank: int, wildcards: [{ value, modifier }, …] }`. |
| `emphases` | object(string→string[]) | Granted emphases: `skill_id → [emphasis, …]`. |
| `emphases_to_choose` | string[] | Pending emphasis choices. |
| `spells` | string[] | Spell ids granted (immutable). |
| `spells_to_choose` | array([element, count, tag]) | Pending spell choices, each a 3-tuple/array. |
| `gained_spells_count` | int | Bonus spells gained this rank. |
| `affinities` | string[] | Spell-element affinities granted. |
| `affinities_to_choose` | string[] | Pending affinity choices (e.g. `"any"`). |
| `deficiencies` | string[] | Spell-element deficiencies. |
| `deficiencies_to_choose` | string[] | Pending deficiency choices. |
| `kiho` | string[] | Kiho ids granted (immutable). |
| `gained_kiho_count` | int | Bonus kiho slots granted. |
| `merits` | array(PerkAdv) | School-granted merits (each a `perk`-shaped object, `tag="merit"`). |
| `flaws` | array(PerkAdv) | School-granted flaws (each a `perk`-shaped object, `tag="flaw"`). |
| `outfit` | string[] | Starting outfit items (immutable). |
| `money` | int[3] | `[koku, bu, zeni]` granted at this rank. |

> The `*_to_choose` lists describe **pending** decisions made in the desktop editor. A read-only companion can safely treat them as informational (or ignore them); the *resolved* results live in the non-`_to_choose` lists and in subsequent advancements.

---

## 4. Deriving character state

This is the part a reader **must** get right. Most "current" values are not stored — they are computed from `starting_*` fields, the `advans[]` history, and (for some) the datapack. References are to `l5r/api/character/`.

### 4.1 Skills (`skills.py`)

For a skill id `S`, **current rank** =
- count of `rank` advancements whose `skills[]` contains `S` (starting grants), **plus**
- count of `skill` advancements with `skill == S` (bought ranks), **plus**
- rule-acquired ranks (special cases, e.g. a free Lore from certain rules).

**Emphases** for `S` = `rank.emphases[S]` across all rank advancements (starting) **plus** all `emph` advancements with `skill == S`.

### 4.2 Traits, rings, and void

For trait index `i`:
```
trait_rank(i) = starting_traits[i]
              + count(AttribAdv where attrib == i)
              + family_bonus(i)        # if the family's trait == i
              + school_bonus(i)        # if the first school's trait == i
```
`void_rank = starting_void + count(VoidAdv) + family/school void bonuses`.

Ring rank = `min` of the ring's two traits (see [§2.7](#trait-index--ring-mapping)). The family/school bonuses come from the datapack (see the datapack spec). A companion without full datapack data can still get the *bought* contribution from `advans[]`; the family/school +1 must come from the datapack.

### 4.3 Merits & flaws (`merits.py`, `flaws.py`)

- **Starting** merits/flaws = the `merits[]` / `flaws[]` lists inside the **rank-1** advancement.
- **Bought** merits = `perk` advancements with `tag == "merit"` (or `cost > 0`).
- **Bought** flaws = `perk` advancements with `tag == "flaw"` (or `cost < 0`).
- Full list = starting + bought.

### 4.4 Schools & techniques (`schools.py`)

- **All schools** = the distinct `school` ids across all `rank` advancements.
- **Current school** = `school` of the most recent `rank` advancement; **first school** = `school` of the rank-1 advancement.
- **School rank in school X** = count of `rank` advancements where `school == X` **or** `replaced == X`.
- **Technique at insight rank N**: find the `rank` advancement with `rank == N`, read its `school` + `school_rank`, then look up that school's technique list at that school-rank **in the datapack**. Techniques are *not* stored in the save file — only the school/rank coordinates that index into the datapack.

### 4.5 Spells (`spells.py`)

- **School/known spells** = concatenation of `rank.spells[]` across ranks **plus** all `spell` advancements.
- **Memorized/bought spells** = all `memo_spell` advancements (`spell` id; cost = mastery).
- **Affinities / deficiencies** = concatenation of `rank.affinities[]` / `rank.deficiencies[]` across ranks, merged with any rule-derived effects.

### 4.6 Wounds and health

`wounds` and `void_points` are stored counters. The **wound-level table** (how many wounds before each penalty step, and the penalties) is derived from the Earth ring / Stamina and the two health multipliers via the rules in `l5r/api/rules/`. A companion that tracks damage at the table needs to reproduce that table from `earth`/`stamina`, `health_multiplier`, and `health_base_multiplier`. (See the rules module for the exact RAW formula.)

### 4.7 Experience

```
xp_spent     = sum(cost for adv in advans if cost > 0)
xp_from_flaws = sum(-cost for adv in advans if adv.type=="perk" and adv.tag=="flaw")
xp_available = exp_limit + xp_from_flaws
xp_left      = xp_available - xp_spent
```

### 4.8 Insight rank

Two notions exist: the **finalized** insight rank = the highest `rank` among `rank` advancements; the **potential** rank is computed from the insight *value* (itself derived from traits, ring costs and void) against the RAW insight table. For a companion, the finalized rank (highest `rank.rank`) is the practical one.

### 4.9 Stored vs. derived — quick reference

| Concept | Stored | Derived from |
|---|---|---|
| Trait/ring rank | `starting_traits` + `AttribAdv` | starting + advans + family/school (datapack) |
| Void rank | `starting_void` + `VoidAdv` | starting + advans + family/school |
| Skill rank | `rank.skills` + `SkillAdv` | starting grants + bought + acquired |
| Merits/flaws | rank-1 `merits`/`flaws` + `perk` | merge starting + bought |
| Schools | each `rank.school` | distinct over ranks |
| Techniques | *(only school + school_rank)* | datapack lookup |
| Spells | `rank.spells` + `spell`/`memo_spell` | concatenate |
| Honor/glory/status/… | delta only | `starting (rules) + delta` |
| Wound levels | `wounds` counter only | earth/stamina + multipliers |
| XP | `cost` per advancement | aggregate advans |
| `attribs`/`void` (legacy) | — | **ignore** |

---

## 5. Nested model objects

### 5.1 `ArmorOutfit` (`armor` key)

| Key | Type | Meaning |
|---|---|---|
| `name` | string | Armor name. |
| `tn` | int | TN bonus to hit the wearer. |
| `rd` | int | Damage reduction. |
| `desc` | string | Effect description. |
| `rule` | string | Effect/rule id. |
| `cost` | string | Free-text cost (e.g. `"50 koku"`). |

### 5.2 `WeaponOutfit` (each element of `weapons`)

| Key | Type | Meaning |
|---|---|---|
| `name` | string | Weapon name. |
| `dr` | string | Damage roll (e.g. `"3k2"`). |
| `dr_alt` | string | Alternate damage roll (e.g. two-handed). |
| `range` | string | `"melee"`, `"ranged"`, … |
| `strength` | int \| string | Strength bonus/contribution. Serialized as `weapon.strength or 'N/A'` (`outfit.py`), so a falsy value is written as the **string** `"N/A"`, not `0`. Readers must tolerate both. |
| `min_str` | int \| string | Minimum Strength to wield. Same `'N/A'` fallback as `strength`. |
| `qty` | int | Quantity carried. |
| `skill_id` | string \| null | Skill id used to attack. |
| `skill_nm` | string | Denormalized skill name (display). |
| `base_atk` / `max_atk` | string | Base / max attack roll. |
| `base_dmg` / `max_dmg` | string | Base / max damage roll. |
| `tags` | string[] | Weapon tags (e.g. `["polearm"]`). |
| `trait` | string | Associated ring/trait (e.g. `"earth"`). |
| `desc` | string | Description. |
| `rule` | string | Effect id. |
| `cost` | string | Free-text cost. |

### 5.3 `ModifierModel` (each element of `modifiers`)

| Key | Type | Meaning |
|---|---|---|
| `type` | string | Target of the modifier (table below). Default `"none"`. |
| `dtl` | string \| null | Detail: skill id (`skir`), trait (`trat`), ring (`ring`), weapon (`wdmg`/`atkr`); else `null`. |
| `value` | int[3] | `[base, increment, final]`. |
| `reason` | string | User rationale. |
| `active` | bool | Whether currently applied. |

`type` values: `wdmg` (weapon damage), `anyr` (any roll), `skir` (skill roll), `atkr` (attack roll), `trat` (trait roll), `ring` (ring roll), `hrnk` (health rank), `artn` (armor TN), `arrd` (armor RD), `init` (initiative), `wpen` (wound penalty), `none`.

---

## 6. Round-trip / load behavior (`load_from`, `_load_advancement`)

When the desktop app reads a `.l5r` it does a flat `obj.__dict__[k] = json[k]` copy, **then rehydrates** the few places that nest typed objects (a plain `dict` would otherwise lack the expected attributes):

1. `armor` → re-instantiated as `ArmorOutfit`.
2. each `weapons[i]` → `WeaponOutfit`.
3. each `modifiers[i]` → `ModifierModel`.
4. each `advans[i]` → `_load_advancement`:
   - `type == "rank"` → real `Rank`, then rehydrate `skills_to_choose` (→ `SchoolSkillWildcardSet` + `SchoolSkillWildcard`), `merits`/`flaws` (→ `PerkAdv`), and `spells_to_choose` (arrays → 3-tuples). Back-fill `school_rank = rank` if it was `0`.
   - any other `type` → generic advancement with the dict applied.

A non-Python reader doesn't need to replicate the class machinery — it just needs to read the JSON shapes documented above and apply the same defaulting/back-fill (`school_rank` defaulting to `rank`).

---

## 7. Minimal example

```json
{
  "name": "Doji Test",
  "uuid": "3f2a9c10-7b4e-4a2d-9f1c-2e5b8d6a0c11",
  "clan": "crane",
  "family": "doji",
  "version": "0.0",
  "starting_traits": [2, 2, 2, 2, 2, 2, 2, 2],
  "starting_void": 2,
  "attribs": [0, 0, 0, 0, 0, 0, 0, 0],
  "void": 0,
  "honor": 0.0, "glory": 0.0, "status": 0.0, "infamy": 0.0, "taint": 0.0,
  "exp_limit": 40,
  "wounds": 0, "void_points": 0,
  "health_multiplier": 2, "health_base_multiplier": 5,
  "spells_per_rank": 3,
  "attrib_costs": [4,4,4,4,4,4,4,4], "void_cost": 6, "insight_calculation": 1,
  "money": [0, 0, 0], "outfit": [],
  "advans": [
    {
      "type": "rank", "desc": "Insight Rank 1", "rule": null, "cost": 0,
      "timestamp": 1782726486.68,
      "rank": 1, "school": "doji_courtier_school", "school_rank": 1, "replaced": null,
      "skills": ["etiquette", "sincerity"], "skills_to_choose": [],
      "emphases": {"etiquette": ["courtesy"]}, "emphases_to_choose": [],
      "spells": [], "spells_to_choose": [], "gained_spells_count": 0,
      "affinities": [], "affinities_to_choose": [],
      "deficiencies": [], "deficiencies_to_choose": [],
      "kiho": [], "gained_kiho_count": 0,
      "merits": [], "flaws": [],
      "outfit": [], "money": [5, 0, 0]
    },
    { "type": "attrib", "desc": "Awareness 2→3", "rule": null, "cost": 4,
      "timestamp": 1782726490.0, "attrib": 3 },
    { "type": "skill", "desc": "Sincerity 1→2", "rule": null, "cost": 2,
      "timestamp": 1782726492.0, "skill": "sincerity" },
    { "type": "perk", "desc": "Allies", "rule": "allies", "cost": 4,
      "timestamp": 1782726494.0, "perk": "allies", "rank": 1, "tag": "merit", "extra": "" }
  ],
  "armor": null,
  "weapons": [
    { "name": "Katana", "dr": "3k2", "dr_alt": "", "range": "melee",
      "strength": 0, "min_str": 0, "qty": 1,
      "skill_id": "kenjutsu", "skill_nm": "Kenjutsu",
      "base_atk": "", "max_atk": "", "base_dmg": "", "max_dmg": "",
      "tags": ["samurai"], "trait": "water", "desc": "", "rule": "", "cost": "" }
  ],
  "modifiers": [],
  "pack_refs": [{ "id": "core", "name": "Core Rulebook", "version": "1.0" }],
  "properties": { "sex": "female", "age": "20" },
  "extra_notes": ""
}
```

In this example the reader would conclude: Awareness 3 (2 + one `attrib` adv on index 3), Air ring = `min(reflexes 2, awareness 3) = 2`; Sincerity rank 2 (1 starting grant + 1 `skill` adv); merit *Allies*; school *Doji Courtier* at school-rank 1, whose rank-1 technique must be looked up in the datapack.
