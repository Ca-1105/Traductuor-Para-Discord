@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto install

py -3.12 -m venv .venv 2>nul
if exist ".venv\Scripts\python.exe" goto install
python -m venv .venv 2>nul
if exist ".venv\Scripts\python.exe" goto install

echo Necesitas instalar Python 3.12 desde https://www.python.org/downloads/
echo (marca "Add python.exe to PATH" durante la instalacion).
pause
exit /b 1

:install
echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error

echo Descargando modelos (puede tardar unos minutos)...
".venv\Scripts\python.exe" setup_models.py
if errorlevel 1 goto error

echo.
echo LISTO. Ahora ejecuta run.bat
pause
exit /b 0

:error
echo Hubo un error. Comprueba tu conexion a internet y vuelve a ejecutar instalar.bat
pause
exit /b 1
