# Run the program from sources

## Getting the sources

### First of all, clone the repo

`git clone https://github.com/OpenNingia/l5r-character-manager-3.git`

### Switch to develop branch
master branch is often outdated, so you want to get the develop branch by running

[![Build Status](https://travis-ci.org/OpenNingia/l5r-character-manager-3.svg)](https://travis-ci.org/OpenNingia/l5r-character-manager-3)

`git checkout -b origin/develop`

### Installing the dependencies
Before running the program you need to install the dependencies:
Some of them can be installed using pip:

```bash
pip install -U asq
pip install -U lxml
```

Then you need to install PyQt4. On a Debian system run:

```bash
apt-get install python-sip python-qt4
```

Windows users can download PyQt4 binaries from here:
https://www.riverbankcomputing.com/software/pyqt/download

### Note for Windows users
You will need a basic compiler in order to build some of the dependencies (mainly lxml). I recommend getting this one:

http://www.microsoft.com/en-us/download/details.aspx?id=44266

You will also need to install Python 2.7.x from here:

https://www.python.org/downloads/

### Note for Linux users
You will need to download one more dependency, the pdf toolkit, needed to export the character sheets.
Use you package manager to install the `pdftk` package. On debian systems run:

`apt-get install pdftk` or `aptitude install pdftk`

### Note for MacOSX users
I don't actually own a Mac, so I cannot test it, however these instruction should work also on OSX.
You might need to manually download the pdf toolkit from here:

https://www.pdflabs.com/tools/pdftk-server/

then place the executable in the system path.

### Finally you launch the program

```
cd l5r
python main.py
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
