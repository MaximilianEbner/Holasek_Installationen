#!/usr/bin/env python3
"""
Railway Database Setup Script
Führt eine vollständige Datenbank-Initialisierung durch
"""
import os
import sys

# Stelle sicher, dass wir die App importieren können
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_railway_database():
    """Vollständige Datenbank-Setup für Railway"""
    
    print("🚀 Railway Database Setup gestartet...")
    
    try:
        # App und Models importieren
        from app import app
        from models import db, LoginAdmin, CompanySettings
        
        with app.app_context():
            print("📋 Prüfe Datenbank-Verbindung...")
            
            # Überprüfe ob wir PostgreSQL oder SQLite verwenden
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"📊 Datenbank URL: {db_url[:50]}...")
            
            if 'postgresql' in db_url:
                print("✅ PostgreSQL Datenbank erkannt")
            elif 'sqlite' in db_url:
                print("⚠️  SQLite Datenbank erkannt")
            
            print("🔧 Erstelle alle Tabellen...")
            db.create_all()
            
            print("👤 Prüfe Admin-Benutzer...")
            existing_admin = LoginAdmin.query.first()
            
            if existing_admin:
                print(f"ℹ️  Admin-Benutzer bereits vorhanden: {existing_admin.login_username}")
            else:
                print("➕ Erstelle Standard-Admin...")
                admin_user = LoginAdmin()
                admin_user.create_login_admin(
                    login_username="admin",
                    login_password="admin123"
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin-Benutzer erstellt: admin/admin123")
            
            # Grundeinstellungen prüfen/erstellen
            print("⚙️  Prüfe Grundeinstellungen...")
            if not CompanySettings.query.first():
                basic_settings = [
                    ("company_name", "Holasek Installationsbetrieb", "Name des Unternehmens"),
                    ("address", "Ihre Adresse", "Firmenadresse"),
                    ("city", "Ihre Stadt", "Stadt"),
                    ("postal_code", "12345", "Postleitzahl"),
                    ("phone", "+43 1 234567", "Telefonnummer"),
                    ("email", "office@holasek.at", "E-Mail Adresse"),
                    ("default_hourly_rate", "95.0", "Standard Stundensatz")
                ]
                
                for setting_name, setting_value, description in basic_settings:
                    setting = CompanySettings(
                        setting_name=setting_name,
                        setting_value=setting_value,
                        description=description
                    )
                    db.session.add(setting)
                
                db.session.commit()
                print("✅ Grundeinstellungen erstellt")
            else:
                print("ℹ️  Grundeinstellungen bereits vorhanden")
            
            # Finale Prüfung
            admin_count = LoginAdmin.query.count()
            settings_count = CompanySettings.query.count()
            
            print("\n" + "="*50)
            print("🎉 RAILWAY DATABASE SETUP ERFOLGREICH!")
            print("="*50)
            print(f"👥 Admin-Benutzer: {admin_count}")
            print(f"⚙️  Einstellungen: {settings_count}")
            print("\n🔐 LOGIN-DATEN:")
            print("   Benutzername: admin")
            print("   Passwort: admin123")
            print("   ⚠️  WICHTIG: Passwort sofort ändern!")
            print("="*50)
            
            return True
            
    except Exception as e:
        print(f"❌ FEHLER beim Database Setup: {e}")
        print(f"Fehler-Typ: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_railway_database()
    sys.exit(0 if success else 1)
