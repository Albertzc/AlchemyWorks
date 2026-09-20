[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$InstanceName,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TargetRoot,

    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$pythonScript = Join-Path $sourceRoot '.workflow\workflow.py'
$arguments = @($pythonScript, 'init-instance', '--name', $InstanceName, '--directory', $TargetRoot)
if ($WhatIf) {
    $arguments += '--dry-run'
}

& python @arguments
exit $LASTEXITCODE
