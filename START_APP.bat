@echo off
title Installations Business App - Starter
color 0A

echo.
echo ============================================================
echo 🏢 INSTALLATIONS BUSINESS APP - STARTER
echo ============================================================
echo.
echo 📋 Starte Anwendung...
echo.

REM Wechsle zum App-Verzeichnis
cd /d "%~dp0"

REM Prüfe ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ FEHLER: Python ist nicht installiert oder nicht im PATH!
    echo.
    echo Bitte installieren Sie Python von https://python.org
    echo und stellen Sie sicher, dass es zum PATH hinzugefügt wird.
    echo.
    pause
    exit /b 1
)

REM Prüfe ob app.py existiert
if not exist "app.py" (
    echo ❌ FEHLER: app.py nicht gefunden!
    echo Stellen Sie sicher, dass Sie sich im richtigen Verzeichnis befinden.
    echo.
    pause
    exit /b 1
)

REM Prüfe kritische Dependencies
echo 📦 Prüfe Dependencies...
python -c "import flask, flask_sqlalchemy, flask_wtf, wtforms, flask_login, reportlab, email_validator" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Einige Dependencies fehlen. Installiere sie jetzt...
    echo.
    pip install Flask Flask-SQLAlchemy Flask-WTF WTForms Flask-Login reportlab email-validator
    if errorlevel 1 (
        echo ❌ FEHLER: Dependencies konnten nicht installiert werden!
        echo.
        pause
        exit /b 1
    )
    echo ✅ Dependencies erfolgreich installiert!
    echo.
)

echo ✅ Alle Dependencies verfügbar!
echo.
echo 🚀 Starte Flask-App...
echo ⚠️  WICHTIG: Lassen Sie dieses Fenster geöffnet!
echo    Zum Beenden der App drücken Sie Strg+C oder schließen Sie das Fenster.
echo.
echo ============================================================

REM Starte die App
python app.py

REM Falls die App beendet wird
echo.
echo 💤 App wurde beendet.
echo.
pause
