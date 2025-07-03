@echo off
echo ===============================================
echo   Installation Business App - Installations Paket
echo ===============================================
echo.
echo Dieses Skript installiert automatisch die Installations-App
echo auf Ihrem Computer. Bitte warten Sie...
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
python -m venv venv
if %errorlevel% neq 0 (
    echo FEHLER: Konnte virtuelle Umgebung nicht erstellen!
    pause
    exit /b 1
)

REM Activate virtual environment
echo 2. Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat

REM Install requirements
echo 3. Installiere benoetigte Pakete...
echo    Dies kann einige Minuten dauern...
echo.

REM Try different installation methods
echo    Versuche Installation mit pip...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo    Normale Installation fehlgeschlagen.
    echo    Versuche alternative Methoden...
    echo.
    
    REM Try with python -m pip (more reliable)
    echo    Versuche mit 'python -m pip'...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo    python -m pip fehlgeschlagen. Versuche mit --user...
        python -m pip install --user -r requirements.txt
        if %errorlevel% neq 0 (
            echo    --user Installation fehlgeschlagen. Versuche ohne Cache...
            python -m pip install --no-cache-dir -r requirements.txt
            if %errorlevel% neq 0 (
                echo    Versuche mit --user und --no-cache-dir...
                python -m pip install --user --no-cache-dir -r requirements.txt
                if %errorlevel% neq 0 (
                    echo.
                    echo FEHLER: Konnte Pakete nicht installieren!
                    echo.
                    echo HAEUFIGSTE URSACHEN UND LOESUNGEN:
                    echo.
                    echo 1. MICROSOFT VISUAL C++ BUILD TOOLS FEHLEN:
                    echo    - Dies ist der haeufigste Grund fuer Installationsfehler
                    echo    - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
                    echo    - Installieren Sie die "C++ build tools"
                    echo    - Starten Sie nach der Installation den Computer neu
                    echo.
                    echo 2. BERECHTIGUNGEN:
                    echo    - Starten Sie als Administrator: Rechtsklick -^> "Als Administrator ausfuehren"
                    echo    - Oder fuegen Sie den Ordner zu den Antivirus-Ausnahmen hinzu
                    echo.
                    echo 3. ANTIVIRUS-SOFTWARE:
                    echo    - Deaktivieren Sie temporaer Ihr Antivirus-Programm
                    echo    - Fuegen Sie den Python- und Projekt-Ordner zu den Ausnahmen hinzu
                    echo.
                    echo 4. NETZWERK:
                    echo    - Pruefen Sie Ihre Internetverbindung
                    echo    - Bei Firewalls: Freigabe fuer Python und pip
                    echo.
                    echo 5. PYTHON VERSION:
                    echo    - Unterstuetzte Versionen: Python 3.8 bis 3.12
                    echo    - Python 3.13 benoetigt zusaetzliche Build Tools
                    echo.
                    echo MANUELLE INSTALLATION:
                    echo Nach dem Beheben des Problems koennen Sie manuell installieren:
                    echo    1. Oeffnen Sie eine Eingabeaufforderung als Administrator
                    echo    2. Navigieren Sie zu diesem Ordner
                    echo    3. Fuehren Sie aus: python -m pip install -r requirements.txt
                    echo.
                    pause
                    exit /b 1
                )
            )
        )
    )
)

REM Initialize database
echo 4. Initialisiere Datenbank...
python init_db.py
if %errorlevel% neq 0 (
    echo FEHLER: Konnte Datenbank nicht initialisieren!
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
echo Weitere Informationen finden Sie in:
echo - BENUTZERHANDBUCH.txt
echo.
pause
