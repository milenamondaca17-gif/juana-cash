@echo off
echo ========================================
echo  JUANA CASH - Sistema POS
echo ========================================
echo.

echo Cerrando procesos anteriores...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak > nul

echo Iniciando servidor backend...
start "Juana Cash - Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

echo Esperando que el backend arranque...
timeout /t 4 /nobreak > nul

echo Iniciando interfaz...
start "Juana Cash - App" cmd /k "cd /d "%~dp0desktop" && ..\venv\Scripts\activate.bat && python main.py"

exit
