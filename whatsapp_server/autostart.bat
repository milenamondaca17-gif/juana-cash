@echo off
echo Agregando servidor WhatsApp al inicio de Windows...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set BAT_PATH=%~dp0iniciar.bat

copy "%BAT_PATH%" "%STARTUP%\JuanaCash_WhatsApp.bat"

echo.
echo LISTO - El servidor arrancara automaticamente cuando enciendas la PC.
echo.
pause
