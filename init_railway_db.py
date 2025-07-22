#!/usr/bin/env python3
"""
Railway-Datenbank Initialisierungsskript
Dieses Skript initialisiert die PostgreSQL-Datenbank auf Railway mit allen notwendigen Tabellen und Daten.
"""

import os
import sys

def init_railway_database():
    """Initialisiert die Railway-Datenbank"""
    
    # Railway stellt DATABASE_URL automatisch bereit
    if not os.environ.get('DATABASE_URL'):
        print("❌ Fehler: DATABASE_URL nicht gefunden!")
        print("Dieses Skript muss auf Railway ausgeführt werden.")
        sys.exit(1)
    
    print("🚀 Initialisiere Railway-Datenbank...")
    print(f"📊 Datenbank URL: {os.environ.get('DATABASE_URL', '').split('@')[0]}@***")
    
    try:
        # Importiere App-Factory
        from app import create_app, db
        
        # Erstelle App-Instanz
        app = create_app()
        
        with app.app_context():
            # Importiere alle Modelle
            from models import (LoginAdmin, Customer, Quote, QuoteItem, QuoteSubItem, 
                              Supplier, CompanySettings, AcquisitionChannel, 
                              PositionTemplate, PositionTemplateSubItem, Order,
                              SupplierOrder, SupplierOrderItem, QuoteRejection)
            
            print("📋 Erstelle alle Tabellen...")
            db.create_all()
            
            # Prüfe ob bereits Daten vorhanden sind
            admin_count = LoginAdmin.query.count()
            if admin_count > 0:
                print(f"✅ Datenbank bereits initialisiert ({admin_count} Admin(s) gefunden)")
                return
            
            print("👤 Erstelle Standard-Admin...")
            admin = LoginAdmin.create_login_admin('admin', 'admin123')
            db.session.add(admin)
            
            print("⚙️ Erstelle Grundeinstellungen...")
            settings_data = [
                ("company_name", "innSAN Installationsbetrieb", "Name des Unternehmens"),
                ("address", "Musterstraße 1", "Firmenadresse"), 
                ("city", "Wien", "Stadt"),
                ("postal_code", "1010", "Postleitzahl"),
                ("country", "Österreich", "Land"),
                ("phone", "+43 1 234 5678", "Telefonnummer"),
                ("email", "office@innsan.at", "E-Mail-Adresse"),
                ("website", "www.innsan.at", "Website"),
                ("hourly_rate", "95.0", "Standard-Stundensatz in Euro"),
                ("vat_rate", "20.0", "Mehrwertsteuersatz in Prozent")
            ]
            
            for key, value, description in settings_data:
                setting = CompanySettings(key=key, value=value, description=description)
                db.session.add(setting)
            
            print("🏢 Erstelle Standard-Akquisekanäle...")
            channels = [
                "Website",
                "Empfehlung", 
                "Google Ads",
                "Social Media",
                "Messe/Event",
                "Direktakquise",
                "Sonstiges"
            ]
            
            for channel_name in channels:
                channel = AcquisitionChannel(name=channel_name, is_active=True)
                db.session.add(channel)
            
            # Commit alle Änderungen
            print("💾 Speichere Daten...")
            db.session.commit()
            
            print("✅ Railway-Datenbank erfolgreich initialisiert!")
            print(f"👤 Standard-Admin: admin / admin123")
            print(f"📊 {len(settings_data)} Einstellungen erstellt")
            print(f"🏢 {len(channels)} Akquisekanäle erstellt")
            
    except Exception as e:
        print(f"❌ Fehler bei der Initialisierung: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    init_railway_database()
