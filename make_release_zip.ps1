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

$configPath = Join-Path $root "config.json"
$instructionsPath = Join-Path $root "instructions.json"
$envExamplePath = Join-Path $root ".env.example"

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade failed with exit code $LASTEXITCODE"
}

& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed with exit code $LASTEXITCODE"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tempDist = Join-Path $root ("dist_zip_" + $timestamp)
$tempBuild = Join-Path $root ("build_zip_" + $timestamp)

& $python -m PyInstaller --noconfirm --console --name ai_cases_chatbot chatbot.py `
  --distpath $tempDist `
  --workpath $tempBuild `
  --specpath $tempBuild `
    --add-data "$configPath;." `
    --add-data "$instructionsPath;." `
    --add-data "$($caseFile.FullName);." `
    --add-data "$envExamplePath;."
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

Copy-Item ".env.example" (Join-Path $tempDist "ai_cases_chatbot\.env.example") -Force

$releasesDir = Join-Path $root "releases"
if (-not (Test-Path $releasesDir)) {
    New-Item -ItemType Directory -Path $releasesDir | Out-Null
}

$zipName = "ai_cases_chatbot-win64-$timestamp.zip"
$zipPath = Join-Path $releasesDir $zipName

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path (Join-Path $tempDist "ai_cases_chatbot") -DestinationPath $zipPath -Force

if (Test-Path $tempDist) {
    Remove-Item $tempDist -Recurse -Force
}
if (Test-Path $tempBuild) {
    Remove-Item $tempBuild -Recurse -Force
}

Write-Host "Release archive created: $zipPath"
