#!/bin/bash
rm -rf ../dist
cxfreeze ../l5rcm.py --include-modules encodings.hex_codec --target-dir ../dist
cp -r ../share ../dist
mkdir ../dist/tools
cp /usr/bin/pdftk ../dist/tools/pdftk
