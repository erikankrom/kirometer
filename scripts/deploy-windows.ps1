# Run from PowerShell; argument forwarding preserves paths containing spaces.
$ErrorActionPreference = 'Stop'
$DeploymentScript = Join-Path $PSScriptRoot 'deploy.py'
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $DeploymentScript @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $DeploymentScript @args
} else {
    Write-Error 'Python 3.10 or newer is required. Install Python, then rerun this command.'
    exit 1
}
exit $LASTEXITCODE
