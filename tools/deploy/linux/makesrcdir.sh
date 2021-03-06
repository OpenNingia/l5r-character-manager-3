#!/bin/bash
cwd=${PWD}

USR=./tmp/usr
OPT=./tmp/opt
INST=${OPT}/l5rcm
SRC=./src
TMPSRC=./tmpsrc

# remove old files
rm $1.tar.gz
rm $1.deb

# remove backups
find ./ | grep '~' | xargs rm

# remove old directory
# should ask for root password
rm -rf ./tmp
rm -rf ./src
rm -rf ./tmpsrc

# make source dir
mkdir -p ${SRC}
mkdir -p ${TMPSRC}

# get l5rdal
wget https://github.com/OpenNingia/l5rcm-data-access/archive/develop.zip -O ${TMPSRC}/l5rdal.zip
unzip ${TMPSRC}/l5rdal.zip -d ${TMPSRC}/
cp -r ${TMPSRC}/l5rcm-data-access-develop/l5rdal ${SRC}/
# copy app source
cp -r ../../../l5r/ ${SRC}

# make source tarball
cd ${SRC}
tar -vzcf ../$1.tar.gz --exclude-vcs -X ../exclude_from_tarball --exclude-backups --exclude-caches ./
cd ..

# make working dir
mkdir -p ${INST}
mkdir -p ${INST}/mime
mkdir -p ${USR}/bin
mkdir -p ${USR}/share/man/man1
mkdir -p ${USR}/share/doc/l5rcm
mkdir -p ${USR}/share/applications
mkdir -p ${USR}/share/pixmaps
mkdir -p ${USR}/share/icons/hicolor/scalable/apps

tar -vxzf $1.tar.gz -C ${INST}

# rasterize svn icon
ICON_SIZES="16 22 24 32 48 64 128 256"
for size in ${ICON_SIZES}
do
    echo "Create icon: ${size}x${size}"
    TRG_DIR=${USR}/share/icons/hicolor/${size}/apps
    mkdir -p ${TRG_DIR}
    rsvg-convert -h ${size} -w ${size} ./l5rcm.svg > ${TRG_DIR}/l5rcm.png
done

cp ./l5rcm.png ${USR}/share/pixmaps
cp ./l5rcmpack.png ${USR}/share/pixmaps
cp ./l5rcm.svg ${USR}/share/icons/hicolor/scalable/apps
cp ./l5rcm.desktop ${USR}/share/applications
cp ./l5rcm ${USR}/bin

# man page
rst2man ./l5rcm.rst ${USR}/share/man/man1/l5rcm.1
gzip -9 ${USR}/share/man/man1/l5rcm.1

# mime files
cp ./*.xml ${OPT}/l5rcm/mime

# copyright file
cp ./copyright ${USR}/share/doc/l5rcm/

# changelog
cp ./changelog ${USR}/share/doc/l5rcm/changelog.Debian
gzip -9 ${USR}/share/doc/l5rcm/changelog.Debian

# requirements
cp ./requirements.txt ${INST}/

cp -r ./DEBIAN ./tmp
rm -rf ./tmp/DEBIAN/.svn
rm -rf ./tmp/DEBIAN/.git

# change GID
fakeroot chown -R root:root ${USR}
fakeroot chown -R root:root ${OPT}

# fix permission
fakeroot find ./tmp -type d | xargs chmod 755
fakeroot find ${OPT} -type f | xargs chmod 644
fakeroot find ${USR} -type f | xargs chmod 644

fakeroot chmod +x ${USR}/bin/l5rcm

fakeroot dpkg-deb -b ./tmp $1.deb

# give my debs!
fakeroot chown $(whoami):$(whoami) $1*
cd $cwd
