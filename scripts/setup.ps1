$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.10+ is required." }
& .\.venv\Scripts\python.exe -m pip install -e ".[real,validation]"
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }
& .\.venv\Scripts\python.exe scripts/build_powerbi.py
if ($LASTEXITCODE -ne 0) { throw "PBIP generation failed." }
Write-Host "Open powerbi\F1 Telemetry Lab.pbip in Power BI Desktop and click Refresh."
