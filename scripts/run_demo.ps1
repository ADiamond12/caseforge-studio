param(
    [switch]$SkipInstall,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $SkipInstall) {
    python -m pip install -e .
}

if (-not $SkipTests) {
    python -m unittest discover -s tests -v
}

$briefPath = "examples/briefs/ops-copilot.md"

Write-Host ""
Write-Host "Previewing deterministic blueprint from $briefPath"
python -m caseforge create --brief-file $briefPath --preset product --preview --json

Write-Host ""
Write-Host "Persisting reviewer-ready blueprint artifacts"
python -m caseforge create --brief-file $briefPath --preset product

Write-Host ""
Write-Host "Recent saved runs"
python -m caseforge list --limit 5

Write-Host ""
Write-Host "Open the local app with:"
Write-Host "python -m caseforge serve --host 127.0.0.1 --port 8127"
Write-Host "Then visit http://127.0.0.1:8127 and compare two saved runs."
