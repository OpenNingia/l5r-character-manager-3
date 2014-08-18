#!/bin/bash
cwd=${PWD}
printf '%s %s\n' "${PWD}" "$1"
cd $1
zip -r -1 $2.l5rcmpack ./* -x *.svn*
mv $2.l5rcmpack ../
cd $cwd

