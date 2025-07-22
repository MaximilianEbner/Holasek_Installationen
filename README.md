# 🚀 Railway Deployment Guide

## ✅ Deployment-fertige Dateien

Alle notwendigen Dateien sind im `deploy/` Ordner vorbereitet:

```
deploy/
├── app.py              # Production-ready Flask App (MIT Upload-Features!)
├── models.py           # Datenbankmodelle (SQLite + PostgreSQL ready)
├── config.py           # Production Config (PostgreSQL für Railway)
├── forms.py            # WTForms
├── utils.py            # Utility-Funktionen
├── backup_system.py    # Backup-System (CSV/Excel)
├── invoice_pdf.py      # PDF-Generation
├── pdf_export.py       # PDF-Export
├── work_steps.py       # Arbeitsschritte
├── requirements.txt    # Optimierte Dependencies
├── Procfile           # Railway Start-Kommando
├── runtime.txt        # Python Version
├── templates/         # Alle HTML-Templates
└── static/           # CSS, JS, Bilder
```

## 🔧 Railway Setup

### 1. GitHub Repository erstellen
```bash
cd deploy/
git init
git add .
git commit -m "Initial deployment version"
git branch -M main
git remote add origin https://github.com/DEIN_USERNAME/installations-app.git
git push -u origin main
```

### 2. Railway Deployment
1. Gehe zu [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Wähle dein Repository
4. Railway erkennt automatisch Python und verwendet:
   - `Procfile` für Start-Kommando
   - `requirements.txt` für Dependencies
   - `runtime.txt` für Python Version

### 3. Umgebungsvariablen (Optional)
In Railway unter "Variables" setzen:
```
SECRET_KEY=dein-super-sicherer-secret-key-hier-mindestens-32-zeichen
```

PostgreSQL wird automatisch von Railway bereitgestellt.

## 🎯 Wichtige Änderungen für Production

### ✅ **Entfernte Features:**
- ❌ File Upload System komplett entfernt
- ❌ Lokale Datei-Speicherung
- ❌ Upload-Ordner und Abhängigkeiten
- ❌ Flask-Login Abhängigkeit (vereinfachtes System)

### ✅ **Vereinfachtes Login:**
- **Benutzername:** `admin`
- **Passwort:** `admin123`
- Fest codiert, keine Umgebungsvariablen nötig
- Automatische Admin-Erstellung beim ersten Start

### ✅ **Datenbank:**
- **Lokal:** SQLite (wie bisher)
- **Railway:** PostgreSQL (automatisch)
- Automatische Erkennung über `DATABASE_URL`

### ✅ **Performance-Optimierungen:**
- Reduzierte Dependencies
- Optimierte Imports
- Vereinfachte Route-Struktur
- Production-ready Config

## 🔍 Nach dem Deployment

### App testen:
1. Railway gibt dir eine URL wie: `https://deine-app.up.railway.app`
2. Login mit: `admin` / `admin123`
3. Teste Grundfunktionen:
   - Kunden anlegen
   - Angebote erstellen
   - PDF-Export
   - Admin-Benutzerverwaltung

### Datenbank-Migration:
Railway erstellt automatisch alle Tabellen beim ersten Start.

## 🛠️ Troubleshooting

### Häufige Probleme:
1. **App startet nicht:** Prüfe Railway Logs
2. **Datenbank-Fehler:** PostgreSQL-Connection prüfen
3. **Login funktioniert nicht:** Logs prüfen, evtl. Admin neu erstellen

### Railway Commands:
```bash
# Logs anzeigen
railway logs

# Neue Deployment triggern
git push origin main
```

## 📊 Monitoring

- **Railway Dashboard:** Zeigt CPU, Memory, Database Usage
- **Logs:** Railway Logs Tab für Fehleranalyse
- **Database:** Railway Database Tab für direkten DB-Zugriff

## 🔐 Sicherheit

### Production Checklist:
- ✅ `SECRET_KEY` als Umgebungsvariable setzen
- ✅ Debug-Modus deaktiviert
- ✅ Sichere Session-Cookies
- ✅ CSRF-Schutz aktiviert
- ✅ Admin-Passwort nach erstem Login ändern

### Nach dem Deployment:
1. Login mit `admin` / `admin123`
2. Gehe zu "Admin" → "Benutzer verwalten"
3. Erstelle neuen Admin-User mit sicherem Passwort
4. Lösche den Standard-Admin (optional)

## 🚀 Ready for Production!

Deine App ist jetzt bereit für Railway Deployment mit:
- ✅ PostgreSQL Database
- ✅ Sicherem Admin-System
- ✅ PDF-Export
- ✅ Backup-System
- ✅ Responsive UI
- ✅ Production-ready Performance

**URL nach Deployment:** `https://deine-app.up.railway.app`
**Login:** `admin` / `admin123`
