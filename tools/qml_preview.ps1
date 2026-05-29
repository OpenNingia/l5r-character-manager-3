# Reusable offscreen QML dialog screenshotter for the L5RCM QML UI.
# Wraps tools/qml_preview.py with the Qt environment it needs (offscreen
# platform + software scene graph so grabWindow works headless + Fusion
# controls style, matching the running app). Produces a PNG you can open
# or inspect; no datapacks or real app bootstrap required.
#
# Examples:
#   tools\qml_preview.ps1 --dialog InscribePerkDialog --call 'present("merit")' --size 980x720 --out merit.png
#   tools\qml_preview.ps1 --dialog FamilyChooserDialog --call open --out family.png
#   tools\qml_preview.ps1 --dialog BuySkillDialog --call open --out skill.png
#   tools\qml_preview.ps1 --qml path\to\Standalone.qml --out s.png
#
# All arguments are forwarded verbatim to tools/qml_preview.py
# (run that with -h for the full option list).
$env:QT_API = 'pyqt6'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:QT_QUICK_BACKEND = 'software'
$env:QT_QUICK_CONTROLS_STYLE = 'Fusion'

$script = Join-Path $PSScriptRoot 'qml_preview.py'
python $script @args
exit $LASTEXITCODE
