#!/usr/bin/env python3
"""
Initialisierung der Akquisekanäle
Dieses Skript erstellt die Standard-Akquisekanäle wenn sie noch nicht existieren.
"""

from app import app, db
from models import AcquisitionChannel

def init_acquisition_channels():
    """Erstellt die Standard-Akquisekanäle wenn sie noch nicht existieren."""
    
    with app.app_context():
        # Überprüfe ob bereits Kanäle existieren
        existing_count = AcquisitionChannel.query.count()
        
        if existing_count > 0:
            print(f"Es existieren bereits {existing_count} Akquisekanäle.")
            return
        
        # Standard-Akquisekanäle definieren
        default_channels = [
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
        
        # Erstelle die Kanäle
        created_count = 0
        for channel_data in default_channels:
            channel = AcquisitionChannel(**channel_data)
            db.session.add(channel)
            created_count += 1
            print(f"Erstellt: {channel_data['name']}")
        
        # Speichere alle Änderungen
        try:
            db.session.commit()
            print(f"\n✅ {created_count} Akquisekanäle erfolgreich erstellt!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Fehler beim Speichern: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("=== Initialisierung der Akquisekanäle ===")
    init_acquisition_channels()
