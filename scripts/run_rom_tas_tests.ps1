param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("black", "white")]
    [string]$Game,

    [Parameter(Mandatory = $true)]
    [ValidateSet("cilan", "chili", "cress")]
    [string]$Checkpoint
)

$ErrorActionPreference = "Stop"
$workspace = [System.IO.Path]::GetFullPath($env:GITHUB_WORKSPACE)
$romSourceDir = $env:BW_ROM_SOURCE_DIR
$checkpointDir = $env:BW_CHECKPOINT_DIR
$bizHawkExe = $env:BIZHAWK_EXE

foreach ($setting in @(
    @{ Name = "BW_ROM_SOURCE_DIR"; Value = $romSourceDir },
    @{ Name = "BW_CHECKPOINT_DIR"; Value = $checkpointDir },
    @{ Name = "BIZHAWK_EXE"; Value = $bizHawkExe }
)) {
    if ([string]::IsNullOrWhiteSpace($setting.Value)) {
        throw "Set machine environment variable $($setting.Name) on the self-hosted runner."
    }
}

if (-not (Test-Path -LiteralPath $romSourceDir -PathType Container)) {
    throw "BW_ROM_SOURCE_DIR does not exist: $romSourceDir"
}
if (-not (Test-Path -LiteralPath $checkpointDir -PathType Container)) {
    throw "BW_CHECKPOINT_DIR does not exist: $checkpointDir"
}
if (-not (Test-Path -LiteralPath $bizHawkExe -PathType Leaf)) {
    throw "BIZHAWK_EXE does not exist: $bizHawkExe"
}

$statePath = Join-Path $checkpointDir "$Game-$Checkpoint.State"
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    throw "Missing local BizHawk checkpoint: $statePath"
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
$luaPath = Join-Path $workspace "tests\striaton_tas_smoke.lua"

Write-Output "Starting BizHawk TAS smoke test: $Game / $Checkpoint"
& $bizHawkExe "--lua=$luaPath" $romPath "--load-state=$statePath"
if ($LASTEXITCODE -ne 0) { throw "BizHawk exited with code $LASTEXITCODE." }

$resultPath = Join-Path $outputDir "result.txt"
if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
    throw "BizHawk did not write a test result. Check its startup/core logs."
}
$result = Get-Content -LiteralPath $resultPath -Raw
Write-Output $result.Trim()
if (-not $result.StartsWith("PASS:")) { throw "TAS smoke test did not pass." }

$screenshots = @(Get-ChildItem -LiteralPath $outputDir -Filter "*.png" -File)
if ($screenshots.Count -ne 4) {
    throw "Expected four screenshot captures, found $($screenshots.Count)."
}
