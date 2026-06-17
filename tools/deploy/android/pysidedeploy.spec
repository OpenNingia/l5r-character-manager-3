/ pyside6-android-deploy configuration for the QML-only Android build.
/
/ NOTE: pyside6-android-deploy parses this with ConfigParser(comment_prefixes="/"),
/ so comments MUST start with '/'. '#' and ';' are treated as content and break
/ the parse with MissingSectionHeaderError. Keep all comments '/'-prefixed.
/
/ IMPORTANT: pyside6-android-deploy resolves project_dir / input_file /
/ qml_files RELATIVE TO THIS FILE's directory, and `buildozer init` writes
/ buildozer.spec into the cwd. So this spec must be RUN FROM THE PROJECT ROOT
/ (copy it there): the paths below (project_dir=., android_main.py,
/ l5r/qmlui/qml) are repo-root-relative. CI copies it to the root before
/ running; the canonical copy lives here.
/
/ Starting point committed for reproducibility. pyside6-android-deploy may
/ normalise/extend this file on first run -- if it does, commit the updated
/ version. The entry point is android_main.py (QML-only, never imports the
/ legacy QWidget UI), and the runtime dep set is pure-Python (no lxml:
/ l5rdal >= v1.4.2 uses stdlib xml.etree), so python-for-android needs no
/ C-extension recipes.

[app]
title = L5RCM
project_dir = .
/ QML-only mobile entry point (forces QT_API=pyside6, L5RCM_UI=qml).
input_file = android_main.py
project_file =
exec_directory = .
icon =

[python]
python_path =
/ buildozer + cython are the python-for-android build prerequisites.
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]
/ QML import roots scanned for .qml files. The whole QML tree lives here.
qml_files = l5r/qmlui/qml
excluded_qml_plugins =
/ Qt modules the app links. QtQuick.Controls/Layouts pull in QuickControls2.
/ Network is needed for the in-app datapack download (stdlib urllib uses the
/ platform stack, but QtNetwork is a safe inclusion). NOTE: no Widgets -- the
/ mobile entry point (android_main.py) runs on a QGuiApplication and the QML
/ proxies import QtWidgets only lazily on desktop-only paths, so QtWidgets must
/ NOT be linked (the Java QtLoader would preload QtWidgets.abi3.so and crash).
/ pyside6-android-deploy ignores this list and auto-detects modules anyway;
/ it is kept accurate for documentation / local builds.
modules = Core,Gui,Network,Qml,Quick,QuickControls2,QuickTemplates2,QuickLayouts,Svg
plugins =

[android]
/ Left empty here: CI passes the OSS Android wheels explicitly via
/ --wheel-pyside / --wheel-shiboken (downloaded from download.qt.io). For a
/ local build, either fill these in or pass the same two flags.
wheel_pyside =
wheel_shiboken =
/ Single ABI for the spike to keep build time/size down. Add armeabi-v7a /
/ x86_64 (emulator) once arm64 works.
plugins =

[buildozer]
mode = debug
recipe_dir =
jars_dir =
ndk_path =
sdk_path =
local_recipes =
arch = aarch64
python_version = 3.11
