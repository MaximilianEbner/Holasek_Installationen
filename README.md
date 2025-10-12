# 🏢 innSAN Installationsbetrieb - Management System

Eine vollständige webbasierte Flask-Anwendung zur Verwaltung von Installationsbetrieben mit modernem Design, umfassenden Funktionen und automatisierter Geschäftslogik.

## 📋 Überblick

Diese Anwendung ist ein komplettes ERP-System für Installationsbetriebe, das den gesamten Geschäftsprozess von der Kundenakquise über die Angebotserstellung bis zur Rechnungsstellung und Auftragsabwicklung abdeckt.

## 🚀 Live Demo

Die Anwendung läuft auf Railway (PostgreSQL) und ist über jeden modernen Browser zugänglich.
- **Standard Login:** admin / admin123 (nach dem ersten Start)

## ✨ Hauptfunktionen

### 📊 Dashboard & Analytics
- Interaktive Statistikkarten mit Direktnavigation
- Echtzeit-Übersicht: Kunden, offene Angebote, aktive Aufträge
- Anstehende Termine und Workflow-Status
- Schnellzugriff zu kritischen Funktionen

### � Intelligentes Angebotssystem
- **Template-System:** Vordefinierte Arbeitsschritte mit Standardzeiten
- **Dynamische Kalkulation:** Aufschläge (Standard 15%), Rabatte, automatische Preisberechnungen
- **Drei Preisanzeige-Modi:** Standard, Detailliert, Nur Gesamtsumme
- **Professional PDF-Export:** Corporate Design mit innSAN-Logo
- **Intelligente Positionen:** Hauptpositionen mit beliebigen Unterpositionen
- Status-Tracking: Entwurf → Gesendet → Angenommen/Abgelehnt

### 🔨 Auftragsmanagement
- **Automatische Auftragserstellung:** Aus angenommenen Angeboten
- **Lieferantenbestellungen:** Direkt aus Angebotspositionen generierbar
- **Arbeitsanweisungen:** Detaillierte Instruktionen für Monteure
- **Status-Verfolgung:** Von Beauftragung bis Fertigstellung
- **Terminplanung:** Integrierte Kalender-Funktionen

### 💰 Vollständiges Rechnungswesen
- **Anzahlungsrechnungen:** Automatisch berechnet aus Auftragssummen
- **Schlussrechnungen:** Mit Anzahlungsverrechnung
- **Mahnwesen:** Automatische Überfälligkeitsverfolgung
- **Professional PDF-Layout:** Angepasst an österreichische Standards
- **MwSt-Berechnung:** 20% Standard-Steuersatz
- **Status-Tracking:** Erstellt → Versendet → Bezahlt → Überfällig

### 🚚 Lieferantenintegration
- **Vollständige Lieferantenverwaltung:** Mit Kontaktdaten und E-Mail-Integration
- **Bestellsystem:** Automatisch aus Angebotspositionen
- **Status-Verfolgung:** Bestellt → Bestätigt → Geliefert
- **E-Mail-Integration:** Automatische Bestellbenachrichtigungen

### � Kundenworkflow-Management
- **6-Stufiger Workflow:**
  1. Termin vereinbaren
  2. 1. Termin vereinbart
  3. Angebot erstellen
  4. 2. Termin vereinbaren
  5. Warten auf Rückmeldung
  6. Kein Interesse
- **Automatische Status-Updates:** Basierend auf Termindaten
- **Akquisekanal-Tracking:** Woher kam der Kunde?
- **Notizen & Kommentare:** Für alle Termine und Interaktionen

### 🛠️ Umfassende Stammdatenverwaltung
- **Arbeitsschritte-Templates:** Kategorisiert (Abbruch, Duschtasse, Badewanne, WC, etc.)
- **Positionsvorlagen:** Hierarchische Struktur mit Unterpositionen
- **Akquisekanäle:** Website, Empfehlung, Werbung, etc.
- **Unternehmenseinstellungen:** Stundensatz, MwSt, Firmenadresse
- **Artikel-Katalog:** Für wiederkehrende Materialien

### 🎨 Modernes UI/UX Design
- **Corporate Design:** innSAN-Branding in Orange/Grün
- **Responsive Bootstrap 5:** Optimiert für Desktop, Tablet, Mobile
- **Intuitive Navigation:** Sidebar mit Hauptfunktionen
- **Smart Cards:** Dashboard mit Live-Statistiken
- **Animations:** Sanfte Hover-Effekte und Übergänge
- **Accessibility:** WCAG-konform und benutzerfreundlich

### 🔐 Sicherheit & Administration
- **Login-System:** Passwort-Hash mit Werkzeug Security
- **Session Management:** Sichere Flask-Sessions
- **Backup-System:** Automatische Excel/SQLite-Backups
- **Datenmigration:** Flask-Migrate für Schema-Updates
- **Railway-Integration:** Cloud-ready PostgreSQL-Support

## 🏗️ Technische Architektur

### 🌐 Frontend-Stack
- **Bootstrap 5.1.3** - Modernes, responsives CSS-Framework
- **Font Awesome 6.0** & **Bootstrap Icons** - Umfassende Icon-Bibliothek
- **Custom CSS** - Maßgeschneidertes innSAN Corporate Design
- **JavaScript/jQuery** - Dynamische UI-Interaktionen
- **Responsive Design** - Mobile-first Ansatz

### ⚙️ Backend-Framework
- **Flask 3.1.1** - Modernes Python Web Framework
- **Flask-SQLAlchemy 3.0.5** - ORM für Datenbankoperationen
- **Flask-Migrate 4.0.5** - Datenbank-Versionskontrolle
- **Flask-WTF 1.2.2** - Sichere Formular-Verarbeitung
- **Werkzeug Security** - Passwort-Hashing und Sicherheit

### 💾 Datenbank-Systeme
- **PostgreSQL** - Production (Railway Cloud)
- **SQLite** - Development & Backup-System
- **SQLAlchemy ORM** - Datenbankabstraktion
- **Alembic Migrations** - Schema-Versionierung

### 📄 PDF & Dokumenten-Engine
- **ReportLab 4.2.2** - Professionelle PDF-Generierung
- **Pillow 10.4.0** - Bildverarbeitung für Logos
- **PyPDF** - PDF-Manipulation und -Kombinierung
- **Corporate Design** - Automatisches Logo und Layout

### 📊 Excel & Datenexport
- **OpenPyXL 3.1.5** - Native Excel-Erstellung
- **Pandas 2.2.2** - Datenverarbeitung für Exporte
- **CSV Export** - Standardisierte Datenausgabe

### 🚀 Deployment & Production
- **Gunicorn 21.2.0** - WSGI HTTP Server
- **Railway.app** - Cloud-Hosting-Plattform  
- **PostgreSQL Cloud** - Managed Database Service
- **Python 3.11** - Runtime Environment
- **Git Integration** - Automatische Deployments

## � Geschäftsprozess-Workflow

### 1️⃣ Kundenakquise & Ersterfassung
- **Kunde erfassen:** Name, Kontaktdaten, Akquisekanal
- **Status:** "1. Termin vereinbaren"
- **Automatik:** Nächste Aktion wird im Dashboard angezeigt

### 2️⃣ Terminplanung & Vor-Ort-Beratung
- **1. Termin vereinbaren** mit Kalendereintrag
- **Vor-Ort-Besichtigung** mit Notizen und Fotos
- **Status-Update:** Automatisch zu "Angebot erstellen"

### 3️⃣ Professionelle Angebotserstellung
- **Template-basiert:** Arbeitsschritte aus Standardkatalog auswählen
- **Intelligente Kalkulation:** Automatische Preisberechnungen mit Aufschlag
- **PDF-Export:** Corporate Design mit Logo, drei Detailgrade
- **Status:** Entwurf → Gesendet → Warten auf Rückmeldung

### 4️⃣ Auftragsabwicklung
- **Bei Annahme:** Automatische Auftragserstellung aus Angebot
- **Lieferantenbestellungen:** Direkt aus Positionen generierbar
- **Arbeitsanweisungen:** Detaillierte Montageinstruktionen
- **Terminplanung:** Start-/Endtermine mit Status-Tracking

### 5️⃣ Rechnungsstellung & Zahlungsabwicklung
- **Anzahlungsrechnung:** Automatisch aus Auftragssumme (z.B. 50%)
- **Schlussrechnung:** Bei Fertigstellung mit Anzahlungsverrechnung
- **Status-Tracking:** Erstellt → Versendet → Bezahlt → Überfällig
- **Mahnwesen:** Automatische Überfälligkeitsverfolgung

### 6️⃣ Nachbearbeitung & Kundenbindung
- **Projektabschluss:** Dokumentation und Archivierung
- **Kundenfeedback:** Notizen für zukünftige Projekte
- **Wiederholungsgeschäft:** Kunden bleiben im System

## 🔧 Installation & Setup

### 📋 Voraussetzungen
- **Python 3.11+**
- **Git** für Repository-Verwaltung
- **PostgreSQL** (für Production) oder **SQLite** (Development)

### 🛠️ Lokale Entwicklungsumgebung

```bash
# 1. Repository klonen
git clone <repository-url>
cd InstallationApp_Distribution_20251012_LAUNCH

# 2. Virtual Environment erstellen
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Datenbank initialisieren
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()

# 5. Admin-Account erstellen (einmalig)
# http://localhost:5000/init-admin aufrufen

# 6. Anwendung starten
python app.py
```

### ☁️ Production-Deployment (Railway)

Die Anwendung ist vollständig für **Railway.app** optimiert:

**Automatische Konfiguration:**
- `Procfile` → Gunicorn WSGI Server
- `runtime.txt` → Python 3.11 Runtime  
- `requirements.txt` → Alle Dependencies
- `DATABASE_URL` → PostgreSQL automatisch konfiguriert

**Deployment-Schritte:**
1. Repository mit Railway verbinden
2. PostgreSQL-Service hinzufügen
3. Environment Variables werden automatisch gesetzt
4. **Erste Anmeldung:** `/init-admin` → admin/admin123

### 🔐 Sicherheitseinstellungen

```python
# Wichtige Konfigurationen in config.py
SECRET_KEY = 'production-secret-key-hier-einfügen'
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
```

**Nach dem ersten Login:**
- Standard-Passwort **sofort ändern**
- Firmeneinstellungen konfigurieren
- Akquisekanäle anpassen
- Templates und Arbeitsschritte überprüfen

## ⚙️ Konfiguration & Settings

### 🌐 Environment Variables (Production)
```bash
DATABASE_URL=postgresql://...           # PostgreSQL Connection String
SECRET_KEY=your-secret-key-here        # Flask Session Key (Railway auto-generated)
FLASK_ENV=production                   # Production Mode
PORT=5000                              # Port (Railway managed)
```

### 🏢 Unternehmenseinstellungen (im System konfigurierbar)
- **Firmenname:** innSAN Installationsbetrieb
- **Stundensatz:** 95,00 € (Standard, anpassbar)
- **MwSt-Satz:** 20% (Österreich-Standard)
- **Aufschlag:** 15% (Standard bei Angeboten)
- **Firmenadresse, Kontaktdaten, UID-Nummer**

### � Dateistruktur
```
InstallationApp/
├── app.py                 # Hauptanwendung mit Flask Routes
├── models.py              # SQLAlchemy Datenbankmodelle
├── forms.py               # WTForms Formular-Definitionen
├── utils.py               # Utility-Funktionen
├── work_steps.py          # Arbeitsschritte-Konfiguration
├── pdf_export.py          # PDF-Generation für Angebote
├── invoice_pdf.py         # PDF-Generation für Rechnungen
├── backup_system.py       # Backup & Restore Funktionen
├── config.py              # Flask-Konfiguration
├── requirements.txt       # Python Dependencies
├── Procfile              # Gunicorn-Konfiguration
├── runtime.txt           # Python-Version
├── templates/            # HTML Jinja2-Templates
├── static/              # CSS, JS, Bilder
├── migrations/          # Datenbank-Migrationen
└── instance/           # SQLite DB (Development)
```

## 🎯 Feature-Details & Funktionen

### 🧮 Intelligente Preiskalkulation
- **Drei Kalkulationsmodi:**
  - **Standard:** Basis + Aufschlag sichtbar
  - **Detailliert:** Alle Einzelpreise und Berechnungen
  - **Nur Gesamt:** Nur Endpreis für Kunden
- **Automatische Berechnungen:** Fläche (L×B), Volumen (L×B×H)
- **Rabattsystem:** Prozentuale Nachlässe
- **MwSt-Integration:** Automatisch 20% auf Nettobeträge

### 🔍 Erweiterte Suchfunktionen
- **Global Search:** Kunden, Angebote, Aufträge durchsuchbar
- **Autocomplete:** Intelligente Kundensuche bei Angebotserstellung
- **Filter-Optionen:** Status, Datum, Betrag, Akquisekanal
- **Sortierung:** Nach allen Spalten möglich

### 💾 Umfassendes Backup-System
```python
# Verfügbare Backup-Formate:
- Excel (.xlsx) - Alle Tabellen in separaten Sheets
- SQLite (.db) - Komplette Datenbank-Kopie
- CSV - Einzelne Tabellen für externe Analyse
```

### 📊 Dashboard-Analytics
- **Live-Statistiken:** Kunden, offene Angebote, aktive Aufträge
- **Workflow-Status:** Anstehende Termine, offene Rechnungen
- **Quick Actions:** Direktzugriff auf häufige Funktionen
- **Recent Activity:** Letzte Kundeninteraktionen

## 🎨 Corporate Design System

### 🎨 Farbpalette
```css
/* Primärfarben */
--primary-green: #28a745      /* Hauptgrün für Buttons */
--primary-orange: #CC5500     /* innSAN Orange für Akzente */
--success: #2ecc71           /* Erfolgsmeldungen */
--warning: #f39c12           /* Warnungen */
--danger: #e74c3c            /* Fehler */

/* UI-Farben */
--background: #f8f9fa        /* Sidebar und Hintergründe */
--card-shadow: rgba(0,0,0,0.1) /* Schatten für Cards */
```

### 🎭 UI-Komponenten
- **Cards mit Hover:** Lift-Effekt bei Mouse-Over
- **Responsive Grid:** Bootstrap-basiertes Layout
- **Status-Badges:** Farbcodierte Zustandsanzeigen
- **Progress Indicators:** Workflow-Fortschritt visuell
- **Mobile Optimization:** Touch-freundliche Buttons

### 📱 Responsive Breakpoints
```css
/* Tablet */ @media (min-width: 768px)  - Sidebar wird sichtbar
/* Desktop */ @media (min-width: 1200px) - Vollständiges Layout
/* Mobile */ @media (max-width: 767px)  - Gestapeltes Layout
```

## � Datenbank-Schema

### 🏗️ Haupttabellen
- **Customer** - Kundendaten mit Workflow-Status
- **Quote** - Angebote mit Positionen und Preiskalkulation
- **Order** - Aufträge aus angenommenen Angeboten
- **Invoice** - Rechnungen mit Mahnfunktion
- **Supplier** - Lieferanten und Bestellsystem

### 🔗 Beziehungsstruktur
```
Customer 1:n Quote 1:n QuoteItem 1:n QuoteSubItem
Quote 1:1 Order 1:n WorkInstruction
Order 1:n Invoice 1:n InvoicePosition
Supplier 1:n SupplierOrder 1:n SupplierOrderItem
```

## 🚀 Version & Updates

### 📅 Aktuelle Version: 2.0 (Oktober 2025)
**Neue Features:**
- ✅ Vollständiges Rechnungssystem mit Mahnwesen
- ✅ Erweiterte PDF-Layouts für Angebote und Rechnungen
- ✅ Railway-Deployment mit PostgreSQL
- ✅ Lieferantenintegration mit Bestellsystem
- ✅ Backup & Restore System
- ✅ Responsive Mobile Design

### 🔄 Geplante Features (Roadmap)
- 📧 E-Mail-Integration für automatische Versendung
- 📊 Erweiterte Reporting-Funktionen
- 📱 Progressive Web App (PWA)
- 🔐 Multi-User-System mit Rollenverwaltung
- 🗄️ Dokumentenmanagement mit Cloud-Storage

## 🤝 Support & Wartung

### 📞 Technischer Support
- **Entwickler:** Maximilian Ebner
- **E-Mail:** [Support-E-Mail]
- **Updates:** Automatisch via Railway-Integration

### 🐛 Bug Reports & Feature Requests
- GitHub Issues für Entwickler-Feedback
- Direct Contact für Business-Anfragen
- Regelmäßige Updates und Verbesserungen

Bei Fragen oder Problemen:
- Technischer Support verfügbar
- Dokumentation in der Anwendung
- Benutzerhandbuch integriert

---

**Entwickelt für Installationsbetrieb Holasek** 🔧
*Professionelle Geschäftsverwaltung im modernen Web*
