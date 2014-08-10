call c:\python27\scripts\pylint -E --rcfile pylint.rc l5rcm.py
call c:\python27\scripts\pylint -E --rcfile pylint.rc l5rcmcore
call c:\python27\scripts\pylint -E --rcfile pylint.rc autoupdate
call c:\python27\scripts\pylint -E --rcfile pylint.rc exporters
call c:\python27\scripts\pylint -E --rcfile pylint.rc widgets
call c:\python27\scripts\pylint -E --rcfile pylint.rc osutil
call c:\python27\scripts\pylint -E --rcfile pylint.rc rules
call c:\python27\scripts\pylint -E --rcfile pylint.rc dal
call c:\python27\scripts\pylint -E --rcfile pylint.rc dialogs
call c:\python27\scripts\pylint -E --rcfile pylint.rc models
call c:\python27\scripts\pylint -E --rcfile pylint.rc sinks

FOR %%f in (pylint_*.txt) do (
	echo %%~ff
	if %%~zf LEQ 0 (
    	del "%%~ff"
	)
)