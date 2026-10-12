@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Rode iniciar.bat uma vez para criar a venv.
  pause
  exit /b 1
)

REM Sem argumentos: usa Excel (1a linha Status=Pendente)
REM Com argumentos: rodar-fluxo.bat BATCH ISSUER

if "%~1"=="" (
  echo Usando Excel - primeira linha Status=Pendente
  ".venv\Scripts\python.exe" main.py fluxo --excel
) else (
  set BATCH=%~1
  set ISSUER=%~2
  echo Batch=%BATCH%  Issuer=%ISSUER%
  ".venv\Scripts\python.exe" main.py fluxo --batch "%BATCH%" --issuer "%ISSUER%"
)

echo.
echo Exit code: %ERRORLEVEL%
pause
endlocal
