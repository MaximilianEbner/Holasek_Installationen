# GitHub Backup-System für Railway

## Setup-Anleitung

### 1. Environment-Variablen in Railway setzen

Gehen Sie zu Ihrem Railway-Projekt → Settings → Environment Variables und fügen Sie hinzu:

```bash
# GitHub Repository (erforderlich)
GITHUB_BACKUP_REPO=MaximilianEbner/Holasek_Installationen

# GitHub Token (optional, nur für private Repositories)
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. GitHub Repository Struktur

Erstellen Sie im Root Ihres GitHub-Repositories einen `backups/` Ordner:

```
your-repo/
├── backups/              # Neuer Ordner für Backup-Dateien
│   ├── InnSAN_Database_Backup_20250801_120000.db
│   ├── InnSAN_Database_Backup_20250802_140000.db
│   └── ...
├── app.py
├── requirements.txt
└── ...
```

### 3. Workflow

#### Backup erstellen:
1. In der App: Backup → "Datenbank Download"
2. `.db` Datei manuell in GitHub `/backups/` Ordner hochladen

#### Backup wiederherstellen:
1. In der App: Backup → "GitHub Backup-Manager" 
2. Gewünschtes Backup auswählen und wiederherstellen
3. Railway-App neu starten (empfohlen)

### 4. Automatischer Railway-Neustart

Nach Backup-Wiederherstellung sollte die Railway-App neu gestartet werden:

```bash
# Railway CLI (lokal)
railway restart

# Oder im Railway Dashboard: Deploy → Restart
```

### 5. Sicherheit

- **Öffentliche Repos:** Keine sensiblen Daten in Backups
- **Private Repos:** GitHub Token mit Repository-Berechtigung
- **Produktionsumgebung:** Backups vor wichtigen Änderungen erstellen

### 6. Fehlerbehandlung

Falls Probleme auftreten:

1. **Repository nicht gefunden:** 
   - `GITHUB_BACKUP_REPO` Environment Variable prüfen
   - Repository-Berechtigung prüfen

2. **Backup nicht gefunden:**
   - `/backups/` Ordner im Repository existiert?
   - `.db` Dateien korrekt hochgeladen?

3. **Wiederherstellung fehlgeschlagen:**
   - Backup-Datei beschädigt?
   - Genügend Speicherplatz auf Railway?
   - Railway-Logs prüfen

### 7. GitHub Token erstellen (falls benötigt)

Für private Repositories:

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" → Berechtigung: `repo` (Full control of private repositories)
3. Token in Railway als `GITHUB_TOKEN` Environment Variable hinzufügen

## Vorteile dieses Systems

✅ **Einfache Handhabung:** Upload manuell, Restore über App-Interface  
✅ **Flexibilität:** Verschiedene Backup-Versionen verfügbar  
✅ **Sicherheit:** Automatische Sicherung vor Wiederherstellung  
✅ **Übersicht:** Detaillierte Backup-Analyse vor Restore  
✅ **Railway-Integration:** Nahtlose Integration in Railway-Deployment
