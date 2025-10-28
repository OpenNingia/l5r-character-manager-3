#!/usr/bin/python3

import os

if 'QT_API' not in os.environ:
    os.environ['QT_API'] = 'pyqt6'

import l5r
import l5r.main

print("Starting L5R Character Manager...")
print(f"QT API: {os.environ['QT_API']}")

l5r.main.main()
