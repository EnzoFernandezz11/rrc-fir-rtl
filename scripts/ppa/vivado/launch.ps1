param(
    [string]$OutputDirectory = "",
    [string]$Top = "fir_frequency_serial",
    [string]$Bench,
    [string]$PeriodNs,
    [string]$LatencyCycles,
    [string]$BlockCycles,
    [string]$ActiveCycles,
    [string]$Vectors
)
$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../../.."))
$commit = "source"
$manifestPath = Join-Path $root "manifest.json"
if (Test-Path $manifestPath) {
    $manifest = Get-Content -Raw $manifestPath | ConvertFrom-Json
    if ($manifest.commit -match '^[0-9a-f]{7,40}$') {
        $commit = $manifest.commit.Substring(0, [Math]::Min(8, $manifest.commit.Length))
    }
}
if (!$OutputDirectory) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $target = $Top -replace '^fir_', ''
    $OutputDirectory = Join-Path $root "build/ppa/$target/$stamp-$commit-vivado"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path $OutputDirectory) {throw "Output already exists: $OutputDirectory"}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
Set-Content -Encoding Ascii -Path (Join-Path $OutputDirectory "launch_pending.txt") -Value "new run"
$env:PPA_VIVADO_OUTPUT = $OutputDirectory
$ppaArguments = @($OutputDirectory, "-top", $Top)
foreach ($pair in @(
    @("Bench", "-bench"), @("PeriodNs", "-period_ns"),
    @("LatencyCycles", "-latency_cycles"), @("BlockCycles", "-block_cycles"),
    @("ActiveCycles", "-active_cycles"), @("Vectors", "-vectors")
)) {
    if ($PSBoundParameters.ContainsKey($pair[0])) {
        $ppaArguments += @($pair[1], $PSBoundParameters[$pair[0]])
    }
}
& vivado -mode batch -log (Join-Path $OutputDirectory "vivado.log") `
    -journal (Join-Path $OutputDirectory "vivado.jou") `
    -source (Join-Path $PSScriptRoot "run.tcl") -tclargs @ppaArguments
$status = $LASTEXITCODE
Write-Host "Results: $OutputDirectory"
exit $status
