@echo off
title Instalando Servidor WhatsApp - Juana Cash
echo.
echo ============================================
echo   INSTALANDO SERVIDOR WHATSAPP JUANA CASH
echo ============================================
echo.
cd /d "%~dp0"

echo Verificando Node.js...
node --version
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Node.js no esta instalado.
    echo Descargalo de: https://nodejs.org/en/download
    echo.
    pause
    exit /b 1
)

echo.
echo Instalando dependencias (puede tardar unos minutos)...
echo.
npm install

if %errorlevel% neq 0 (
    echo.
    echo ERROR en la instalacion. Revisa tu conexion a internet.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   INSTALACION COMPLETADA!
echo ============================================
echo.
echo Ahora ejecuta "iniciar.bat" para arrancar el servidor.
echo.
pause
