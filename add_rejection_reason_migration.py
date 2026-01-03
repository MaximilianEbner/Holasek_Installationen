"""
Migration Script: Add rejection_reason column to customer table
Dieses Skript fügt das Feld 'rejection_reason' zur Customer-Tabelle hinzu.
Unterstützt sowohl SQLite als auch PostgreSQL.
"""

from app import create_app
from models import db
from sqlalchemy import inspect, text

def check_column_exists(table_name, column_name):
    """Prüft ob eine Spalte bereits existiert"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_rejection_reason_column():
    """Fügt die rejection_reason Spalte zur customer Tabelle hinzu"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("MIGRATION: Add rejection_reason to customer table")
        print("=" * 60)
        
        # Prüfen ob Spalte bereits existiert
        if check_column_exists('customer', 'rejection_reason'):
            print("✓ Spalte 'rejection_reason' existiert bereits!")
            return
        
        try:
            # Datenbank-Typ ermitteln
            db_type = db.engine.url.drivername
            print(f"📊 Datenbank-Typ: {db_type}")
            
            # Migration durchführen
            print("\n🔧 Füge Spalte 'rejection_reason' hinzu...")
            
            if 'sqlite' in db_type:
                # SQLite
                db.session.execute(text(
                    "ALTER TABLE customer ADD COLUMN rejection_reason TEXT"
                ))
            else:
                # PostgreSQL
                db.session.execute(text(
                    "ALTER TABLE customer ADD COLUMN rejection_reason TEXT"
                ))
            
            db.session.commit()
            print("✓ Spalte erfolgreich hinzugefügt!")
            
            # Verifizierung
            if check_column_exists('customer', 'rejection_reason'):
                print("\n✓ Migration erfolgreich abgeschlossen!")
                print("  - Spalte 'rejection_reason' wurde zur 'customer' Tabelle hinzugefügt")
            else:
                print("\n❌ Fehler: Spalte wurde nicht gefunden!")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Fehler bei der Migration: {str(e)}")
            raise
        
        print("=" * 60)

if __name__ == '__main__':
    add_rejection_reason_column()
