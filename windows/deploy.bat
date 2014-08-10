@echo off
cd ..

REM DELETE PREVIOUS BUILD
del /S /F /Q .\build\*.*
del /S /F /Q .\dist\*.*

python setup.py py2exe

xcopy /Y /E /C /I /R share\* dist\share\
xcopy /Y /E /C /I /R tools\* dist\tools\

copy LICENSE.GPL3 dist\

cd windows
