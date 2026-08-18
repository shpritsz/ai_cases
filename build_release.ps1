$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python executable not found: $python"
}

$caseFile = Get-ChildItem -Path $root -Filter "matsp*II.json" | Select-Object -First 1
if (-not $caseFile) {
  throw "Could not find case JSON file matching matsp*II.json"
}

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  throw "pip upgrade failed with exit code $LASTEXITCODE"
}

& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
  throw "pip install failed with exit code $LASTEXITCODE"
}

& $python -m PyInstaller --noconfirm --console --name ai_cases_chatbot chatbot.py `
  --add-data "config.json;." `
  --add-data "instructions.json;." `
  --add-data "$($caseFile.Name);." `
  --add-data ".env.example;."
if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

Copy-Item ".env.example" "dist\ai_cases_chatbot\.env.example" -Force

Write-Host "Build complete. Share dist\ai_cases_chatbot\ with your colleague."
Write-Host "Your colleague must create .env beside ai_cases_chatbot.exe and set API_KEY."
