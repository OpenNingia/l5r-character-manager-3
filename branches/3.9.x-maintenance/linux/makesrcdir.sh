#!/bin/bash
cwd=${PWD}

USR=./tmp/usr
OPT=./tmp/opt
INST=${OPT}/l5rcm

# remove old files
rm $1.tar.gz
rm $1.deb

# remove backups
find ./ | grep '~' | xargs rm

# make source tarball
tar -vzcf $1.tar.gz --exclude-vcs -X exclude_from_tarball --exclude-backups --exclude-caches ../

# remove old directory
# should ask for root password
rm -rf ./tmp

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

cp -r ./DEBIAN ./tmp
rm -rf ./tmp/DEBIAN/.svn

# change GID
chown -R root:root ${USR}
chown -R root:root ${OPT}

# fix permission
find ./tmp -type d | xargs chmod 755
find ${OPT} -type f | xargs chmod 644
find ${USR} -type f | xargs chmod 644

chmod +x ${USR}/bin/l5rcm

dpkg-deb -b ./tmp $1.deb

# give my debs!
chown $(whoami):$(whoami) $1*
cd $cwd
