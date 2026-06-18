#!/usr/bin/env bash
# =============================================================================
# WSL validation build for the L5RCM Android (QML) target.
#
# PURPOSE: prove that a CLEANER deploy config builds a working APK, so we can
# replace the fragile bits of .github/workflows/android.yml:
#   - the whole in-place qtpy-trimming step  -> two CLI flags (see below)
#   - the Widgets-strip generator patch      -> no longer needed
# ...keeping:
#   - the p4a -> Python 3.11 commit pin       (irreducible: hardcoded in the tool)
#   - the Core-first reorder of --qt-libs      (load-order safety, set-derived list)
#
# ROOT CAUSE we proved (run #1 + reading config.py): setting `qt.modules` in
# pysidedeploy.spec does NOT work, because Config.__init__ (base class) ends with
# `self.modules = []`, whose setter writes "" into qt.modules in the in-memory
# parser BEFORE AndroidConfig reads it -> get_value("qt","modules") is empty ->
# the tool always falls back to AST auto-detection, which scans qtpy's shims and
# finds bogus modules (AxContainer, Widgets, ...) -> crash. So qt.modules is a
# dead end on 6.11.1; we must instead steer the auto-detection:
#   --extra-ignore-dirs qtpy  -> get_py_files() skips qtpy in the AST scan
#                                (scan-only; p4a still bundles qtpy at runtime),
#                                so no bogus modules and NO need to delete files.
#   --extra-modules <list>    -> main() does config.modules += these, declaring
#                                the exact Qt module set explicitly.
# This is the run #2 hypothesis: the two flags fully replace the qtpy-trim hack.
#
# Run it from the repo root checkout (even on /mnt/c -- it copies the tree into
# the native WSL filesystem first, where p4a builds correctly and fast):
#     bash tools/deploy/android/wsl_validate.sh
#
# First run downloads NDK r27 (~1 GB) + SDK + builds CPython/openssl/libffi from
# source via p4a: expect 30-60 min. Re-runs are much faster (toolchain cached).
#
# At the end it prints the GENERATED buildozer.spec and the deployment/ tree --
# paste those back so we can decide whether buildozer.spec is committable too.
# =============================================================================
set -euo pipefail

# --- knobs (keep in sync with android.yml) ---
PYSIDE_VERSION="${PYSIDE_VERSION:-6.11.1}"
# HOST interpreter used to CREATE the venv -- must be 3.11 (the cp311 wheels need
# libpython3.11). On Ubuntu `python3` may be 3.12+, so pin the binary explicitly.
# Override with `PYTHON=python3.11 bash ...` if your binary is named differently.
# NB: only for the host; inside the activated venv we call `python`/`python3`,
# which already resolve to this 3.11.
PYTHON="${PYTHON:-python3.11}"
P4A_COMMIT="6b66944a2f51e0c848c7ac51e04a771324067ecc"   # last p4a on Python 3.11.13
NDK_VER="27.2.12479018"
SDK_ROOT="$HOME/android-sdk"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DST_DIR="$HOME/l5rcm-android-build"

echo "==> source tree : $SRC_DIR"
echo "==> build tree  : $DST_DIR  (native WSL fs)"
echo "==> PySide6     : $PYSIDE_VERSION   NDK: $NDK_VER"

# --- 0. system build deps (autotools for p4a recipes, JDK17 for gradle) ---
echo "==> [0/7] apt deps"
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  autoconf automake libtool libltdl-dev pkg-config m4 \
  build-essential zlib1g-dev libffi-dev libssl-dev \
  openjdk-17-jdk zip unzip wget git rsync python3-venv >/dev/null
  # zip: p4a's create_python_bundle shells out to `zip` to pack the stdlib
  #      (sh.CommandNotFound: zip otherwise). Preinstalled on ubuntu-latest CI,
  #      but not on a bare WSL.
export JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(which javac)")")")"
echo "    JAVA_HOME=$JAVA_HOME"

# --- 1. copy working tree into native fs (exclude heavy/regenerated dirs) ---
echo "==> [1/7] copy working tree -> $DST_DIR"
mkdir -p "$DST_DIR"
rsync -a --delete \
  --exclude '.git' --exclude '.venv' --exclude 'build' \
  --exclude '.buildozer' --exclude 'deployment' \
  --exclude 'qtpy' --exclude 'asq' --exclude 'l5rdal' \
  --exclude 'pypdf' --exclude 'packaging' --exclude 'certifi' \
  "$SRC_DIR/" "$DST_DIR/"
cd "$DST_DIR"

# --- 2. Android SDK cmdline-tools + NDK ---
echo "==> [2/7] Android SDK + NDK r$NDK_VER"
if [ ! -x "$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" ]; then
  mkdir -p "$SDK_ROOT/cmdline-tools"
  wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdtools.zip
  rm -rf /tmp/cmdline-tools && unzip -q /tmp/cmdtools.zip -d /tmp
  rm -rf "$SDK_ROOT/cmdline-tools/latest"
  mv /tmp/cmdline-tools "$SDK_ROOT/cmdline-tools/latest"
fi
export ANDROID_SDK_ROOT="$SDK_ROOT"
export ANDROID_HOME="$SDK_ROOT"
SM="$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
yes | "$SM" --sdk_root="$SDK_ROOT" --licenses >/dev/null 2>&1 || true
"$SM" --sdk_root="$SDK_ROOT" "ndk;$NDK_VER" "platforms;android-35" "build-tools;35.0.0" >/dev/null
export ANDROID_NDK_ROOT="$SDK_ROOT/ndk/$NDK_VER"

# buildozer 1.5.0 hardcodes <sdk>/tools/bin/sdkmanager (obsolete launcher, needs
# JAXB removed from JDK17) -> shim it to the modern cmdline-tools sdkmanager.
mkdir -p "$SDK_ROOT/tools/bin"
printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$SM" > "$SDK_ROOT/tools/bin/sdkmanager"
chmod +x "$SDK_ROOT/tools/bin/sdkmanager"

# --- 3. python venv + deploy tooling ---
echo "==> [3/7] venv + pyside6-android-deploy tooling"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "::error:: host interpreter '$PYTHON' not found. Install it"
  echo "          (sudo apt-get install python3.11 python3.11-venv) or pass PYTHON=..."
  exit 1
fi
echo "    host interpreter: $("$PYTHON" --version 2>&1) ($("$PYTHON" -c 'import sys;print(sys.executable)'))"
VENV="$HOME/.l5rcm-android-venv"
# Recreate the venv if it was built with a non-3.11 interpreter (e.g. a previous
# run picked the system python3). The cp311 wheels require libpython3.11.
if [ -x "$VENV/bin/python" ] && ! "$VENV/bin/python" -c 'import sys;sys.exit(0 if sys.version_info[:2]==(3,11) else 1)'; then
  echo "    existing venv is not 3.11 -> recreating"
  rm -rf "$VENV"
fi
"$PYTHON" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip
pip install -q "PySide6==${PYSIDE_VERSION}"
pip install -q -r "$(python -c 'import os, PySide6; print(os.path.join(os.path.dirname(PySide6.__file__), "scripts", "requirements-android.txt"))')"
pip install -q "asq>=2.0" "qtpy>=2.4" "certifi" \
  "git+https://github.com/OpenNingia/pypdf.git@fix_escape" \
  "git+https://github.com/OpenNingia/l5rcm-data-access.git@v1.4.2"

# --- 4. download OSS Android wheels (aarch64/cp311) ---
echo "==> [4/7] download OSS Android wheels"
base="https://download.qt.io/official_releases/QtForPython"
pyw="pyside6-${PYSIDE_VERSION}-${PYSIDE_VERSION}-cp311-cp311-android_aarch64.whl"
shw="shiboken6-${PYSIDE_VERSION}-${PYSIDE_VERSION}-cp311-cp311-android_aarch64.whl"
mkdir -p android_wheels
[ -f "android_wheels/$pyw" ] || curl -fSL --retry 3 -o "android_wheels/$pyw" "$base/pyside6/$pyw"
[ -f "android_wheels/$shw" ] || curl -fSL --retry 3 -o "android_wheels/$shw" "$base/shiboken6/$shw"
WHEEL_PYSIDE="$PWD/android_wheels/$pyw"
WHEEL_SHIBOKEN="$PWD/android_wheels/$shw"

# --- 5. patch the deploy tool generator: p4a pin + Core-first --qt-libs ---
echo "==> [5/7] patch deploy tool: p4a.commit pin + Core-first module order"
# Two idempotent injections into deploy_lib/android/buildozer.py:
#  (a) p4a.commit pin -- irreducible (p4a.branch=develop is hardcoded, no spec
#      lever; the develop branch ships Python 3.14, our wheels are cp311).
#  (b) Core-first reorder of the --qt-libs list -- libQt6Core's JNI_OnLoad must
#      run first to register the JavaVM; config.modules is set-derived (arbitrary
#      order), so we force Core to the front. NOTE: no Widgets-strip anymore --
#      with --extra-ignore-dirs qtpy, Widgets is never auto-detected and we don't
#      pass it via --extra-modules, so it can't appear in the list.
BZ="$(python -c 'import os, PySide6; print(os.path.join(os.path.dirname(PySide6.__file__), "scripts", "deploy_lib", "android", "buildozer.py"))')"
python - "$BZ" "$P4A_COMMIT" <<'PY'
import re, sys
path, commit = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
changed = False
# (a) p4a.commit right after the hardcoded p4a.branch set_value
if "p4a.commit" not in s:
    pat = re.compile(r'(?m)^([ \t]*)self\.set_value\(\s*["\']app["\']\s*,\s*["\']p4a\.branch["\']\s*,\s*["\']develop["\']\s*\).*$')
    s, n = pat.subn(lambda m: m.group(0) + "\n" + m.group(1) + f'self.set_value("app", "p4a.commit", "{commit}")', s)
    assert n == 1, f"expected 1 p4a.branch set_value, found {n}"
    changed = True
    print(f"    pinned p4a.commit={commit}")
else:
    print("    p4a.commit already present")
# (b) Core-first reorder of the modules join feeding --qt-libs
if 'modules = ",".join(["Core"]' not in s:
    s2, n2 = re.subn(
        r'(?m)^([ \t]*)modules\s*=\s*",".join\(\s*pysidedeploy_config\.modules\s*\)\s*$',
        r'\1modules = ",".join(["Core"] + [m for m in dict.fromkeys(pysidedeploy_config.modules) if m != "Core"])',
        s)
    assert n2 == 1, f"expected 1 modules-join line, found {n2}"
    s = s2
    changed = True
    print("    forced Core-first --qt-libs order")
else:
    print("    Core-first order already present")
if changed:
    open(path, "w", encoding="utf-8").write(s)
PY

# --- 6. vendor pure-Python deps into project_dir (NO qtpy trim this time) ---
echo "==> [6/7] vendor pure-Python deps (full qtpy, no trimming)"
python - <<'PY'
import importlib.util, os, shutil
for name in ("qtpy", "asq", "l5rdal", "pypdf", "packaging", "certifi"):
    spec = importlib.util.find_spec(name)
    assert spec and spec.origin, f"{name} not importable"
    src = os.path.dirname(spec.origin)
    dst = os.path.join(os.getcwd(), name)
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
    print(f"    vendored {name}")
PY

# --- 7. build the APK (single pyside6-android-deploy invocation) ---
echo "==> [7/7] pyside6-android-deploy build (this is the long step)"
cp tools/deploy/android/pysidedeploy.spec ./pysidedeploy.spec
# Purge stale generated recipes: the p4a PySide6 recipe bakes the module list
# into deployment/recipes/PySide6/__init__.py and copies one Qt{module}.abi3.so
# per module. A previous run's recipe (with a bad module list) would be reused
# (recipes_exist() short-circuits regeneration), so wipe it. Also drop any
# half-installed PySide6/shiboken6 under .buildozer so the recipe re-copies
# cleanly. This is CHEAP (re-unzips wheels + regenerates recipes, seconds) and
# does NOT touch the expensive cache (NDK, CPython compile, openssl/libffi).
# Needed only while iterating on the --extra-modules list; once stable, skip it
# for faster re-runs with: CLEAN=0 bash tools/deploy/android/wsl_validate.sh
if [ "${CLEAN:-1}" = "1" ]; then
  echo "    cleaning stale recipes + PySide6/shiboken6 installs (CLEAN=0 to skip)"
  # Surgical: only the generated recipes/jars, NOT deployment/.buildozer -- on a
  # successful build the deploy tool moves the whole .buildozer cache (incl. the
  # compiled hostpython3 / CPython) into deployment/, and nuking that would force
  # a full rebuild next run. Keep it.
  rm -rf deployment/recipes deployment/jar
  find .buildozer deployment/.buildozer -type d \( -name PySide6 -o -name shiboken6 \) \
    -path '*python-installs*' -exec rm -rf {} + 2>/dev/null || true
else
  echo "    CLEAN=0: keeping existing recipes/installs (fast re-run)"
fi
set +e
# --extra-ignore-dirs qtpy : keep qtpy out of the AST module scan (scan-only;
#                            p4a still bundles it) -> no bogus AxContainer/Widgets.
# --extra-modules <list>   : declare the Qt module set explicitly (qt.modules in
#                            the spec is clobbered by Config.__init__, see header).
#                            ONLY real PySide6 Python modules: QuickTemplates2 /
#                            QuickLayouts are native-only (no Qt*.abi3.so) and are
#                            pulled transitively; listing them makes the recipe's
#                            per-module abi3 copy crash (FileNotFoundError).
pyside6-android-deploy \
  -c pysidedeploy.spec \
  --wheel-pyside "$WHEEL_PYSIDE" \
  --wheel-shiboken "$WHEEL_SHIBOKEN" \
  --ndk-path "$ANDROID_NDK_ROOT" \
  --sdk-path "$ANDROID_SDK_ROOT" \
  --extra-ignore-dirs qtpy \
  --extra-modules Core,Gui,Network,Qml,Quick,QuickControls2,Svg \
  --keep-deployment-files \
  -f -v
DEPLOY_RC=$?
set -e
# pyside6-android-deploy wraps the buildozer run in try/except and returns 0 even
# when buildozer fails (it just prints "Exception occurred"). So the tool's exit
# code is NOT reliable -- judge success by whether an APK was actually produced.
APK="$(find . -maxdepth 3 -name '*.apk' 2>/dev/null | head -1)"
if [ -n "$APK" ]; then BUILD_RC=0; else BUILD_RC=1; fi

echo ""
echo "============================================================"
echo " VERDICT: $([ "$BUILD_RC" -eq 0 ] && echo 'APK PRODUCED (success)' || echo 'NO APK (failure)')"
echo " (deploy-tool exit code was $DEPLOY_RC -- unreliable, see note above)"
echo "============================================================"
echo ""
echo "----- GENERATED buildozer.spec (paste this back) -----------"
[ -f buildozer.spec ] && grep -vE '^\s*#' buildozer.spec | grep -vE '^\s*$' || echo "(buildozer.spec not produced)"
echo "----- end buildozer.spec -----------------------------------"
echo ""
echo "----- deployment/ tree (recipes + jars) --------------------"
[ -d deployment ] && find deployment -maxdepth 3 | sort || echo "(no deployment/ dir)"
echo "----- end deployment tree ----------------------------------"
echo ""
echo "----- produced APK(s) --------------------------------------"
find . -maxdepth 3 -name '*.apk' 2>/dev/null || true
echo "------------------------------------------------------------"
echo ""
echo "----- effective --qt-libs (what got bundled) --------------"
[ -f buildozer.spec ] && grep -E "p4a.extra_args" buildozer.spec || echo "(no buildozer.spec)"
echo "------------------------------------------------------------"
echo ""
if [ "$BUILD_RC" -eq 0 ]; then
  echo "OK: build succeeded WITHOUT the in-place qtpy-trim step."
  echo "    The two flags (--extra-ignore-dirs qtpy / --extra-modules) replaced it."
  echo "Next: install the APK and confirm the QML UI loads. Watch specifically for a"
  echo "runtime ImportError on QtWidgets (qtpy.QtGui may import QFileSystemModel from"
  echo "QtWidgets) -- if that happens we add back ONLY that one qtpy line, not the"
  echo "whole trim. Capture logcat: adb logcat | grep -iE 'python|qtpy|widgets'"
else
  echo "Build failed -- paste the last ~60 lines of output above + the --qt-libs line."
fi
