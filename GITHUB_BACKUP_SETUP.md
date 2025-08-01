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
1. **Lokal:** App → Backup → "Datenbank Download" → `.db` Datei
2. **GitHub Upload:** Manuell die `.db` Datei in `Holasek_Installationen/backups/` hochladen

#### Backup wiederherstellen:
1. **Railway App:** Backup → "GitHub Backup-Manager" 
2. **Automatische Konvertierung:** SQLite-Backup → PostgreSQL Migration
3. **Gewünschtes Backup auswählen:** "Wiederherstellen" klicken
4. **Railway:** Automatische PostgreSQL-Integration (kein Neustart nötig)

### 4. Datenbank-Typen

Das System erkennt automatisch die Umgebung:

- **🏠 Lokale Entwicklung:** SQLite (`instance/installation_business.db`)
- **🚀 Railway Production:** PostgreSQL (automatisch bereitgestellt)

#### SQLite zu PostgreSQL Migration:
- **Automatisch:** SQLite-Backups werden zu PostgreSQL konvertiert
- **Tabellen:** Alle Daten und Beziehungen bleiben erhalten  
- **Sequences:** Auto-Increment IDs werden korrekt synchronisiert
- **Fehlerbehandlung:** Detaillierte Logs bei Problemen

### 5. Railway PostgreSQL Besonderheiten

Railway stellt automatisch bereit:
- `DATABASE_URL` Environment Variable
- PostgreSQL-Instanz mit SSL
- Automatische Verbindungsparameter

**Keine manuelle Konfiguration nötig!**

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
