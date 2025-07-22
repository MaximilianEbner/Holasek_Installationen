# 🏢 Installations Business App

Eine professionelle Webanwendung für Installationsbetriebe zur Verwaltung von Kunden, Angeboten, Aufträgen und Lieferantenbestellungen.

## 🚀 Live Demo
Die App läuft auf Railway: [Ihre Railway URL hier einfügen]

## ✨ Hauptfunktionen

### � Kundenverwaltung
- Vollständige Kundendatenbank
- Kundenhistorie und Kontaktdaten
- Schnelle Suche und Filter

### 📄 Angebotssystem
- **Klassische Positionen**: Produkte und Dienstleistungen
- **Arbeitspositionen**: Vordefinierte Arbeitsschritte mit Kategorien
- Automatische Preisberechnung inkl. MwSt.
- PDF-Export mit professionellem Layout

### 🔧 Arbeitsschritte-Bibliothek
- Kategorien: Abbruch, Duschtasse, Badewanne, WC, Sanitär, etc.
- Standardzeiten und Preise
- Individuelle Anpassungen möglich

### 📋 Auftragsverwaltung
- Angebote zu Aufträgen konvertieren
- Status-Tracking
- Lieferantenbestellungen verwalten

### 💾 Datensicherung
- Automatische CSV-Backups
- Excel-Export aller Daten
- SQLite-Datenbank-Backups

### � Admin-System
- Sichere Benutzeranmeldung
- Benutzerverwaltung für Admins
- Passwort-geschützte Bereiche

## 🛠️ Technologie

- **Backend**: Python Flask, SQLAlchemy
- **Frontend**: Bootstrap 5, responsive Design
- **Datenbank**: SQLite (lokal) / PostgreSQL (Production)
- **PDF-Generation**: ReportLab
- **Excel-Support**: openpyxl

## 📋 Installation (Lokal)

```bash
# Repository klonen
git clone [Ihr Repository]
cd InstallationApp

# Virtual Environment erstellen
python -m venv venv
venv\Scripts\activate  # Windows
# oder: source venv/bin/activate  # macOS/Linux

# Dependencies installieren
pip install -r requirements.txt

# Datenbank initialisieren
python init_db.py

# App starten
python app.py
```

Die App ist dann unter `http://localhost:5000` erreichbar.

## 🚢 Deployment (Railway)

1. Repository auf GitHub pushen
2. Railway-Account erstellen
3. Repository mit Railway verbinden
4. Environment Variables setzen (siehe unten)
5. Automatisches Deployment

### Environment Variables für Railway:
```
SECRET_KEY=ihr-geheimer-schluessel-hier
DATABASE_URL=postgresql://... (wird automatisch gesetzt)
```

## 📖 Systemvoraussetzungen

- **Lokal**: Python 3.13+, moderner Browser
- **Cloud**: Läuft auf Railway/Heroku/etc.
- **Browser**: Chrome, Firefox, Edge, Safari

## 📚 Dokumentation

Siehe `BENUTZERHANDBUCH.txt` für detaillierte Bedienungsanleitung.

## 🆘 Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Dokumentation
2. Erstellen Sie ein Issue auf GitHub
3. Kontaktieren Sie den Support

## 📄 Lizenz

[Ihre Lizenz hier einfügen]

---

**Version 2.0** - Juli 2025  
Mit Admin-System und erweiterten Funktionen
