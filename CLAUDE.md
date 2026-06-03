# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

L5RCM — a desktop character manager for the Legend of the Five Rings (4th ed.) tabletop RPG. PyQt6 GUI app written in Python 3.11+. Game rules content is not in this repo; it ships as separate "datapacks" loaded at runtime from the user's config directory.

## Commands

Run the app (from repo root):
```bash
python3 main.py
```
`main.py` sets `QT_API=pyqt6` before importing `l5r`. The whole codebase imports Qt through `qtpy` (`from qtpy import QtCore, QtGui, QtWidgets`) — never import `PyQt6`/`PyQt5` directly.

Install (editable, with all deps including the git-only ones):
```bash
pip install -e .
```
All runtime deps — including the forked `pypdf` and the `l5rdal` data-access layer — are declared in `pyproject.toml`. There is no `requirements.txt` and no `setup.py`.

Run tests (plain `unittest`, no pytest config):
```bash
python -m unittest discover -s l5r
# single module:
python -m unittest l5r.api.tests.test_character
# single test:
python -m unittest l5r.api.tests.test_character.TestCharacterBll.test_set_family
```
Set `QT_QPA_PLATFORM=offscreen` if running tests on a headless machine.

Lint (matches CI in `.github/workflows/ci.yml`):
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

Windows build (cx_Freeze, configured in `pyproject.toml`):
```bash
cxfreeze build
```
Linux `.deb` build: `tools/deploy/linux/makedeb.sh` (needs `librsvg2-bin`, `python3-docutils`, `fakeroot`).
Linux AppImage and Windows installer are produced by `.github/workflows/release.yml` (workflow_dispatch or `v3.*` tag push).

## Datapacks at runtime

The app is non-functional without datapacks. They are imported by the user via *Gear menu → Import datapack…* into `$XDG_CONFIG_HOME/openningia/l5rcm/data*` (Linux) or `%APPDATA%\openningia\l5rcm\data*` (Windows) — see `L5RCMContext.reload()` in `l5r/api/context.py` and `l5r.api.get_user_data_path()`. When debugging missing schools/skills/spells, the cause is usually missing or unselected datapacks, not a code bug.

## Architecture

### The `L5RCMContext` (`l5r/api/context.py`)
An `L5RCMContext` instance holds the mutable session state the API layer operates on: `ctx.pc` is the active character model, `ctx.ds` is the `l5rdal.Data` store, plus `ctx.locale`, `ctx.blacklist`, `ctx.current_rank_adv`, and `ctx.translation_provider`. The `l5r.api.character.*` and `l5r.api.data.*` submodules are *functions* that read/mutate this context — they are not classes. So `api.character.model()` returns the current PC; `api.character.new()` replaces it; `api.data.set_model(ds)` swaps the data store.

Internally every API function reads the active context via `get_context()` — a `contextvars.ContextVar` lookup. Production code calls `api.character.X(...)` as-is; no context is threaded through call sites. At import time `l5r/api/__init__.py` binds a single production `L5RCMContext` onto the `_current` ContextVar; that's the one production reads.

Tests override the context per-scope with `l5r.api.context.use(...)`:
```python
with l5r.api.context.use(L5RCMContext()):
    api.character.set_family('doji')
    # ...
# previous context restored here
```

Implication: don't thread a `ctx` parameter through call chains — the API layer reads it implicitly from the ContextVar. If you find yourself wanting a fresh context (e.g. for a test or a second character editor), construct an `L5RCMContext` and push it with `use()`.

### Layers
- **`l5r/api/`** — pure-Python business logic. `character/` (skills, schools, spells, merits, flaws, ranks, books, powers), `data/` (clan/family/school/skill/etc. lookups against the DAL), `rules/` (calculations like rings, TN, wounds, glory).
- **`l5r/models/`** — data classes for persistence and view models. `chmodel.AdvancedPcModel` is the character; `advancements/` holds the rank-by-rank advancement history that drives recomputation; `*viewmodel.py` are `QAbstractItemModel` adapters for Qt views.
- **`l5r/main.py`** — `L5RMain(L5RCMCore)` Qt main window coordinator (~380 lines), plus `def main()` which constructs `QApplication` and the window. Just lifecycle + signal wiring + the master `_build_generic_page` helper; the actual UI lives in `l5r/ui/`.
- **`l5r/ui/`** — every per-tab mixin and per-concern mixin that used to live in `main.py`. `L5RMain` is `class L5RMain(AboutTabMixin, AdvancementsTabMixin, AdvanceMixin, AdviseMixin, EquipmentTabMixin, HealthDisplayMixin, MenuMixin, ModelRefreshMixin, ModifiersTabMixin, NicebarMixin, NotesTabMixin, PcInfoTabMixin, PerksTabMixin, PersistenceMixin, PowersTabMixin, SettingsTabMixin, SkillsTabMixin, TechniquesTabMixin, WeaponsTabMixin, L5RCMCore)`. Each mixin file in `l5r/ui/` (and `l5r/ui/tabs/` for per-tab ones) also defines its own private `XxxSink(QObject)` containing the Qt slot endpoints for that area — `self.persistence_sink.save_character`, `self.weapons_sink.show_add_weapon`, etc. (the old monolithic `Sink1..Sink4` are gone). When adding a new menu action or button, find the matching mixin + sink rather than putting code in `main.py`.
- **`l5r/l5rcmcore/`** — base class `L5RCMCore` for the main window plus app-wide constants (`APP_NAME`, `APP_VERSION`, `DB_VERSION`, icon/file path helpers). `APP_VERSION` is the **single source of truth for the version**: `pyproject.toml` reads it via `[tool.setuptools.dynamic]`, and `tools/deploy/linux/makedeb.sh` greps the same line. Keep that line in a grep-friendly `APP_VERSION = 'X.Y.Z'` format.
- **`l5r/dialogs/`** and **`l5r/widgets/`** — modal dialogs and reusable Qt widgets. Icons are loaded via `l5r.widgets.iconloader` (which `pyproject.toml` explicitly includes for cxfreeze).
- **`l5r/exporters/`** — `FDFExporter` writes an FDF file then merges it into one of the bundled PDF templates in `l5r/share/l5rcm/sheet_*.pdf` to produce character sheets. PDF tooling is `pypdf` (forked: `git+https://github.com/OpenNingia/pypdf.git@main`). `npc.py` handles NPC-style export.
- **`l5r/diceroller/`** — standalone dice subsystem (`drcore.py` rules, `drgui.py` UI).
- **`l5r/util/`** — `settings.L5RCMSettings` (QSettings wrapper), `log` (loggers per subsystem: `log.api`, `log.ui`, etc. — use these, don't `print`), `worker.Worker` (QThreadPool runnable), `osutil`, `fsutil`, `names`.

### Resources
- `l5r/share/` ships PDF sheet templates, banners, name lists, and icons. Listed in `[tool.setuptools.package-data]` in `pyproject.toml` — when adding new bundled assets, add them there *and* verify cxfreeze still picks them up.
- Translations live in `l5r/share/l5rcm/i18n/*.qm` (compiled) and `l5r/i18n/` (sources). The `.pro` file is `l5r/l5rcm.pro`.

## CI / Release

- `.github/workflows/ci.yml` — lint (flake8) + tests (unittest discover) on every PR and push to master.
- `.github/workflows/release.yml` — three matrix-style jobs (Windows installer via cx_Freeze + Inno Setup, Linux `.deb`, Linux AppImage). Triggered by `workflow_dispatch` (for pre-release builds, artifacts only) or by pushing a `v3.*` tag (which also creates a draft GitHub Release). Windows signing is SignPath-ready: the signing steps activate only when `secrets.SIGNPATH_API_TOKEN` and the `SIGNPATH_*` repo variables are populated.

## Conventions to preserve

- **Qt imports always through `qtpy`**, never `PyQt6` directly. The codebase deliberately targets multiple Qt bindings via the `QT_API` env var (set in `main.py`).
- **Read context implicitly via `get_context()`, don't thread `ctx` through call chains.** Every `l5r.api.character.*` / `l5r.api.data.*` / `l5r.api.rules.*` function reads the active `L5RCMContext` from the `_current` `ContextVar` (see [The `L5RCMContext`](#the-l5rcmcontext-l5rapicontextpy) above). Production binds one at import time; tests scope an alternative with `l5r.api.context.use(...)`. If you find yourself adding a `ctx` parameter to an API function, you're swimming against the pattern.
- **Setters in `l5r/api/character/*.py` own the dirty flag.** When you add a function that mutates `pc`, call `set_dirty_flag(True)` so close-the-window prompts work. `set_money` and `set_health_multiplier` are the reference shape. The Qt-side wrappers in `L5RCMCore` should delegate to the API setter rather than poking `self.pc.<attr>` directly.
- The package-level `__init__.py` files in `l5r/dialogs/`, `l5r/diceroller/`, `l5r/exporters/`, `l5r/models/`, `l5r/widgets/` use `from X import *` to re-export submodule symbols. This is the intentional namespace shape so callers can write `dialogs.AdvDlg(...)`. Don't "fix" these in passing — converting them requires touching every consumer.
- **Mixin + per-mixin sink pattern.** Each `l5r/ui/*.py` module (and `l5r/ui/tabs/*.py`) exports both `XxxMixin` (plain Python methods inherited by `L5RMain`) and `XxxSink(QObject)` (Qt slot endpoints owned by `L5RMain` as `self.xxx_sink`). When wiring a `signal.connect(...)`, connect to a sink method (`self.persistence_sink.save_character`); when calling internal helpers from other mixin code, call the mixin method directly (`self.load_character_from(path)`). Sinks have proper Qt parent-ownership and keep the per-class slot surface from ballooning on a 19-base MRO.
- **Every QML UI element must match the design system reference in [`docs/L5R_UI_Design_System.md`](docs/L5R_UI_Design_System.md).** That document is the authoritative style spec for the `l5r/qmlui/` QML UI: every component, dialog, form, and control must derive its colours, fonts, spacing, sizing, and motion from the tokens defined there. Do not hard-code hex colours or pixel values inline and do not introduce colours/fonts/spacing that are not in the spec — add the token to `l5r/qmlui/qml/Theme/Theme.qml` (the token singleton, imported everywhere via `import Theme 1.0`) first, then consume it. When the reference and `Theme.qml` disagree, treat it as a gap to reconcile, not a free choice. Clan accent overrides (Section 5) belong in a runtime-writable singleton, not duplicated per-component.
