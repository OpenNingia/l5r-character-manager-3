@echo off

set root=%~dp0

REM COPY RESOURCES
xcopy /Y /E /C /I /R ..\..\..\l5r\share\* common\share\

REM COPY THIRD PARTY TOOLS
xcopy /Y /E /C /I /R ..\..\pdftk\* common\tools\

copy ..\..\..\LICENSE.GPL3 common\

cd %root%
