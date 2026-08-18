@echo off
setlocal

set ROOT=%~dp0
cd /d "%ROOT%"

set PYTHON=%ROOT%.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo Python executable not found: %PYTHON%
  exit /b 1
)

set CASE_FILE=
for %%F in (matsp*II.json) do if not defined CASE_FILE set CASE_FILE=%%F
if "%CASE_FILE%"=="" (
  echo Could not find case JSON file matching matsp*II.json
  exit /b 1
)

"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON%" -m PyInstaller --noconfirm --console --name ai_cases_chatbot chatbot.py ^
  --add-data "config.json;." ^
  --add-data "instructions.json;." ^
  --add-data "%CASE_FILE%;." ^
  --add-data ".env.example;."
if errorlevel 1 exit /b 1

copy /Y ".env.example" "dist\ai_cases_chatbot\.env.example" >nul

echo Build complete. Share dist\ai_cases_chatbot\ with your colleague.
echo Your colleague must create .env beside ai_cases_chatbot.exe and set API_KEY.
exit /b 0
