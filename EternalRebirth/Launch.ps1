param(
    [ValidateSet('Explore','Editor','Build','RebuildScene','Capture','Gallery','Heroes','Combat','Battle','Motion','WeatherCapture')]
    [string]$Mode = 'Explore',
    [switch]$Anime,
    [ValidateRange(1,5)][int]$View = 1
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$workspaceRoot = Split-Path $projectRoot -Parent
$engineRoot = 'D:\Epic Games\UE_5.8'
$projectFile = Join-Path $projectRoot 'EternalRebirth.uproject'
$editor = Join-Path $engineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
if (!(Test-Path -LiteralPath $editor)) { throw "Unreal Engine 5.8 not found: $engineRoot" }
if ($Mode -eq 'Build') {
    $env:LLVM_PATH = Join-Path $workspaceRoot 'Tools\LLVM'
    & (Join-Path $engineRoot 'Engine\Build\BatchFiles\Build.bat') EternalRebirthEditor Win64 Development "-Project=$projectFile" -WaitMutex -NoHotReloadFromIDE
    if ($LASTEXITCODE -ne 0) { throw 'C++ compilation failed. See Saved/Logs and UnrealBuildTool output.' }
} elseif ($Mode -eq 'RebuildScene') {
    $steps = @(
        @('build_showcase.py', 'SHOWCASE_COMPLETE'),
        @('repair_surface.py', 'SURFACE_REPAIRED'),
        @('polish_showcase.py', 'POLISH_COMPLETE'),
        @('light_polish.py', 'LIGHT_POLISH_COMPLETE'),
        @('finish_environment.py', 'DISTANT_LIGHTING_COMPLETE'),
        @('tune_showcase.py', 'TUNING_COMPLETE'),
        @('animate_environment.py', 'ANIMATED_ENVIRONMENT_COMPLETE'),
        @('build_weather_materials.py', 'WEATHER_MATERIALS_COMPLETE'),
        @('build_weather_effects.py', 'WEATHER_EFFECTS_COMPLETE')
    )
    foreach ($step in $steps) {
        $stepFile = Join-Path $workspaceRoot ('Tools\' + $step[0])
        $stepLog = Join-Path $projectRoot ('Saved\Logs\Rebuild_' + $step[0] + '.log')
        & (Join-Path $engineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe') (Join-Path $projectRoot 'ArtBuild.uproject') -run=pythonscript "-script=$stepFile" -NullRHI -unattended -nosplash -NoSound "-abslog=$stepLog"
        if ($LASTEXITCODE -ne 0 -or !(Select-String -LiteralPath $stepLog -Pattern ('REBIRTH: ' + $step[1]) -Quiet)) {
            throw ('Scene build failed at ' + $step[0] + '. See ' + $stepLog)
        }
    }
} elseif ($Mode -eq 'Editor') {
    & $editor $projectFile -NoSplash
} else {
    $map = if ($Mode -eq 'Heroes') { '/Game/Maps/HeroShowcase' } elseif ($Mode -eq 'Combat') { '/Game/Maps/HeroCombatPrototype' } elseif ($Mode -eq 'Battle') { '/Game/Maps/EternalCombat' } else { '/Game/Maps/EternalShowcase' }
    $launchArgs = @($projectFile, $map, '-game', '-windowed', '-ResX=1600', '-ResY=900', '-ForceRes', '-NoSplash', "-RebirthView=$View")
    if ($Anime) { $launchArgs += '-Anime' }
    if ($Mode -eq 'Capture') { $launchArgs += @('-RenderOffscreen','-ForceRes','-RebirthCapture','-RebirthStyleTest','-unattended','-NoSound') }
    if ($Mode -eq 'Gallery') { $launchArgs += @('-RenderOffscreen','-ForceRes','-RebirthGallery','-unattended','-NoSound') }
    if ($Mode -eq 'Motion') { $launchArgs += @('-RenderOffscreen','-ForceRes','-RebirthCapture','-RebirthMotionTest','-Clean','-unattended','-NoSound') }
    if ($Mode -eq 'WeatherCapture') { $launchArgs += @('-RenderOffscreen','-ForceRes','-RebirthWeatherTest','-Clean','-unattended') }
    & $editor @launchArgs
}
