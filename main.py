#!/usr/bin/python3

import os

# python-for-android always runs the file named main.py as the entry point, so
# on Android this desktop launcher is what gets executed -- not android_main.py
# (which is bundled too, but never invoked by the bootstrap). Dispatch to the
# QML-only mobile entry point BEFORE importing l5r.main, which would pull in the
# desktop QWidget UI and its non-mobile deps (lxml, etc.). ANDROID_ARGUMENT is
# set by the p4a bootstrap.
if 'ANDROID_ARGUMENT' in os.environ:
    os.environ.setdefault('QT_API', 'pyside6')
    import android_main
    raise SystemExit(android_main.main())

if 'QT_API' not in os.environ:
    os.environ['QT_API'] = 'pyqt6'

import l5r
import l5r.main

print("Starting L5R Character Manager...")
print(f"QT API: {os.environ['QT_API']}")

l5r.main.main()
