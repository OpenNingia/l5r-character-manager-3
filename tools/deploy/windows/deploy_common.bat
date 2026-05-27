@echo off

set root=%~dp0

REM COPY RESOURCES
xcopy /Y /E /C /I /R ..\..\..\l5r\share\* common\share\

copy ..\..\..\LICENSE.GPL3 common\

cd %root%
