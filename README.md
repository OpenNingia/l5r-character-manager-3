# Run the program from sources

## Getting the sources

### First of all, clone the repo
`git clone https://github.com/OpenNingia/l5r-character-manager-3.git`

### Switch to develop branch
master branch is often outdated, so you want to get the develop branch by running

`git checkout develop`

### Installing the dependencies
the simplest way is to run

`pip install -r requirements.txt`

otherwise you can install them one by one
`pip install -U PySide'
`pip install -U asq'
`pip install -U lxml'

### Note for Windows users
You will need a basic compiler in order to build some of the dependencies. I recommend getting this one:
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
`cd l5r`
`python main.py`

