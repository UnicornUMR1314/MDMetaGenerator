$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  python -m pip install --upgrade pip
  python -m pip install pyinstaller
}
pyinstaller --noconfirm --clean --onefile --windowed --name MDMetaGenerator main.py
$dist = Join-Path $PSScriptRoot 'dist'
$src = Join-Path $dist 'MDMetaGenerator.exe'
$dstName = 'MD' + ([char]0x6587) + ([char]0x7AE0) + 'meta' + ([char]0x4FE1) + ([char]0x606F) + ([char]0x751F) + ([char]0x6210) + ([char]0x5668) + '.exe'
$dst = Join-Path $dist $dstName
if (Test-Path $src) {
  if (Test-Path $dst) { Remove-Item $dst -Force }
  Rename-Item -Path $src -NewName $dstName
}
Pop-Location