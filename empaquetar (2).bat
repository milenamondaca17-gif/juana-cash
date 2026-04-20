@echo off
title JUANA CASH - Empaquetando...
color 0A

echo ============================================
echo   JUANA CASH - Empaquetando para Windows
echo ============================================
echo.

pip install pyinstaller --quiet

echo [1/2] Empaquetando...
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --name "JuanaCash" ^
    --icon "juana_cash.ico" ^
    --add-data "backend;backend" ^
    --add-data "desktop;desktop" ^
    --add-data "juana_cash.db;." ^
    --collect-all "uvicorn" ^
    --collect-all "fastapi" ^
    --collect-all "sqlalchemy" ^
    --collect-all "passlib" ^
    --collect-all "jose" ^
    --collect-all "starlette" ^
    --collect-all "pydantic" ^
    --collect-all "anyio" ^
    --collect-all "h11" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "passlib.handlers.bcrypt" ^
    --hidden-import "sqlalchemy.dialects.sqlite" ^
    "desktop\main.py"

echo.
echo [2/2] Copiando base de datos...
copy "juana_cash.db" "dist\JuanaCash\juana_cash.db" >nul 2>&1
copy "juana_cash.ico" "dist\JuanaCash\juana_cash.ico" >nul 2>&1

echo.
echo ============================================
echo   LISTO - Ahora abre setup_nuevo.iss
echo   en Inno Setup y presiona F9
echo ============================================
pause
