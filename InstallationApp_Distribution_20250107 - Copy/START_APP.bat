@echo off
echo ===============================================
echo   Installations Business App wird gestartet...
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo FEHLER: Die App ist noch nicht installiert!
    echo.
    echo Bitte fuehren Sie zuerst "INSTALLATION_PACKAGE.bat" aus.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the application
echo App wird gestartet...
echo.
echo Die App ist unter folgender Adresse erreichbar:
echo http://localhost:5000
echo.
echo WICHTIG: Lassen Sie dieses Fenster offen!
echo Zum Beenden der App druecken Sie Strg+C
echo.
echo Browser wird automatisch geoeffnet...
timeout /t 3 /nobreak > nul
start http://localhost:5000

python app.py

echo.
echo App wurde beendet.
pause
