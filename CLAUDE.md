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

The app is non-functional without datapacks. They are imported by the user via *Gear menu → Import datapack…* into `$XDG_CONFIG_HOME/openningia/l5rcm/data*` (Linux) or `%APPDATA%\openningia\l5rcm\data*` (Windows) — see `l5r.api.L5RCMAPI.reload()` / `l5r.api.get_user_data_path()`. When debugging missing schools/skills/spells, the cause is usually missing or unselected datapacks, not a code bug.

## Architecture

### The `__api` singleton (`l5r/api/__init__.py`)
A single module-level `L5RCMAPI` instance holds global mutable state: `__api.pc` is the active character model, `__api.ds` is the `l5rdal.Data` store, plus locale and the current rank advancement. The `l5r.api.character.*` and `l5r.api.data.*` submodules are *functions* that read/mutate this singleton — they are not classes. So `api.character.model()` returns the current PC; `api.character.new()` replaces it; `api.data.set_model(ds)` swaps the data store (this is how tests inject fake data — see `l5r/tests/fakedata.py`).

Implication: tests and any code that touches characters/data must `set_model` first or the singleton will be `None`. Don't try to thread a character object through call chains — the API layer assumes the singleton.

### Layers
- **`l5r/api/`** — pure-Python business logic. `character/` (skills, schools, spells, merits, flaws, ranks, books, powers), `data/` (clan/family/school/skill/etc. lookups against the DAL), `rules/` (calculations like rings, TN, wounds, glory).
- **`l5r/models/`** — data classes for persistence and view models. `chmodel.AdvancedPcModel` is the character; `advancements/` holds the rank-by-rank advancement history that drives recomputation; `*viewmodel.py` are `QAbstractItemModel` adapters for Qt views.
- **`l5r/main.py`** — the monolithic `L5RMain(L5RCMCore)` Qt main window (~2500 lines), plus `def main()` which constructs `QApplication` and the window. Most UI wiring lives here.
- **`l5r/l5rcmcore/`** — base class `L5RCMCore` for the main window plus app-wide constants (`APP_NAME`, `APP_VERSION`, `DB_VERSION`, icon/file path helpers). `APP_VERSION` is the **single source of truth for the version**: `pyproject.toml` reads it via `[tool.setuptools.dynamic]`, and `tools/deploy/linux/makedeb.sh` greps the same line. Keep that line in a grep-friendly `APP_VERSION = 'X.Y.Z'` format.
- **`l5r/sinks/`** — `Sink1`..`Sink4` are `QObject` subclasses that group menu/button slot handlers split out from `main.py` to keep it (slightly) manageable. `sinks/__init__.py` star-imports all four. When adding a new menu action, find the matching sink rather than putting more code in `main.py`.
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
- **Don't move logic out of the `__api` singleton pattern** unless you intend to refactor the whole API layer — every `l5r.api.character.*` function depends on it.
- The package-level `__init__.py` files in `l5r/dialogs/`, `l5r/diceroller/`, `l5r/exporters/`, `l5r/models/`, `l5r/sinks/`, `l5r/widgets/` use `from X import *` to re-export submodule symbols. This is the intentional namespace shape so callers can write `dialogs.AdvDlg(...)`. Don't "fix" these in passing — converting them requires touching every consumer.
- `main.py` (the 2551-line one) currently uses `from l5r.l5rcmcore import *`. That star-import is on the roadmap to disappear when `L5RMain` is split into per-tab modules, but until then it's load-bearing — any new symbol you want available to `main.py` must be reachable through `l5r.l5rcmcore`'s namespace.
