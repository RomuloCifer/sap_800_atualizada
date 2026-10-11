@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv .venv
  if errorlevel 1 (
    echo Falha ao criar .venv. Confira se o Python esta no PATH.
    pause
    exit /b 1
  )
  echo Instalando dependencias...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Falha ao instalar dependencias.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
endlocal
