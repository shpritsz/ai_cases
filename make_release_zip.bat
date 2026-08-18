@echo off
setlocal

set ROOT=%~dp0
cd /d "%ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File ".\make_release_zip.ps1"
if errorlevel 1 exit /b 1

echo Release archive created in releases\
exit /b 0
