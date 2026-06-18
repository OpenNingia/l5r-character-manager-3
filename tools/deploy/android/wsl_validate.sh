#!/usr/bin/env bash
# =============================================================================
# WSL validation build for the L5RCM Android (QML) target.
#
# PURPOSE: prove that the "simplified" deploy config builds a working APK, so we
# can delete the fragile bits of .github/workflows/android.yml:
#   - the whole qtpy-trimming step               (REMOVED here)
#   - the Core-first reorder + Widgets-strip      (REMOVED here)
# ...keeping only the single irreducible patch:
#   - the p4a -> Python 3.11 commit pin           (KEPT here, one set_value line)
#
# The hypothesis (grounded in PySide6 6.11.1 sources, deploy_lib/android/
# android_config.py): when `qt.modules` is set in pysidedeploy.spec, the tool
# uses that list verbatim for --qt-libs and SKIPS module auto-detection + the
# project_dir AST scan -> qtpy no longer needs trimming, Widgets never enters
# --qt-libs, and Core stays first because the spec lists it first.
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
  openjdk-17-jdk unzip wget git rsync python3-venv >/dev/null
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
python3 -m venv "$HOME/.l5rcm-android-venv"
# shellcheck disable=SC1091
source "$HOME/.l5rcm-android-venv/bin/activate"
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

# --- 5. p4a Python-3.11 pin (THE ONLY source patch we keep) ---
echo "==> [5/7] inject p4a.commit pin into the deploy tool generator"
# NOTE: deliberately NOT touching the modules-join line -- testing the
# hypothesis that qt.modules in the spec already controls --qt-libs.
BZ="$(python -c 'import os, PySide6; print(os.path.join(os.path.dirname(PySide6.__file__), "scripts", "deploy_lib", "android", "buildozer.py"))')"
python - "$BZ" "$P4A_COMMIT" <<'PY'
import re, sys
path, commit = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
if "p4a.commit" not in s:
    pat = re.compile(r'(?m)^([ \t]*)self\.set_value\(\s*["\']app["\']\s*,\s*["\']p4a\.branch["\']\s*,\s*["\']develop["\']\s*\).*$')
    s, n = pat.subn(lambda m: m.group(0) + "\n" + m.group(1) + f'self.set_value("app", "p4a.commit", "{commit}")', s)
    assert n == 1, f"expected 1 p4a.branch set_value, found {n}"
    open(path, "w", encoding="utf-8").write(s)
    print(f"    pinned p4a.commit={commit}")
else:
    print("    p4a.commit already present")
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
set +e
pyside6-android-deploy \
  -c pysidedeploy.spec \
  --wheel-pyside "$WHEEL_PYSIDE" \
  --wheel-shiboken "$WHEEL_SHIBOKEN" \
  --ndk-path "$ANDROID_NDK_ROOT" \
  --sdk-path "$ANDROID_SDK_ROOT" \
  --keep-deployment-files \
  -f -v
BUILD_RC=$?
set -e

echo ""
echo "============================================================"
echo " BUILD EXIT CODE: $BUILD_RC"
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
if [ "$BUILD_RC" -eq 0 ]; then
  echo "OK: build succeeded WITHOUT qtpy-trim / Widgets-strip / Core-reorder."
  echo "Next: install the APK and confirm the QML UI loads (no QtWidgets crash)."
else
  echo "Build failed -- paste the last ~60 lines of output above + the spec dump."
fi
