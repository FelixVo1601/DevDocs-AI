# One-command local development (Windows PowerShell)
# Usage (from repo root):  .\scripts\dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> DevDocs AI local stack" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example"
}
if (-not (Test-Path "frontend/.env")) {
  Copy-Item "frontend/.env.example" "frontend/.env"
  Write-Host "Created frontend/.env from frontend/.env.example"
}

Write-Host "==> Starting Postgres (Docker Compose)"
docker compose up -d db

$venvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$venvUvicorn = Join-Path $Root "backend\.venv\Scripts\uvicorn.exe"
$venvAlembic = Join-Path $Root "backend\.venv\Scripts\alembic.exe"

if (-not (Test-Path $venvPython)) {
  Write-Host "==> Creating backend venv"
  python -m venv "backend\.venv"
}

Write-Host "==> Installing backend deps + migrating"
& $venvPython -m pip install -q -r "backend\requirements.txt"
Push-Location "backend"
& $venvAlembic upgrade head
Pop-Location

if (-not (Test-Path "frontend\node_modules")) {
  Write-Host "==> Installing frontend deps"
  Push-Location "frontend"
  npm install
  Pop-Location
}

Write-Host "==> Starting API on http://localhost:8001"
Start-Process -FilePath $venvUvicorn -ArgumentList @(
  "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8001"
) -WorkingDirectory (Join-Path $Root "backend") -WindowStyle Normal

Write-Host "==> Starting UI on http://localhost:5173"
Start-Process -FilePath "npm" -ArgumentList @("run", "dev", "--", "--host", "localhost", "--port", "5173") -WorkingDirectory (Join-Path $Root "frontend") -WindowStyle Normal

Write-Host ""
Write-Host "Ready:" -ForegroundColor Green
Write-Host "  UI:      http://localhost:5173"
Write-Host "  Register http://localhost:5173/register"
Write-Host "  App:     http://localhost:5173/app  (requires login)"
Write-Host "  API:     http://localhost:8001/docs"
Write-Host "  Health:  http://localhost:8001/health"
Write-Host ""
Write-Host "Use localhost (not 127.0.0.1) in the browser so the session cookie works."
