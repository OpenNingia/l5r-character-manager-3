@echo off
cd %1
"c:\Program Files\7-Zip\7z.exe" a -r -tzip -y %2.l5rcmpack .\*
move %2.l5rcmpack ..\%2.l5rcmpack
cd %~dp0