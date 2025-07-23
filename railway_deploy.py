#!/usr/bin/env python3
"""
Railway Deployment Skript
Führt einmalig die Datenbank-Initialisierung aus
"""

import os
import sys

def deploy_to_railway():
    """Deployment auf Railway mit Datenbank-Initialisierung"""
    
    print("🚀 Railway Deployment gestartet...")
    
    # Importiere App
    from app import create_app, db
    app = create_app()
    
    with app.app_context():
        print("📊 Prüfe Datenbankverbindung...")
        
        try:
            # Test der Datenbankverbindung
            from sqlalchemy import text
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                print("✅ Datenbankverbindung erfolgreich")
        except Exception as e:
            print(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
            sys.exit(1)
        
        # Prüfe ob Tabellen existieren
        try:
            from models import LoginAdmin
            admin_count = LoginAdmin.query.count()
            print(f"📋 Gefundene Admins: {admin_count}")
            
            if admin_count == 0:
                print("🔧 Initialisiere Datenbank...")
                exec(open('init_railway_db.py').read())
            else:
                print("✅ Datenbank bereits initialisiert")
                
        except Exception as e:
            print(f"🔧 Tabellen nicht gefunden, erstelle sie: {e}")
            # Führe vollständige Initialisierung aus
            exec(open('init_railway_db.py').read())
    
    print("🎉 Railway Deployment abgeschlossen!")

if __name__ == '__main__':
    deploy_to_railway()
