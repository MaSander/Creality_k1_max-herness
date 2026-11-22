# Exporta os perfis de usuario do Creality Print 7.3 deste notebook para o repositorio,
# para importar em outro computador (File > Import > Import Configuration).
# Copia so os .json (os .info tem o ID da conta Creality e nao sao necessarios).
# Uso:  powershell -ExecutionPolicy Bypass -File .claude\perfis\exportar_perfis.ps1
$ErrorActionPreference = 'Stop'
$versao = '7.3'
$userRoot = Join-Path $env:APPDATA "Creality\Creality Print\$versao\user"
$origem = Get-ChildItem $userRoot -Directory | Where-Object { $_.Name -match '^\d+$' -or $_.Name -eq 'default' } |
          Sort-Object { (Get-ChildItem $_.FullName -Recurse -File -Filter *.json | Measure-Object).Count } -Descending |
          Select-Object -First 1
if (-not $origem) { throw "Nenhuma pasta de usuario encontrada em $userRoot" }
$destino = Join-Path $PSScriptRoot "creality-print-$versao"
if (Test-Path $destino) { Remove-Item $destino -Recurse -Force }
foreach ($tipo in 'machine', 'filament', 'process') {
    $src = Join-Path $origem.FullName $tipo
    if (Test-Path $src) {
        New-Item -ItemType Directory -Force (Join-Path $destino $tipo) | Out-Null
        Get-ChildItem $src -Filter *.json | Copy-Item -Destination (Join-Path $destino $tipo)
    }
}
# zip unico com todos os perfis, sem pastas internas (o Creality importa .zip)
$zip = Join-Path $PSScriptRoot "perfis_creality_$versao.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$za = [IO.Compression.ZipFile]::Open($zip, 'Create')
foreach ($f in Get-ChildItem $destino -Recurse -File -Filter *.json) {
    [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($za, $f.FullName, $f.Name, 'Optimal') | Out-Null
}
$za.Dispose()
Get-ChildItem $destino -Recurse -File | ForEach-Object { $_.FullName.Substring($destino.Length + 1) }
"Exportado de: $($origem.FullName)"
"Pasta: $destino"
"Zip:   $zip"
