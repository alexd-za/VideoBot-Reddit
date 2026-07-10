[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GuardianArgs
)

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "guardian.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $ScriptPath @GuardianArgs
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $ScriptPath @GuardianArgs
    exit $LASTEXITCODE
}

Write-Error "Python 3 was not found. Install Python 3.10 or newer, or make py/python available on PATH."
exit 2
