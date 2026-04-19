@echo off
title JUANA CASH - App Celular
color 0B

echo ===================================================
echo       INICIANDO JUANA CASH - MODO CELULAR
echo ===================================================
echo.

:: Activar entorno virtual
call venv\Scripts\activate

:: Verificar si el backend ya está corriendo
curl -s http://127.0.0.1:8000/ > nul 2>&1
if %errorlevel% == 0 (
    echo Backend ya esta corriendo - OK
) else (
    echo Iniciando backend...
    start "Juana Cash - Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --reload"
    echo Esperando que el backend arranque...
    timeout /t 4 /nobreak > nul
)

echo Iniciando app celular...
python mobile\app.py

pause
