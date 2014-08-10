# pyqticonloader.py

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Authors: Federico Brega, Pierluigi Villani
# Inspired from C++ code by Qt software qticonloader.cpp
# Adapted to PySide by Daniele Simonetti

import os
from PySide.QtCore import *
from PySide.QtGui import *

class QIconTheme:
    def __init__(self, dirList, parents):
        self._dirList = dirList
        self._parents = parents
        self.valid = True
    def dirList(self):
        return self._dirList
    def parents(self):
        return self._parents
    def isValid(self):
        return self.valid

class QtIconLoaderImplementation():
    def __init__(self):
        self._themeName = None
        self._iconDirs = None
        self._themeList = {}

        self.lookupIconTheme()

    def lookupIconTheme(self):
        #begin ifdef Q_WS_X11
        #self._themeName
        dataDirs = QFile.decodeName(os.getenv("XDG_DATA_DIRS"))
        if len(dataDirs) == 0:
            dataDirs = "/usr/local/share/:/usr/share"
        dataDirs = QDir.homePath() + "/:" + dataDirs
        self._iconDirs = dataDirs.split(":")
        #If we are running gnome use gconftool runtime to get theme name
        if os.getenv("DESKTOP_SESSION") == "gnome" or  os.getenv("GNOME_DESKTOP_SESSION_ID"):
            if not self._themeName:
                import subprocess
                subpr = subprocess.Popen(["gconftool", "--get", "/desktop/gnome/interface/icon_theme"], stdout=subprocess.PIPE)
                self._themeName = subpr.communicate()[0].strip()
            if not self._themeName:
                self._themeName = "gnome"
            return
        #KDE and others
        if not dataDirs:
            dataDirs = "/usr/local/share/:/usr/share/"
        dataDirs += ":" +kdeHome() + "/share"
        dataDirs = QDir.homePath() + "/:" + dataDirs
        kdeDirs = str(QFile.decodeName(os.getenv("KDEDIRS"))).split(':')
        for dirName in kdeDirs:
            dataDirs += ":" + dirName + "/share"
        fileInfo4 = QFileInfo("/usr/share/icons/default.kde4")
        fileInfo = QFileInfo("/usr/share/icons/default.kde")
        if fileInfo.exists() or fileInfo4.exists():
            if fileInfo4.exists():
                fileInfo = fileInfo4
            dir_ = QDir(fileInfo.canonicalFilePath())
            defaultTheme = dir_.dirName()
        else:
            if _kdeVersion() >= 4:
                defaultTheme  = "oxygen"
            else:
                defaultTheme = "crystalsvg"
        configpath = kdeHome() + "/share/config/kdeglobals"
        settings = QSettings(configpath, QSettings.IniFormat)
        settings.beginGroup("Icons")
        self._themeName = str(settings.value("Theme", defaultTheme))
        #endif
    def findIcon(self, size, name):
        pixmap = QPixmap()
        pixmapName = "$qt" + name + str(size)
        if QPixmapCache.find(pixmapName, pixmap):
            return pixmap
        if self._themeName:
            visited = []
            pixmap = self.findIconHelper(size, self._themeName, name, visited)
            QPixmapCache.insert(pixmapName, pixmap)
        return pixmap
    def lookupIconHelper(self, msize, themeName, iconName, visited):
        pass
    def parseIndexFile(self, themeName):
        themeIndex = QFile()
        parents = []
        dirList = {}

        i = 0
        while i<len(self._iconDirs) and not themeIndex.exists():
            if self._iconDirs[i].startswith(QDir.homePath()):
                contentDir = "/.icons/"
            else:
                contentDir = "/icons/"
            themeIndex.setFileName(self._iconDirs[i] + contentDir + themeName + "/index.theme")
            i += 1
        if themeIndex.exists():
            indexReader = QSettings(themeIndex.fileName(), QSettings.IniFormat)
            for key in indexReader.allKeys():
                if key.endswith("/Size"):
                    size = indexReader.value(key)		    
                    if len(size) > 1 and size[1]:
                        if size[0] not in dirList:
                            dirList[size[0]] = []
                        dirList[size[0]].append(key[:-5])
            parents = indexReader.value("Icon Theme/Inherits") or []
            if type(parents) != type([]):
                parents = [parents]
            
        if _kdeVersion() >= 3:
            fileInfo = QFileInfo("/usr/share/icons/default.kde4")
            dir_ = QDir(fileInfo.canonicalFilePath())
            if not dir_.exists():
                fileinfo = QFileInfo("/usr/share/icons/default.kde")
                dir_ = QDir(fileInfo.canonicalFilePath())

            if dir_.exists():
                defaultKDETheme = dir_.dirName()
            elif _kdeVersion() == 3:
                defaultKDETheme = "crystalsvg"
            else:
                defaultKDETheme = "oxygen"

            if defaultKDETheme not in parents and themeName!=defaultKDETheme:
                parents.append(defaultKDETheme)
        elif len(parents) == 0 and themeName!="hicolor":
            parents.append("hicolor")
        theme = QIconTheme(dirList, parents)
        return theme
    def findIconHelper(self, size, themeName, iconName, visited):
        theme = None
        pixmap = QPixmap()
        if themeName:
            visited.append(themeName)
            if themeName in self._themeList:
                theme = self._themeList[themeName]
            if not theme or not theme.isValid():
                theme = self.parseIndexFile(themeName)
                self._themeList[themeName] = theme
            if not theme.isValid():
                return QPixmap()
            dirList = theme.dirList()
            subDirs = []
            for key in dirList:
                if key==size:
                    subDirs = dirList[key]
                    break
            for iconDir in self._iconDirs:
                for subDir in subDirs:
                    if iconDir.startswith(QDir.homePath()):
                        contentDir = ".icons/"
                    else:
                        contentDir = "/icons/"
                    fileName = iconDir + contentDir \
                                        + themeName + "/" + subDir \
                                        + "/" +  iconName
                    file_ = QFile(fileName)
                    if file_.exists():
                        pixmap.load(fileName)
                    if not pixmap.isNull():
                        #break
                        return pixmap
            if pixmap.isNull():
                parents = theme.parents()
                i = 0
                while pixmap.isNull() and i<len(parents):
                    parentTheme = parents[i].strip()
                    if parentTheme not in visited:
                        pixmap = self.findIconHelper(size, parentTheme, iconName, visited)
                    i += 1
        return pixmap

loader = None
def icon(name, fallbackIcon=QIcon(),  iconSizes=[16, 24, 32, 48, 64]):
    global loader
    icon = QIcon()
    #TODO: begins ifdef Q_WS_X11
    if not loader: loader = QtIconLoaderImplementation()
    for size in iconSizes:
#        pix = QtIconLoaderImplementation().findIcon(size, name + ".png")
        pix = loader.findIcon(size, name + ".png")
        icon.addPixmap( pix )
    #ends idef Q_WS_X11
    if icon.isNull():
        icon = fallbackIcon
    return icon

_version = None
def _kdeVersion():
    global _version
    ver = os.getenv("KDE_SESSION_VERSION")
    if ver: _version = int(ver)
    else: _version = 0
    return _version

kdeHomePath = ""
def kdeHome():
    global kdeHomePath
    if not kdeHomePath:
        kdeHomePath = QFile.decodeName(os.getenv("KDEHOME"))
        if not kdeHomePath:
            kdeSessioneVersion = _kdeVersion()
            homeDir = QDir(QDir.homePath())
            kdeConfDir = "/.kde"
            #if kdeSessioneVersion==4 and homeDir.exists(".kde4"):
                #kdeConfDir = "/.kde4"
            kdeHomePath = QDir.homePath() + kdeConfDir
    return kdeHomePath
