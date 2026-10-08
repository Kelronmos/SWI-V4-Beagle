@echo off
set ROOT=%~dp0..
cd /d "%ROOT%"
set PYTHONPATH=%ROOT%;%PYTHONPATH%
echo SWI V4 Beagle — AUDIT first. AUTHORIZED=NO
python -m swi_beagle audit --roots "%ROOT%\.."
if errorlevel 1 py -3 -m swi_beagle audit --roots "%ROOT%\.."
