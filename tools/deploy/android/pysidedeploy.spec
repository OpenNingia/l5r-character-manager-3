/ pyside6-android-deploy configuration for the QML-only Android build.
/
/ NOTE: pyside6-android-deploy parses this with ConfigParser(comment_prefixes="/"),
/ so comments MUST start with '/'. '#' and ';' are treated as content and break
/ the parse with MissingSectionHeaderError. Keep all comments '/'-prefixed.
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
/ platform stack, but QtNetwork is a safe inclusion). Svg/widgets are kept
/ because some Quick Controls styling and the QApplication base need them.
modules = Core,Gui,Network,Qml,Quick,QuickControls2,QuickTemplates2,QuickLayouts,Svg,Widgets
plugins =

[android]
/ Leave empty so the deploy tool downloads the Android wheels that MATCH the
/ desktop PySide6 version installed in CI. Pin a version with published
/ Android wheels (see .github/workflows/android.yml header).
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
arch = arm64-v8a
