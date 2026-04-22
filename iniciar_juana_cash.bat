@echo off
echo ==========================================
echo  JUANA CASH - Sistema POS
echo ==========================================
echo.
echo Iniciando servidor backend...
start "Juana Cash - Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --reload --host 0.0.0.0"
timeout /t 3 /nobreak > nul
echo Iniciando interfaz...
start "Juana Cash - App" cmd /k "cd /d "%~dp0desktop" && ..\venv\Scripts\activate.bat && python main.py"
exit
