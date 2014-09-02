@echo off

set root=%~dp0

del /S /F /Q .\dist\*.*

REM GO TO SOURCE DIR
cd ..\..\..\src

REM BUILD EXECUTABLE
python setup.py py2exe

REM COPY RESOURCES
xcopy /Y /E /C /I /R share\* dist\share\

REM COPY THIRD PARTY TOOLS
xcopy /Y /E /C /I /R ..\tools\pdftk\* dist\tools\

copy ..\LICENSE.GPL3 dist\

REM MOVE DIST DIRECTORY IN THE DEPLOY DIR
echo move /Y .\dist "%root%"
move /Y .\dist "%root%"

REM DELETE BUILD DIRECTORY
del /S /F /Q .\build\*.*

cd %root%
