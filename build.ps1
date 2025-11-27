$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  python -m pip install --upgrade pip
  python -m pip install pyinstaller
}
pyinstaller --noconfirm --clean --onefile --windowed --name MDMetaGenerator main.py
Pop-Location
