GETTING THE SOURCES

clone the repository
svn checkout http://l5rcm.googlecode.com/svn/trunk/ l5rcm-read-only

or you can clone a release tag instead
svn checkout http://l5rcm.googlecode.com/svn/tags/v3.7.1 l5rcm-3-7.1

GETTING THE DEPENDENCIES

* python2       >= 2.6   ( 2.7.3 recommended )
* python-pyside >= 1.1.0 ( 1.1.1 if l5rcm version < 3.7, 1.1.2 recommended with 3.7+ )
* pdftk                  ( needed for pdf export )

RUN

python l5rcm.py

GETTING DATAPACKS

The software alone is not useful. You need game data in order to create and
manage your characters.

Game data is provided through packages named "datapacks" that are downloadable
from the project website:
	https://code.google.com/p/l5rcm/downloads/list
	
Each datapack contains the game data equivalent of a L5R book with the exception
of the "community data pack" that is a collection of game data that doesn't fit
anywhere else (yet.)

Be aware that the game and the game data are still under active development
and may not be complete.

INSTALLING DATAPACKS

The preferred way to install datapacks is from the application Data menu.
Click on Data -> Import datapack... and select the file to import.
Tipically datapacks have the ".l5rcmpack" extension.

This operation is only needed the first time and on each datapack update.

On Windows you can also doubleclick the datapack to do so.	

BROWSING / EDITING DATAPACKS

If you wonder what a datapack contains you can rename the extension to ".zip"
and extract with your preferred application ( e.g. 7Zip, unzip, Archive Roller, etc... )

The "manifest" file ( without extension ) describe the name and contents of the datapack
and contains information useful to the application and the user ( e.g. the version number ).

The ".xml" files contains the game data itself. You can try to modify the data
and re-import the pack ( zip the folder -> rename to .l5rcmpack ) to see the changes.

If you mess up you can just redownload the pack and re-import it.

CONTRIBUITE

If you make a modification to a datapack that add value to the application
I would be glad to accept it as contribute to the project :)

Please send it to me or file a bug here:
https://code.google.com/p/l5rcm/issues/list

