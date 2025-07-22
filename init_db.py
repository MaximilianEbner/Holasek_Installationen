#!/usr/bin/env python3
"""
Initialisierungsskript für die Holasek Installationsbetrieb Datenbank
Erstellt die Datenbank mit allen Tabellen und lädt Testdaten
"""

import os
import sys

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import app
from models import db, Customer, Quote, QuoteItem, QuoteSubItem, Supplier, CompanySettings, AcquisitionChannel, LoginAdmin
from datetime import date, timedelta

def init_database():
    """Initialisiert die Datenbank mit allen Tabellen und Testdaten"""
    
    with app.app_context():
        print("🗑️  Lösche alte Datenbank...")
        db.drop_all()
        
        print("🔧 Erstelle neue Datenbankstruktur...")
        db.create_all()
        
        print("� Erstelle Login-Admin...")
        
        # Login-Admin erstellen
        admin = LoginAdmin.create_login_admin('admin', 'admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Login-Admin erstellt (admin/admin123)")
        
        print("�📊 Erstelle Grunddaten...")
        
        # Erstelle Grundeinstellungen
        settings_data = [
            ("company_name", "innSAN Installationsbetrieb", "Name des Unternehmens"),
            ("address", "Musterstraße 1", "Firmenadresse"),
            ("city", "Wien", "Stadt"),
            ("postal_code", "1010", "Postleitzahl"),
            ("phone", "+43 1 234567", "Telefonnummer"),
            ("email", "office@innsan.at", "E-Mail Adresse"),
            ("default_hourly_rate", "65.0", "Standard Stundensatz")
        ]
        
        for setting_name, setting_value, description in settings_data:
            if not CompanySettings.query.filter_by(setting_name=setting_name).first():
                setting = CompanySettings(
                    setting_name=setting_name,
                    setting_value=setting_value,
                    description=description
                )
                db.session.add(setting)
        
        db.session.commit()
        print("✅ Grundeinstellungen erstellt")
        
        # Teste Lieferanten erstellen
        test_suppliers = [
            Supplier(name="Sanitär Großhandel GmbH", contact_person="Herr Meyer", email="meyer@sanitaer-gh.at", phone="+43 1 555-0101"),
            Supplier(name="Fliesen & Co", contact_person="Frau Weber", email="weber@fliesen-co.at", phone="+43 1 555-0202"),
            Supplier(name="Elektro Technik AG", contact_person="Herr Fischer", email="fischer@elektro-ag.at", phone="+43 1 555-0303")
        ]
        
        for supplier in test_suppliers:
            db.session.add(supplier)
        
        db.session.commit()
        print("✅ Test-Lieferanten erstellt")
        
        # Standard-Akquisekanäle erstellen
        acquisition_channels = [
            {
                'name': 'Homepage',
                'description': 'Kunde hat uns über die Webseite gefunden',
                'is_active': True
            },
            {
                'name': 'Telefon',
                'description': 'Kunde hat direkt angerufen',
                'is_active': True
            },
            {
                'name': 'Messe',
                'description': 'Kunde auf einer Messe kennengelernt',
                'is_active': True
            },
            {
                'name': 'Schauraum',
                'description': 'Kunde im Schauraum beraten',
                'is_active': True
            }
        ]
        
        for channel_data in acquisition_channels:
            channel = AcquisitionChannel(**channel_data)
            db.session.add(channel)
        
        db.session.commit()
        print("✅ Standard-Akquisekanäle erstellt")
        
        print("👥 Erstelle Testdaten...")
        
        # Testkunden erstellen
        customers = [
            Customer(
                salutation="Herr",
                first_name="Max", 
                last_name="Mustermann", 
                email="max.mustermann@email.com",
                phone="+43 664 1234567",
                address="Musterstraße 123",
                city="Wien",
                postal_code="1010",
                customer_manager="Franz Huber",
                acquisition_channel_id=1  # Homepage
            ),
            Customer(
                salutation="Frau",
                first_name="Maria", 
                last_name="Schmidt", 
                email="maria.schmidt@email.com",
                phone="+43 664 7654321",
                address="Testgasse 456",
                city="Graz",
                postal_code="8010",
                customer_manager="Anna Müller",
                acquisition_channel_id=2  # Telefon
            ),
            Customer(
                salutation="Herr",
                first_name="Johann", 
                last_name="Müller", 
                email="johann.mueller@email.com",
                phone="+43 664 9876543",
                address="Beispielweg 789",
                city="Salzburg", 
                postal_code="5020",
                customer_manager="Franz Huber",
                acquisition_channel_id=3  # Messe
            )
        ]
        
        for customer in customers:
            db.session.add(customer)
            
        db.session.commit()
        
        # Test-Angebot erstellen
        test_quote = Quote(
            quote_number="ANG-2025-001",
            customer_id=1,
            project_description="Komplette Badsanierung mit neuer Dusche, Waschtisch und Fliesenarbeiten",
            total_amount=0.0,
            status="Entwurf",
            valid_until=date.today() + timedelta(days=30),
            include_additional_info=True
        )
        
        db.session.add(test_quote)
        db.session.commit()
        
        print("✅ Datenbank erfolgreich initialisiert!")
        print(f"📁 Datenbank-Datei: {os.path.join(project_dir, 'instance', 'installation_business.db')}")
        print("🚀 Sie können nun die App starten mit: python app.py")

if __name__ == "__main__":
    init_database()
