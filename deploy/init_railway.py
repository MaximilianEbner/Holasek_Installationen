#!/usr/bin/env python3
"""
Railway-spezifisches Initialisierungsskript
Erstellt automatisch einen Admin-Benutzer bei der ersten Bereitstellung
"""
import os
import sys
from app import app
from models import db, LoginAdmin, CompanySettings

def init_railway_database():
    """Initialisiert die Railway-Datenbank mit essentiellen Daten"""
    
    with app.app_context():
        print("🚀 Railway Datenbank-Initialisierung...")
        
        # Erstelle Tabellen falls sie nicht existieren
        db.create_all()
        
        # Erstelle Standard-Admin falls keiner existiert
        existing_admin = LoginAdmin.query.first()
        if not existing_admin:
            print("👤 Erstelle Standard-Admin-Benutzer...")
            admin_user = LoginAdmin()
            admin_user.create_login_admin(
                login_username="admin",
                login_password="admin123"  # WICHTIG: Nach dem ersten Login ändern!
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Standard-Admin erstellt:")
            print("   Benutzername: admin")
            print("   Passwort: admin123")
            print("   ⚠️  WICHTIG: Ändern Sie das Passwort sofort nach dem ersten Login!")
        else:
            print("ℹ️  Admin-Benutzer bereits vorhanden...")
        
        # Erstelle Grundeinstellungen falls sie nicht existieren
        basic_settings = [
            ("company_name", "Ihr Installationsbetrieb", "Name des Unternehmens"),
            ("address", "Ihre Adresse", "Firmenadresse"),
            ("city", "Ihre Stadt", "Stadt"),
            ("postal_code", "12345", "Postleitzahl"),
            ("phone", "+43 1 234567", "Telefonnummer"),
            ("email", "office@company.com", "E-Mail Adresse"),
            ("default_hourly_rate", "65.0", "Standard Stundensatz")
        ]
        
        for setting_name, setting_value, description in basic_settings:
            if not CompanySettings.query.filter_by(setting_name=setting_name).first():
                setting = CompanySettings(
                    setting_name=setting_name,
                    setting_value=setting_value,
                    description=description
                )
                db.session.add(setting)
        
        db.session.commit()
        print("✅ Railway-Datenbank erfolgreich initialisiert!")
        print("🌐 Die App ist jetzt bereit für die Nutzung!")

if __name__ == "__main__":
    init_railway_database()
