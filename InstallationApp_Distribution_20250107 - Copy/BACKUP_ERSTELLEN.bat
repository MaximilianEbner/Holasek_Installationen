@echo off
echo ===============================================
echo   Datenbank-Backup erstellen...
echo ===============================================
echo.

if not exist "instance\installation_business.db" (
    echo FEHLER: Keine Datenbank gefunden!
    echo Stellen Sie sicher, dass die App mindestens einmal gestartet wurde.
    pause
    exit /b 1
)

REM Create backup filename with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "datestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

echo Backup wird erstellt: installation_business_backup_%datestamp%.db
copy "instance\installation_business.db" "instance\installation_business_backup_%datestamp%.db"

if %errorlevel% equ 0 (
    echo.
    echo Backup erfolgreich erstellt!
    echo Datei: instance\installation_business_backup_%datestamp%.db
) else (
    echo.
    echo FEHLER: Backup konnte nicht erstellt werden!
)

echo.
pause
