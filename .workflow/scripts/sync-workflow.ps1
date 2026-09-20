[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TargetRoot,

    [string]$WorkflowVersion,

    [switch]$AllowDirtyTarget,

    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$pythonScript = Join-Path $sourceRoot '.workflow\workflow.py'
$arguments = @($pythonScript, 'sync', '--directory', $TargetRoot)
if ($AllowDirtyTarget) {
    $arguments += '--allow-dirty'
}
if ($WhatIf) {
    $arguments += '--dry-run'
}
if ($WorkflowVersion) {
    $arguments += @('--workflow-version', $WorkflowVersion)
}

& python @arguments
exit $LASTEXITCODE
