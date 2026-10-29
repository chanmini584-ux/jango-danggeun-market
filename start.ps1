$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path .venv/Scripts/python.exe)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed" }
}
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& ./.venv/Scripts/python.exe manage.py migrate
if ($LASTEXITCODE -ne 0) { throw "Database migration failed" }
& ./.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload
