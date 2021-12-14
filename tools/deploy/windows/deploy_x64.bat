@echo off

echo "> START BUILD x64 APP"

set root=%~dp0
set dist="%root%\bin_x64"

echo "* deleting old binaries"
del /S /F /Q %dist%\*.* 1> NUL

REM GO TO SOURCE DIR
cd ..\..\..\l5r

REM CLEAN BUILD
del /S /F /Q .\dist\*.* 1> NUL

REM BUILD EXECUTABLE
echo "* building new binaries"
python setup.py py2exe 1> NUL

REM COPY DIST DIRECTORY IN THE DEPLOY DIR
echo "* copying binaries to deployment directory"
xcopy /Y /I .\dist\*.* %dist%\

REM DELETE BUILD DIRECTORY
echo "* deleting intermediate directories"
del /S /F /Q .\build\*.* 1> NUL
del /S /F /Q .\dist\*.* 1> NUL

cd %root%
