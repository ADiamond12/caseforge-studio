param(
    [switch]$SkipInstall,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Assert-NativeSuccess {
    param([string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

if (-not $SkipInstall) {
    python -m pip install -e .
    Assert-NativeSuccess "Install editable package"
}

if (-not $SkipTests) {
    python -m unittest discover -s tests -v
    Assert-NativeSuccess "Run unittest suite"
}

$briefPath = "examples/briefs/intralogistics-commissioning-planner.md"
$alternateBriefPath = "examples/briefs/ops-copilot.md"

if ($env:CASEFORGE_OUTPUT_ROOT) {
    Write-Host "Using output root: $env:CASEFORGE_OUTPUT_ROOT"
}

Write-Host ""
Write-Host "Previewing deterministic blueprint from $briefPath"
python -m caseforge create --brief-file $briefPath --preset product --preview --json
Assert-NativeSuccess "Preview deterministic blueprint"

Write-Host ""
Write-Host "Persisting reviewer-ready blueprint artifacts"
$primaryJson = python -m caseforge create --brief-file $briefPath --preset product --json
Assert-NativeSuccess "Persist primary blueprint"
$primary = $primaryJson | ConvertFrom-Json
Write-Host "Primary run: $($primary.slug)"
Write-Host "Export manifest: $($primary.manifestPath)"

Write-Host ""
Write-Host "Persisting alternate run for comparison"
$alternateJson = python -m caseforge create --brief-file $alternateBriefPath --preset full-stack --json
Assert-NativeSuccess "Persist alternate blueprint"
$alternate = $alternateJson | ConvertFrom-Json
Write-Host "Alternate run: $($alternate.slug)"

Write-Host ""
Write-Host "Comparing saved runs"
python -m caseforge compare $primary.slug $alternate.slug --markdown
Assert-NativeSuccess "Compare saved runs"

Write-Host ""
Write-Host "Recent saved runs"
python -m caseforge list --limit 5
Assert-NativeSuccess "List recent saved runs"

Write-Host ""
Write-Host "Open the local app with:"
Write-Host "python -m caseforge serve --host 127.0.0.1 --port 8127"
Write-Host "Then visit http://127.0.0.1:8127 and compare two saved runs."
