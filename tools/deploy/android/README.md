# Android build (QML-only) — feasibility spike

This directory packages the **QML-only** UI as an Android APK via
`pyside6-android-deploy` (which wraps python-for-android). It is an
**experimental spike**, not a supported release target.

## Why it's structured this way

- **Binding:** Android needs **PySide6** — PyQt6 ships no Android wheels. The
  codebase imports Qt through `qtpy`, so the binding is selected at runtime
  by `QT_API`. The Android entry point forces `QT_API=pyside6`.
- **Entry point:** [`android_main.py`](../../../android_main.py) (repo root).
  It deliberately does **not** import `l5r.main`, because that module imports
  the entire legacy QWidget UI (`from l5r.ui... import`), which drags in
  desktop-only deps (`lxml` via `l5r/dialogs/spelldlg.py`, `pyqtwaitingspinner`,
  `darkdetect`). Instead it calls `l5r.qmlui.run_qml_app` directly after a
  minimal `QApplication` + settings bootstrap.
- **Pure-Python deps:** the mobile dep set (`pyproject.toml` →
  `[project.optional-dependencies] android`) is pure-Python. The key enabler
  is **`l5rdal >= v1.4.2`**, which dropped `lxml` for stdlib `xml.etree`
  (lxml was only used for datapack *authoring*, never loading). With no
  C-extensions, python-for-android needs no custom recipes.
- **Writable storage:** `l5r.api.is_android()` (set when `ANDROID_ARGUMENT`
  is present) routes `get_user_data_path()` to the app's private storage
  (`ANDROID_PRIVATE`). Datapacks download in-app via the existing Library
  section (stdlib `urllib`).
- **Dialogs:** native `QFileDialog`/`QMessageBox` don't map to Android, so
  the QML `AppController` guards them: `fileSaveAs` writes to app storage
  under the character name, File > Open is a no-op (session resume covers
  reload), and PDF/NPC export are out of scope for mobile.

## Building

CI does this on Linux (python-for-android does not run on Windows):
`.github/workflows/android.yml` (manual `workflow_dispatch`).

Locally on Linux/WSL2:

```bash
pip install "PySide6==6.11.1"       # provides the pyside6-android-deploy CLI
pip install -r "$(python -c 'import os,PySide6;print(os.path.join(os.path.dirname(PySide6.__file__),"scripts","requirements-android.txt"))')"
pip install -e ".[android]"          # pure-Python runtime deps
sdkmanager --install "ndk;27.2.12479018" "platforms;android-35" "build-tools;35.0.0"
export ANDROID_NDK_ROOT=$ANDROID_SDK_ROOT/ndk/27.2.12479018

# OSS Android wheels (aarch64, cp311) from download.qt.io. pyside6-android-deploy
# does NOT fetch these, and `qtpip --android` pulls the COMMERCIAL wheels (needs a
# Qt commercial licence), so download the open-source wheels directly:
base=https://download.qt.io/official_releases/QtForPython
curl -fSLO "$base/pyside6/pyside6-6.11.1-6.11.1-cp311-cp311-android_aarch64.whl"
curl -fSLO "$base/shiboken6/shiboken6-6.11.1-6.11.1-cp311-cp311-android_aarch64.whl"

pyside6-android-deploy -c tools/deploy/android/pysidedeploy.spec \
  --wheel-pyside  pyside6-6.11.1-6.11.1-cp311-cp311-android_aarch64.whl \
  --wheel-shiboken shiboken6-6.11.1-6.11.1-cp311-cp311-android_aarch64.whl \
  --ndk-path "$ANDROID_NDK_ROOT" --sdk-path "$ANDROID_SDK_ROOT" \
  --keep-deployment-files
```

## The two things that will need iteration (make-or-break)

1. **Android Qt wheel ↔ PySide6 version match.** `pyside6-android-deploy`
   fetches Android wheels matching the desktop PySide6 it runs under. Pin
   `PYSIDE_VERSION` (workflow input) to a version with published Android
   wheels; bump the NDK version in lockstep.
2. **NDK version.** Must be the one the chosen Qt-for-Android expects
   (r27 / 27.2.12479018 for Qt 6.11; r26 / 26.1.10909125 for Qt 6.7/6.8).
   A mismatch is the most common build failure.

## Spike success criteria (verify on an emulator)

1. App launches into `MainSheet.qml` (PySide6 binding).
2. `l5rdal` imports without `lxml`; `l5rdal.Data` builds from app storage.
3. A datapack downloads in-app and populates schools/skills.
4. Create → edit → save to app storage → kill + relaunch → data persists.

## Already verified on desktop (PySide6)

- The full QML tree loads under PySide6; all 26 QML tests + the full 145-test
  suite pass under `QT_API=pyside6`.
- Data loads with `lxml` hard-blocked (37 clans).
- `android_main.main()` boots the QML UI with `lxml`/`PyQt6`/
  `pyqtwaitingspinner`/`darkdetect` blocked, loading zero legacy modules.
- With `ANDROID_ARGUMENT` set, `get_user_data_path()` resolves under
  `ANDROID_PRIVATE` and `fileSaveAs` writes a `.l5r` there with no dialog.
