# Run the program from sources

## getting the sources

### first of all, clone the repo
`git clone https://github.com/OpenNingia/l5r-character-manager-3.git`

### switch to develop branch
master branch is often outdated, so you want to get the develop branch
`git checkout develop`

### getting the dependencies
the simplest way is to run

`pip install -r requirements.txt`

otherwise you can install them one by one
`pip install -U PySide'
`pip install -U asq'
`pip install -U lxml'

### note for windows users
You will need a basic compiler in order to build some of the dependencies. I recommend getting this one:
http://www.microsoft.com/en-us/download/details.aspx?id=44266

You will also need to install Python 2.7.x from here:
https://www.python.org/downloads/

### note for linux users
You will need to download one more dependency, the pdf toolkit, needed to export the character sheets.
Use you package manager to install the `pdftk` package. On debian systems run:

`apt-get install pdftk` or `aptitude install pdftk`

### finally you launch the program
`cd l5r`
`python main.py`

