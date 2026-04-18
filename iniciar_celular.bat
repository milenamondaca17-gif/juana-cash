@echo off
title JUANA CASH - App Celular
color 0B

echo ===================================================
echo       INICIANDO JUANA CASH - MODO CELULAR
echo ===================================================
echo.

:: Activamos tu entorno virtual para que Flet funcione
call venv\Scripts\activate

:: Ejecutamos la aplicacion
python mobile\app.py

pause