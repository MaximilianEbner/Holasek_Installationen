# 🚀 Deploy Package - InstallationApp

## 📦 Bereit für GitHub & Railway!

Dieser Ordner enthält alle Dateien, die für die Bereitstellung auf GitHub und Railway benötigt werden.

## ✅ Inhalt des Deploy-Pakets:

### 🔧 Core Application:
- `app.py` - Haupt-Flask-Anwendung (mit Login-System)
- `config.py` - Konfiguration für Produktion
- `models.py` - Datenbankmodelle 
- `forms.py` - Web-Formulare
- `utils.py` - Hilfsfunktionen
- `work_steps.py` - Arbeitsschritte-Logik

### 🗄️ Datenbank & Migration:
- `init_db.py` - Lokale Datenbank-Initialisierung
- `init_railway.py` - Railway-spezifische Initialisierung
- `migrations/` - Datenbank-Migrationen (44 Dateien)

### 📄 PDF & Export:
- `invoice_pdf.py` - PDF-Generierung
- `pdf_export.py` - Export-Funktionen

### 🎨 Templates & Static:
- `templates/` - Alle HTML-Templates (44 Dateien)
- `static/` - CSS, JS, Bilder (ohne user uploads)
- `templates_excel/` - Excel-Vorlagen

### ⚙️ Deployment:
- `requirements.txt` - Python-Dependencies
- `Procfile` - Railway-Konfiguration
- `runtime.txt` - Python-Version (3.13.5)
- `.gitignore` - Git-Ignore-Regeln

### 📚 Dokumentation:
- `README.txt` - Projekt-README
- `DEPLOYMENT_GUIDE.md` - Deployment-Anleitung

### 🛠️ Admin-Tools:
- `backup_system.py` - Backup-Funktionen
- `templates_admin.py` - Template-Verwaltung
- `db_explorer.py` - Datenbank-Explorer

## 🚀 Deployment-Schritte:

### 1. GitHub Upload:
```bash
# Alle Dateien aus diesem deploy/ Ordner hochladen
# NICHT die ursprünglichen Projektdateien!
```

### 2. Railway Deployment:
1. GitHub Repository mit Railway verbinden
2. Environment Variables setzen:
   - `SECRET_KEY`: Starker geheimer Schlüssel
   - `DATABASE_URL`: Wird automatisch gesetzt
3. Automatisches Deployment starten

### 3. Nach dem Deployment:
- Login mit: `admin` / `admin123`
- **SOFORT Passwort ändern!**
- Stammdaten konfigurieren

## ⚠️ Wichtige Hinweise:

### ✅ ENTHÄLT:
- Alle notwendigen Anwendungsdateien
- Komplettes Template-System
- Migrations für Datenbank
- Admin-Login-System
- Deployment-Konfiguration

### ❌ ENTHÄLT NICHT:
- Lokale Datenbank-Dateien (.db)
- User-Upload-Dateien
- Backup-Ordner
- Cache-Dateien (__pycache__)
- Lokale Entwicklungstools

## 🔐 Standard-Login (Railway):
- **Benutzername:** admin
- **Passwort:** admin123
- **⚠️ WICHTIG:** Passwort sofort ändern!

## 📊 Statistik:
- **Python-Dateien:** 22
- **Templates:** 44
- **Migrations:** 22
- **Excel-Templates:** 3
- **Gesamt:** ~100 Dateien

---

**Ready for Production! 🎉**

Alle Dateien sind deployment-ready und enthalten keine lokalen Entwicklungsdaten.
