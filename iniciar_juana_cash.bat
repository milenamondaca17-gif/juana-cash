@echo off
title Juana Cash - Iniciando...
color 0C
cd /d "%~dp0"

echo.
echo  ============================================
echo   JUANA CASH - Sistema POS
echo  ============================================
echo.
echo  Iniciando servidor backend...

start "Juana Cash - Backend" cmd /k "cd /d %~dp0 && venv\Scripts\activate.bat && uvicorn backend.app.main:app"

timeout /t 3 /nobreak > nul

echo  Iniciando interfaz...
start "Juana Cash - App" cmd /k "cd /d %~dp0desktop && ..\venv\Scripts\activate.bat && python main.py"

exit