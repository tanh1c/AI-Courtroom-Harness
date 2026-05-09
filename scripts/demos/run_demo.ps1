param(
    [switch]$OpenPreview,
    [string]$ReviewerName = "Codex Demo Reviewer"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$demoScript = Join-Path $repoRoot "scripts\demos\run_demo.py"

if (-not (Test-Path $pythonExe)) {
    throw "Missing repo-local Python environment at $pythonExe"
}

$arguments = @($demoScript, "--reviewer-name", $ReviewerName)
if ($OpenPreview) {
    $arguments += "--open-preview"
}

& $pythonExe @arguments
