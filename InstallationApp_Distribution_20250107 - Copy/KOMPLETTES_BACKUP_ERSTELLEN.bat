@echo off
echo ===============================================
echo   Komplettes Backup erstellen
echo ===============================================
echo.
echo Erstellt ein vollstaendiges Backup der Installation Business App:
echo - SQLite-Datenbank (komplette Kopie)
echo - CSV-Export aller Tabellen  
echo - Detaillierte Backup-Information
echo.
echo Bitte warten...
echo.

REM Prüfe ob Python verfügbar ist
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo FEHLER: Python ist nicht verfuegbar!
    echo Bitte stellen Sie sicher, dass Python installiert ist.
    pause
    exit /b 1
)

REM Prüfe ob Datenbank existiert
if not exist "instance\installation_business.db" (
    echo FEHLER: Keine Datenbank gefunden!
    echo Bitte starten Sie die App mindestens einmal, um eine Datenbank zu erstellen.
    pause
    exit /b 1
)

REM Aktiviere virtuelle Umgebung falls vorhanden
if exist "venv\Scripts\activate.bat" (
    echo Aktiviere virtuelle Umgebung...
    call venv\Scripts\activate.bat
)

REM Führe Backup-Script aus
python db_explorer.py --auto-backup

REM Deaktiviere virtuelle Umgebung
if exist "venv\Scripts\activate.bat" (
    deactivate 2>nul
)

echo.
echo ===============================================
echo   Backup-Erstellung abgeschlossen
echo ===============================================
echo.
echo Das Backup wurde im Ordner 'backup_[Zeitstempel]' erstellt.
echo.
echo INHALT DES BACKUPS:
echo - installation_business.db (SQLite-Datenbank)
echo - csv_export/ (Alle Tabellen als CSV-Dateien)
echo - BACKUP_INFO.txt (Detaillierte Informationen)
echo.
echo WICHTIG: Bewahren Sie Backups an einem sicheren Ort auf!
echo.
pause
