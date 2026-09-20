[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string]$InstanceName,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TargetRoot,

    [string]$WorkflowVersion,

    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$pythonScript = Join-Path $sourceRoot '.workflow\workflow.py'
$arguments = @($pythonScript, 'init-instance')
if ($InstanceName) {
    $arguments += @('--name', $InstanceName)
}
$arguments += @('--directory', $TargetRoot)
if ($WhatIf) {
    $arguments += '--dry-run'
}
if ($WorkflowVersion) {
    $arguments += @('--workflow-version', $WorkflowVersion)
}

& python @arguments
exit $LASTEXITCODE
