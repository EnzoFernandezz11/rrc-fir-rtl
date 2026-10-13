param([string]$OutputDirectory = "")
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
    $OutputDirectory = Join-Path $root "build/ppa/frequency_serial/$stamp-$commit-vivado"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path $OutputDirectory) {throw "Output already exists: $OutputDirectory"}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
Set-Content -Encoding Ascii -Path (Join-Path $OutputDirectory "launch_pending.txt") -Value "new run"
$env:PPA_VIVADO_OUTPUT = $OutputDirectory
& vivado -mode batch -log (Join-Path $OutputDirectory "vivado.log") `
    -journal (Join-Path $OutputDirectory "vivado.jou") `
    -source (Join-Path $PSScriptRoot "run.tcl") -tclargs $OutputDirectory
$status = $LASTEXITCODE
Write-Host "Results: $OutputDirectory"
exit $status
