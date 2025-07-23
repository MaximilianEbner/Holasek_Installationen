# 🏢 Installationsbetrieb Holasek - Management System

Eine vollständige webbasierte Anwendung zur Verwaltung von Installationsbetrieben mit modernem Design und umfassenden Funktionen.

## 🚀 Live Demo

Die Anwendung läuft auf Railway und ist über jeden modernen Browser zugänglich.

## ✨ Hauptfunktionen

### 📊 Dashboard
- Interaktive Statistikkarten mit Navigation
- Übersicht über Kunden, Angebote und Aufträge
- Anstehende Termine und letzte Aktivitäten
- Schnellzugriff zu wichtigen Funktionen

### 👥 Kundenverwaltung
- Vollständige Kundendatenbank
- Kontaktinformationen und Akquisekanäle
- Suchfunktion und Filter
- Kundenhistorie

### 📋 Angebotssystem
- Professionelle Angebotserstellung
- Template-basierte Positionen mit Unterpositionen
- Dynamische Berechnungen (Länge, Breite, Höhe, Fläche, Volumen)
- PDF-Export mit Corporate Design
- Status-Tracking (Entwurf → Versendet → Angenommen/Abgelehnt)

### 🔨 Auftragsverwaltung
- Automatische Aufragserstellung aus angenommenen Angeboten
- Terminplanung und Status-Verfolgung
- Arbeitsanweisungen und Dokumentation
- Integration mit Rechnungssystem

### 💰 Rechnungswesen
- Anzahlungs- und Schlussrechnungen
- Automatische Berechnung aus Aufträgen
- Status-Tracking (Erstellt → Versendet → Bezahlt)
- Überfälligkeits-Management
- PDF-Export

### 🚚 Lieferantenverwaltung
- Lieferantendatenbank
- Bestellsystem mit Status-Verfolgung
- Integration in Angebots- und Auftragsprozess

### 🎨 Design & UX
- Modernes, responsives Bootstrap-Design
- Einheitliches grünes Farbschema
- Sanfte Animationen und Hover-Effekte
- Mobile-optimierte Darstellung
- Intuitive Navigation

### 🛠️ Stammdaten
- Positionsvorlagen-Verwaltung
- Arbeitsschritte-Konfiguration
- Akquisekanal-Management
- Unternehmenseinstellungen
- Einheitliche Verwaltungsoberfläche

### 🔐 Administration
- Benutzerverwaltung
- Backup-System (CSV, Excel, SQLite)
- Login-System mit Session-Management

## 🛠️ Technische Details

### Frontend
- **Bootstrap 5.1.3** - Modernes CSS Framework
- **Font Awesome 6.0** - Icons
- **Bootstrap Icons** - Zusätzliche Icons
- **Responsive Design** - Mobile-optimiert

### Backend
- **Flask 3.1.1** - Python Web Framework
- **SQLAlchemy 1.4.54** - ORM
- **Flask-Migrate** - Datenbank-Migrationen
- **Flask-Login** - Authentifizierung
- **Flask-WTF** - Formular-Handling

### Datenbank
- **PostgreSQL** (Production auf Railway)
- **SQLite** (Development/Backup)

### PDF-Generation
- **ReportLab 4.2.2** - PDF-Erstellung
- **Pillow** - Bildverarbeitung

### Excel-Support
- **OpenPyXL** - Excel-Import/Export

### Deployment
- **Gunicorn** - WSGI Server
- **Railway** - Cloud Platform
- **Python 3.11** - Runtime

## 📦 Installation (Development)

```bash
# Repository klonen
git clone <repository-url>
cd InstallationApp

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt

# Datenbank initialisieren
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Anwendung starten
python app.py
```

## 🚀 Deployment auf Railway

Die Anwendung ist für Railway optimiert:

- **Procfile**: Gunicorn-Konfiguration
- **runtime.txt**: Python 3.11
- **requirements.txt**: Alle Dependencies
- **Automatische PostgreSQL-Integration**

## 🎯 Workflow

1. **Kunde anlegen** → Kontaktdaten erfassen
2. **Angebot erstellen** → Templates verwenden, Positionen hinzufügen
3. **PDF senden** → Professionelles Angebot an Kunde
4. **Auftrag generieren** → Bei Annahme automatisch erstellen
5. **Termine planen** → Arbeitszeiten koordinieren
6. **Rechnung stellen** → Anzahlung/Schlussrechnung
7. **Status verfolgen** → Bis zur Bezahlung

## 🔧 Konfiguration

### Umgebungsvariablen (Railway)
- `DATABASE_URL` - PostgreSQL Connection String
- `SECRET_KEY` - Flask Secret Key
- `FLASK_ENV` - production

### Lokale Entwicklung
- SQLite-Datenbank in `instance/`
- Debug-Modus aktiviert
- Template-Auto-Reload

## 📱 Browser-Unterstützung

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile Browsers

## 📈 Features im Detail

### Template-System
- Vordefinierte Positionsvorlagen
- Unterpositionen mit Mengen und Preisen
- Aktivierbare Felder (Länge, Breite, Höhe)
- Automatische Flächen- und Volumenberechnung

### Suchfunktionen
- Autocomplete in Auftragsauswahl
- Filter in allen Übersichten
- Globale Suchfunktion

### Backup-System
- CSV-Export für Excel
- Native Excel-Export
- SQLite-Datenbank-Download
- Automatische Datensicherung

## 🎨 Design-System

### Farben
- **Primär**: Sanftes Grün (#28a745)
- **Sekundär**: Bootstrap-Standardfarben
- **Akzente**: Warnsignale und Status-Badges

### Komponenten
- Hover-Effekte mit Lift-Animation
- Sanfte Übergänge (0.3s)
- Konsistente Button-Styles
- Responsive Card-Layout

## 🔄 Version History

- **v1.0** (Juli 2025) - Erste vollständige Version
- Kundenverwaltung, Angebote, Aufträge, Rechnungen
- Template-System, PDF-Export
- Moderne UI mit grünem Design
- Railway-Deployment-ready

## 🤝 Support

Bei Fragen oder Problemen:
- Technischer Support verfügbar
- Dokumentation in der Anwendung
- Benutzerhandbuch integriert

---

**Entwickelt für Installationsbetrieb Holasek** 🔧
*Professionelle Geschäftsverwaltung im modernen Web*
