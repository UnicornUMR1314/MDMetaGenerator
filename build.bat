@echo off
setlocal
pushd "%~dp0"
where pyinstaller >nul 2>&1
if errorlevel 1 (
  python -m pip install --upgrade pip
  python -m pip install pyinstaller
)
pyinstaller --noconfirm --clean --onefile --windowed --name MDMetaGenerator main.py
powershell -NoProfile -ExecutionPolicy Bypass -Command "$dist = Join-Path $pwd 'dist'; $src = Join-Path $dist 'MDMetaGenerator.exe'; $dstName = 'MD' + ([char]0x6587) + ([char]0x7AE0) + 'meta' + ([char]0x4FE1) + ([char]0x606F) + ([char]0x751F) + ([char]0x6210) + ([char]0x5668) + '.exe'; $dst = Join-Path $dist $dstName; if (Test-Path $src) { if (Test-Path $dst) { Remove-Item $dst -Force }; Rename-Item -LiteralPath $src -NewName $dstName }"
popd