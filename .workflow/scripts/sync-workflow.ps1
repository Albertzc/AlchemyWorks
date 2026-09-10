[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TargetRoot,

    [switch]$AllowDirtyTarget
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
$targetRoot = (Resolve-Path $TargetRoot).Path

if ($sourceRoot -eq $targetRoot) {
    throw 'The workflow source and target must be different directories.'
}

if (-not (Test-Path (Join-Path $targetRoot '.git'))) {
    throw "Target is not a Git working tree: $targetRoot"
}

# Keep this list aligned with .workflow/workflow-file-inventory.md. It deliberately
# excludes project deliverables, business code, and generated workflow state.
$items = @(
    'AGENTS.md',
    'README.md',
    '.gitignore',
    '.workflow/README.md',
    '.workflow/workflow.py',
    '.workflow/workflow-file-inventory.md',
    '.workflow/dashboard/template.html',
    '.workflow/tests/test_workflow.py',
    '.workflow/scripts/stage_status.py',
    '.workflow/scripts/id_registry.py',
    '.workflow/scripts/query_id.py',
    '.workflow/scripts/check_links.py',
    '.workflow/scripts/diff_versions.py',
    '.workflow/scripts/sync-workflow.ps1',
    'templates',
    'baseline/README.md',
    'baseline/raw-requirement/README.md',
    'iteration/README.md',
    'iteration/raw-requirement/README.md',
    'workspace/README.md',
    '.agents/skills/stage-gate',
    '.agents/skills/normalize-requirement',
    '.agents/skills/manage-iteration',
    '.agents/skills/prototype-design-system',
    '.agents/skills/design-specification',
    '.agents/skills/planning-validation',
    '.agents/skills/iterate-implementation',
    '.agents/skills/review-release',
    '.agents/skills/workflow-governance'
)

if (-not $AllowDirtyTarget) {
    $targetChanges = @(
        & git -C $targetRoot diff --name-only
        & git -C $targetRoot diff --cached --name-only
        & git -C $targetRoot ls-files --others --exclude-standard
    ) | Where-Object { $_ }
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read Git status for target: $targetRoot"
    }

    $overlaps = foreach ($changedPath in ($targetChanges | Sort-Object -Unique)) {
        $normalizedChange = $changedPath.Replace('\\', '/').TrimStart('./')
        foreach ($workflowItem in $items) {
            $normalizedItem = $workflowItem.Replace('\\', '/').TrimEnd('/')
            if ($normalizedChange -eq $normalizedItem -or $normalizedChange.StartsWith("$normalizedItem/")) {
                $changedPath
                break
            }
        }
    }
    if ($overlaps) {
        $list = ($overlaps | Sort-Object -Unique) -join ', '
        throw "Target has uncommitted changes that overlap synchronized workflow paths: $list. Commit or stash them first, or rerun with -AllowDirtyTarget after review."
    }
}

foreach ($relativePath in $items) {
    $sourceItem = Join-Path $sourceRoot $relativePath
    $targetItem = Join-Path $targetRoot $relativePath
    if (-not (Test-Path $sourceItem)) {
        throw "Workflow source item is missing: $sourceItem"
    }

    if (Test-Path -LiteralPath $sourceItem -PathType Container) {
        if ($PSCmdlet.ShouldProcess($targetItem, "Create directory for $relativePath")) {
            New-Item -ItemType Directory -Force -Path $targetItem | Out-Null
        }
        foreach ($childItem in (Get-ChildItem -LiteralPath $sourceItem -Force)) {
            if ($PSCmdlet.ShouldProcess($targetItem, "Copy workflow item $relativePath/$($childItem.Name)")) {
                Copy-Item -LiteralPath $childItem.FullName -Destination $targetItem -Recurse -Force
            }
        }
    }
    else {
        $targetParent = Split-Path -Parent $targetItem
        if ($PSCmdlet.ShouldProcess($targetParent, "Create directory for $relativePath")) {
            New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
        }
        if ($PSCmdlet.ShouldProcess($targetItem, "Copy workflow item $relativePath")) {
            Copy-Item -LiteralPath $sourceItem -Destination $targetItem -Force
        }
    }
}

Write-Host "Workflow synchronized from $sourceRoot to $targetRoot."
