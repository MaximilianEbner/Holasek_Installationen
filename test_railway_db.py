#!/usr/bin/env python3
"""
Railway Datenbank Test
Einfacher Test der PostgreSQL-Verbindung auf Railway
"""

import os

def test_railway_database():
    """Testet die Railway-Datenbankverbindung"""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL nicht gefunden!")
        return False
    
    print(f"🔍 Teste Datenbankverbindung...")
    print(f"📊 URL: {database_url.split('@')[0] if '@' in database_url else 'local'}@***")
    
    try:
        # Importiere und erstelle App
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Test 1: Verbindung testen
            from sqlalchemy import text
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Datenbankverbindung: {row[0] == 1}")
            
            # Test 2: Tabellen prüfen
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Gefundene Tabellen ({len(tables)}): {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
            
            # Test 3: Admin-Daten prüfen
            if 'login_admins' in tables:
                from models import LoginAdmin
                admin_count = LoginAdmin.query.count()
                print(f"👤 Admin-Benutzer: {admin_count}")
                
                if admin_count > 0:
                    admin = LoginAdmin.query.first()
                    print(f"📝 Erster Admin: {admin.login_username}")
            else:
                print("⚠️ login_admins Tabelle nicht gefunden!")
            
            # Test 4: Settings prüfen
            if 'company_settings' in tables:
                from models import CompanySettings
                settings_count = CompanySettings.query.count()
                print(f"⚙️ Einstellungen: {settings_count}")
            else:
                print("⚠️ company_settings Tabelle nicht gefunden!")
            
            return True
            
    except Exception as e:
        print(f"❌ Datenbanktest fehlgeschlagen: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_railway_database()
    exit(0 if success else 1)
