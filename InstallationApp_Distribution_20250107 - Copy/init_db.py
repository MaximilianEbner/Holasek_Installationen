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

from app import app, db, Customer, Quote, QuoteItem, QuoteSubItem, Supplier, PositionTemplate, load_position_templates, load_suppliers
from datetime import date, timedelta

def init_database():
    """Initialisiert die Datenbank mit allen Tabellen und Testdaten"""
    
    with app.app_context():
        print("🗑️  Lösche alte Datenbank...")
        db.drop_all()
        
        print("🔧 Erstelle neue Datenbankstruktur...")
        db.create_all()
        
        print("📊 Lade Excel-Templates...")
        
        # Lade Positionsvorlagen
        if load_position_templates():
            print("✅ Positionsvorlagen erfolgreich geladen")
        else:
            print("❌ Fehler beim Laden der Positionsvorlagen")
            
        # Lade Lieferanten
        if load_suppliers():
            print("✅ Lieferanten erfolgreich geladen")
        else:
            print("❌ Fehler beim Laden der Lieferanten")
        
        print("👥 Erstelle Testdaten...")
        
        # Testkunden erstellen
        customers = [
            Customer(
                first_name="Max", 
                last_name="Mustermann", 
                email="max.mustermann@email.com",
                phone="+43 664 1234567",
                address="Musterstraße 123",
                city="Wien",
                postal_code="1010"
            ),
            Customer(
                first_name="Maria", 
                last_name="Schmidt", 
                email="maria.schmidt@email.com",
                phone="+43 664 7654321",
                address="Testgasse 456",
                city="Graz",
                postal_code="8010"
            ),
            Customer(
                first_name="Johann", 
                last_name="Müller", 
                email="johann.mueller@email.com",
                phone="+43 664 9876543",
                address="Beispielweg 789",
                city="Salzburg", 
                postal_code="5020"
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
