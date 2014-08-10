#!/bin/bash
# Make sure only root can run our script
if [ $EUID -ne 0 ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

if command -v rsvg-convert 2>/dev/null; then
    echo "rsvg-convert found"
else
   echo "This script require rsvg-convert" 1>&2
   echo "install librsvg2-bin and try again" 1>&2
   exit 1
fi

if command -v rst2man 2>/dev/null; then
    echo "rst2man found"
else
   echo "This script require rst2man" 1>&2
   echo "install docutils-common and try again" 1>&2
   exit 1
fi

APP_NAME=`grep -E '^APP_NAME\s*=\s*' '../l5rcmcore/__init__.py' | cut -d\' -f2`
APP_VER=`grep '^APP_VERSION\s*=\s*' '../l5rcmcore/__init__.py' | cut -d\' -f2`
echo 'APP_VERSION:' $APP_NAME'_'$APP_VER

DEB_VER_FLL=`grep '^Version:\s' './DEBIAN/control' | cut -d\   -f2`
echo 'OLD_DEBIAN_VERSION:' $DEB_VER_FLL

DEB_VER=`echo $DEB_VER_FLL | cut -d- -f1`

DEB_CNT=`echo $DEB_VER_FLL | cut -d- -f2`

if [ $APP_VER == $DEB_VER ]
then
    DEB_CNT=`expr $DEB_CNT + 1`
else
    DEB_VER=$APP_VER
    DEB_CNT=1
fi

NEW_DEB_VER_FLL=$DEB_VER-$DEB_CNT
echo 'NEW_DEBIAN_VERSION:' $NEW_DEB_VER_FLL

sed -i.bak -e 's/^Version: '$DEB_VER_FLL'/Version: '$NEW_DEB_VER_FLL'/' ./DEBIAN/control

./makesrcdir.sh $APP_NAME'-'$NEW_DEB_VER_FLL'_all'
