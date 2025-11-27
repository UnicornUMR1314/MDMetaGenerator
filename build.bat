@echo off
setlocal
pushd "%~dp0"
where pyinstaller >nul 2>&1
if errorlevel 1 (
  python -m pip install --upgrade pip
  python -m pip install pyinstaller
)
pyinstaller --noconfirm --clean --onefile --windowed --name MDMetaGenerator main.py
popd
