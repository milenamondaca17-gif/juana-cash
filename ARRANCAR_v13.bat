@echo off
chcp 65001 > nul
title JUANA CASH - Sistema POS

echo.
echo  ========================================
echo   JUANA CASH - Sistema POS
echo  ========================================
echo.

:: ── ACTUALIZAR DESDE GITHUB ──────────────────────────────────────────────────
echo  Buscando actualizaciones...
git -C "%~dp0" pull origin main --quiet 2>nul
if errorlevel 1 (
    echo  [OK] Sin cambios o sin internet - continuando con version actual.
) else (
    echo  [OK] Codigo actualizado.
)
echo.

:: ── INSTALAR DEPENDENCIAS NUEVAS (si las hay) ─────────────────────────────────
echo  Verificando dependencias...
call "%~dp0venv\Scripts\activate.bat"
pip install -r "%~dp0requirements.txt" --quiet --no-warn-script-location 2>nul
echo  [OK] Dependencias listas.
echo.

:: ── MATAR PROCESOS ANTERIORES ────────────────────────────────────────────────
taskkill /F /IM python.exe > nul 2>&1
timeout /t 2 /nobreak > nul

:: ── ARRANCAR BACKEND ─────────────────────────────────────────────────────────
echo  Iniciando backend...
start "Juana Cash - Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

:: ── ESPERAR QUE ARRANQUE ─────────────────────────────────────────────────────
timeout /t 4 /nobreak > nul

:: ── ARRANCAR DESKTOP ─────────────────────────────────────────────────────────
echo  Iniciando interfaz...
start "Juana Cash - App" cmd /k "cd /d "%~dp0desktop" && ..\venv\Scripts\activate.bat && python main.py"

echo.
echo  Sistema iniciado. Podes cerrar esta ventana.
echo.
timeout /t 3 /nobreak > nul
exit
