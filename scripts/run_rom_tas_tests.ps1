param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("black", "white")]
    [string]$Game,

    [Parameter(Mandatory = $true)]
    [ValidateSet("gym-entry", "cilan", "chili", "cress")]
    [string]$Checkpoint
)

$ErrorActionPreference = "Stop"
$workspace = [System.IO.Path]::GetFullPath($env:GITHUB_WORKSPACE)
$romSourceDir = $env:BW_ROM_SOURCE_DIR
$checkpointDir = $env:BW_CHECKPOINT_DIR
$bizHawkExe = $env:BIZHAWK_EXE

foreach ($setting in @(
    @{ Name = "BW_ROM_SOURCE_DIR"; Value = $romSourceDir },
    @{ Name = "BIZHAWK_EXE"; Value = $bizHawkExe }
)) {
    if ([string]::IsNullOrWhiteSpace($setting.Value)) {
        throw "Set machine environment variable $($setting.Name) on the self-hosted runner."
    }
}
if ($Checkpoint -ne "gym-entry" -and [string]::IsNullOrWhiteSpace($checkpointDir)) {
    throw "Set machine environment variable BW_CHECKPOINT_DIR for leader battle-start tests."
}

if (-not (Test-Path -LiteralPath $romSourceDir -PathType Container)) {
    throw "BW_ROM_SOURCE_DIR does not exist: $romSourceDir"
}
if ($Checkpoint -ne "gym-entry" -and -not (Test-Path -LiteralPath $checkpointDir -PathType Container)) {
    throw "BW_CHECKPOINT_DIR does not exist: $checkpointDir"
}
if (-not (Test-Path -LiteralPath $bizHawkExe -PathType Leaf)) {
    throw "BIZHAWK_EXE does not exist: $bizHawkExe"
}

$env:BW_ROM_SOURCE_DIR = [System.IO.Path]::GetFullPath($romSourceDir)
python (Join-Path $workspace "scripts\verify_roms.py")
if ($LASTEXITCODE -ne 0) { throw "Source ROM validation failed." }
python (Join-Path $workspace "scripts\build_striaton.py")
if ($LASTEXITCODE -ne 0) { throw "Building the local test ROMs failed." }

$romPath = Join-Path $workspace "build\striaton\pokemon_$Game`_vanilla_plus_striaton.nds"
if (-not (Test-Path -LiteralPath $romPath -PathType Leaf)) {
    throw "Expected patched ROM was not created: $romPath"
}

$outputDir = Join-Path $workspace "build\rom-test\$Game-$Checkpoint"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$env:BW_TAS_OUTPUT_DIR = $outputDir

Write-Output "Starting BizHawk TAS smoke test: $Game / $Checkpoint"

if ($Checkpoint -eq "gym-entry") {
    $saveVariable = if ($Game -eq "black") { "BW_BLACK_SAVE" } else { "BW_WHITE_SAVE" }
    $sourceSave = [Environment]::GetEnvironmentVariable($saveVariable)
    if ([string]::IsNullOrWhiteSpace($sourceSave) -or -not (Test-Path -LiteralPath $sourceSave -PathType Leaf)) {
        throw "Set $saveVariable to a matching local raw 512 KiB save file on the runner."
    }

    $manifestPath = Join-Path $workspace "build\striaton\manifest.json"
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $sourceName = ($manifest.builds | Where-Object { $_.game -eq $Game } | Select-Object -First 1).source_file
    if ([string]::IsNullOrWhiteSpace($sourceName)) { throw "No source ROM recorded for $Game in the build manifest." }
    $sourceRom = Join-Path $env:BW_ROM_SOURCE_DIR $sourceName
    $checkpointSave = Join-Path $outputDir "$Game-striaton-gym.sav"
    python (Join-Path $workspace "scripts\create_test_checkpoint.py") --source $sourceSave --rom $sourceRom --output $checkpointSave
    if ($LASTEXITCODE -ne 0) { throw "Generating the Striaton Gym save checkpoint failed." }

    $luaPath = Join-Path $workspace "tests\bizhawk_save_checkpoint_verify.lua"
    $saveRamDir = Join-Path (Split-Path -Parent $bizHawkExe) "NDS\SaveRAM"
    if (-not (Test-Path -LiteralPath $saveRamDir -PathType Container)) { throw "BizHawk SaveRAM folder not found: $saveRamDir" }
    $saveRamPath = Join-Path $saveRamDir "pokemon $Game vanilla plus striaton.SaveRAM"
    $backupPath = "$saveRamPath.codex-backup-$([guid]::NewGuid().ToString('N'))"
    $hadSaveRam = Test-Path -LiteralPath $saveRamPath -PathType Leaf
    if ($hadSaveRam) { Copy-Item -LiteralPath $saveRamPath -Destination $backupPath }

    try {
        Copy-Item -LiteralPath $checkpointSave -Destination $saveRamPath -Force
        & $bizHawkExe "--lua=$luaPath" $romPath
        if ($LASTEXITCODE -ne 0) { throw "BizHawk exited with code $LASTEXITCODE." }
    }
    finally {
        if ($hadSaveRam -and (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
            Copy-Item -LiteralPath $backupPath -Destination $saveRamPath -Force
            Remove-Item -LiteralPath $backupPath -Force
        }
        elseif (-not $hadSaveRam -and (Test-Path -LiteralPath $saveRamPath -PathType Leaf)) {
            Remove-Item -LiteralPath $saveRamPath -Force
        }
    }
}
else {
    $statePath = Join-Path $checkpointDir "$Game-$Checkpoint.State"
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "Missing local BizHawk battle checkpoint: $statePath"
    }
    $luaPath = Join-Path $workspace "tests\striaton_tas_smoke.lua"
    & $bizHawkExe "--lua=$luaPath" $romPath "--load-state=$statePath"
    if ($LASTEXITCODE -ne 0) { throw "BizHawk exited with code $LASTEXITCODE." }
}

$resultPath = Join-Path $outputDir "result.txt"
if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
    throw "BizHawk did not write a test result. Check its startup/core logs."
}
$result = Get-Content -LiteralPath $resultPath -Raw
Write-Output $result.Trim()
if (-not $result.StartsWith("PASS:")) { throw "TAS smoke test did not pass." }

$screenshots = @(Get-ChildItem -LiteralPath $outputDir -Filter "*.png" -File)
$expectedScreenshots = if ($Checkpoint -eq "gym-entry") { 3 } else { 4 }
if ($screenshots.Count -ne $expectedScreenshots) {
    throw "Expected $expectedScreenshots screenshot captures, found $($screenshots.Count)."
}
