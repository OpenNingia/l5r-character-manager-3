# Run the program from sources

## Getting the sources

### First of all, clone the repo

[![Build Status](https://travis-ci.org/OpenNingia/l5r-character-manager-3.svg)](https://travis-ci.org/OpenNingia/l5r-character-manager-3)

```bash
git clone https://github.com/OpenNingia/l5r-character-manager-3.git
cd ./l5r-character-manager-3/
git checkout develop
```

### Create a virtual environment
Install python3-venv and create a new virtual environment for python.

```bash
apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
```

### Installing the dependencies
Before running the program you need to install the dependencies:
Some of them can be installed using pip:

```bash
pip install -r requirements.txt
pip install git+https://github.com/OpenNingia/l5rcm-data-access.git@master
```

Windows users can download PyQt5 binaries from here:
https://www.riverbankcomputing.com/software/pyqt/download

### Note for Windows users
You will need a basic compiler in order to build some of the dependencies (mainly lxml). 

You will also need to install Python 3.6.x from here:

https://www.python.org/downloads/

### Note for Linux users
You will need to download one more dependency, the pdf toolkit, needed to export the character sheets.
Use you package manager to install the `pdftk` package. I recommend this version:

https://gitlab.com/pdftk-java/pdftk

### Finally you launch the program

```
cd l5r
python3 main.py
```

## Getting the Datapacks
The software alone is not useful. You need game data in order to create and
manage your characters.

Game data is provided through packages named "datapacks" that are downloadable
from the project website:

http://sourceforge.net/projects/l5rcm/files/Data%20Packs/

however you might want to compile the datapack yourself; in order to do so follow these simple instructions.

### Clone the datapack repository
The data pack sources are hosted in a different repo, to get them run:

```
git clone https://github.com/OpenNingia/l5rcm-data-packs.git
git checkout develop
```

### Build the datapacks
In the repo there is a convenience script that builds all the datapacks

```
cd scripts
python make_all_packs.py
```

### Installing the datapacks
The preferred way to install datapacks is from the application menu.
Click on **Gear menu -> Import datapack...** and select the files to import.
Tipically datapacks have the `.l5rcmpack` extension.
This operation is only needed the first time and on each datapack update.

If the program was installed using the setup and/or debian file then you can also doubleclick the datapack files.

## CONTRIBUITE

If you make a modification to the software or datapack that add value to the application
don't esitate to share it!

Please submit a pull request to the relative repository :)
