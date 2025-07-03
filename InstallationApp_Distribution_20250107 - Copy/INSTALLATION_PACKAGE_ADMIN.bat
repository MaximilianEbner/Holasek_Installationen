@echo off
echo ===============================================
echo   Installation Business App - ADMINISTRATOR INSTALLATION
echo ===============================================
echo.
echo Dieses Skript wird als Administrator ausgefuehrt, um
echo Berechtigungsprobleme zu vermeiden.
echo.

REM Check for administrator privileges
NET SESSION >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Dieses Skript muss als Administrator ausgefuehrt werden!
    echo.
    echo Bitte:
    echo 1. Rechtsklick auf diese Datei
    echo 2. "Als Administrator ausfuehren" waehlen
    echo.
    pause
    exit /b 1
)

echo ✓ Administrator-Rechte erkannt.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Python ist nicht installiert!
    echo.
    echo Bitte installieren Sie zuerst Python von:
    echo https://www.python.org/downloads/
    echo.
    echo Wichtig: Waehlen Sie bei der Installation "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Python gefunden! Installation wird fortgesetzt...
echo.

REM Create virtual environment
echo 1. Erstelle virtuelle Umgebung...
python -m venv "%~dp0venv"
if %errorlevel% neq 0 (
    echo FEHLER: Konnte virtuelle Umgebung nicht erstellen!
    echo Das kann passieren wenn:
    echo - Python nicht korrekt installiert ist
    echo - Antivirus-Software blockiert
    echo - Nicht genug Festplattenspeicher
    pause
    exit /b 1
)

REM Activate virtual environment
echo 2. Aktiviere virtuelle Umgebung...
call "%~dp0venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo FEHLER: Konnte virtuelle Umgebung nicht aktivieren!
    pause
    exit /b 1
)

REM Upgrade pip first
echo 3a. Aktualisiere pip...
python -m pip install --upgrade pip

REM Install requirements with multiple fallback methods
echo 3b. Installiere benoetigte Pakete (mit Administrator-Rechten)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo    Erste Methode fehlgeschlagen. Versuche ohne Cache...
    pip install --no-cache-dir -r requirements.txt
    if %errorlevel% neq 0 (
        echo    Versuche einzelne Installation...
        pip install Flask
        pip install Flask-SQLAlchemy
        pip install Flask-WTF
        pip install WTForms
        pip install reportlab
        pip install openpyxl
        if %errorlevel% neq 0 (
            echo.
            echo FEHLER: Konnte Pakete auch mit Administrator-Rechten nicht installieren!
            echo.
            echo WEITERE LOESUNGSVERSUCHE:
            echo 1. Pruefen Sie Ihre Internetverbindung
            echo 2. Deaktivieren Sie temporaer alle Antivirus/Firewall-Programme
            echo 3. Versuchen Sie es zu einem spaeteren Zeitpunkt
            echo 4. Kontaktieren Sie den Support mit dieser Fehlermeldung
            echo.
            pause
            exit /b 1
        )
    )
)

REM Initialize database
echo 4. Initialisiere Datenbank...
python init_db.py
if %errorlevel% neq 0 (
    echo FEHLER: Konnte Datenbank nicht initialisieren!
    echo Das ist ungewoehnlich nach erfolgreicher Paket-Installation.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   INSTALLATION ERFOLGREICH ABGESCHLOSSEN!
echo ===============================================
echo.
echo Die App ist jetzt installiert und einsatzbereit.
echo.
echo Zum Starten der App:
echo - Doppelklick auf "START_APP.bat"
echo.
echo HINWEIS: Die App kann normal (ohne Administrator) gestartet werden.
echo.
pause
