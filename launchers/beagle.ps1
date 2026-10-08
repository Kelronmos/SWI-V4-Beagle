$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = $Root
Set-Location $Root
Write-Host "SWI V4 Beagle — AUDIT first. AUTHORIZED=NO"
python -m swi_beagle audit --roots (Split-Path -Parent $Root)
