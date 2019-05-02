import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["lxml._elementpath"], "excludes": ["tests"], "includes": ["l5r.widgets.iconloader"], "build_exe": "tools/deploy/windows/dist"}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "l5rcm",
        version = "3.11",
        description = "L5R RPG character manager",
        options = {"build_exe": build_exe_options},
        executables = [Executable(
			"main.py", 
			#targetDir="tools/deploy/windows/dist",
			targetName="l5rcm.exe",
			base=base, 
			icon="tools/deploy/windows/l5rcm.ico")])