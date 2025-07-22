#!/usr/bin/env python3
"""
Skript zum Laden von Standard-Positionsvorlagen mit Kategorien
Erstellt Beispielvorlagen für alle definierten Kategorien
"""
import os
import sys

# Flask App-Kontext importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, PositionTemplate, PositionTemplateSubItem
from datetime import datetime

def create_default_templates():
    """
    Erstellt Standard-Vorlagen für alle Kategorien
    """
    with app.app_context():
        try:
            # Standard-Vorlagen definieren
            default_templates = [
                {
                    'name': 'Standard Wannenumbau zur Dusche',
                    'category': 'UmbauWanneZurDusche',
                    'description': 'Kompletter Umbau einer Badewanne zu einer barrierefreien Dusche mit Standardausstattung',
                    'subitems': [
                        {'description': 'Duschtasse Mineralwerkstoff 90x90', 'type': 'bestellteil', 'unit': 'Stück', 'price': 450.00, 'formula': ''},
                        {'description': 'Rückwand-Montage', 'type': 'arbeitsvorgang', 'unit': 'm²', 'price': 65.00, 'formula': 'hoehe*breite'},
                        {'description': 'Duscharmatur Standardausführung', 'type': 'bestellteil', 'unit': 'Stück', 'price': 180.00, 'formula': ''},
                        {'description': 'Entsorgung alte Wanne', 'type': 'sonstiges', 'unit': 'Pauschal', 'price': 150.00, 'formula': ''}
                    ]
                },
                {
                    'name': 'Wandverfliesungen Standard',
                    'category': 'Wandflaeche',
                    'description': 'Standard-Wandverfliesung für Badezimmer mit Grundausstattung',
                    'subitems': [
                        {'description': 'Grundierung/Haftgrund', 'type': 'bestellteil', 'unit': 'm²', 'price': 8.50, 'formula': 'breite*hoehe'},
                        {'description': 'Fliesenverlegung', 'type': 'arbeitsvorgang', 'unit': 'm²', 'price': 35.00, 'formula': 'breite*hoehe'},
                        {'description': 'Fugenmaterial', 'type': 'bestellteil', 'unit': 'm²', 'price': 3.20, 'formula': 'breite*hoehe'},
                        {'description': 'Silikonfugen', 'type': 'arbeitsvorgang', 'unit': 'm', 'price': 8.00, 'formula': 'umfang'}
                    ]
                },
                {
                    'name': 'Bodenverlegung Vinyl',
                    'category': 'Boden',
                    'description': 'Vinylboden-Verlegung mit Vorbereitung und Fußleisten',
                    'subitems': [
                        {'description': 'Vinyl-Planken Premium', 'type': 'bestellteil', 'unit': 'm²', 'price': 25.00, 'formula': 'laenge*breite'},
                        {'description': 'Unterlagsmatte', 'type': 'bestellteil', 'unit': 'm²', 'price': 4.50, 'formula': 'laenge*breite'},
                        {'description': 'Verlegung Vinylboden', 'type': 'arbeitsvorgang', 'unit': 'm²', 'price': 18.00, 'formula': 'laenge*breite'},
                        {'description': 'Fußleisten setzen', 'type': 'arbeitsvorgang', 'unit': 'm', 'price': 12.00, 'formula': 'umfang'}
                    ]
                },
                {
                    'name': 'Sanitärausstattung Komplett',
                    'category': 'Sanitaerprodukte',
                    'description': 'Komplette Sanitärausstattung für ein Standardbad',
                    'subitems': [
                        {'description': 'Waschtisch mit Unterschrank', 'type': 'bestellteil', 'unit': 'Stück', 'price': 280.00, 'formula': ''},
                        {'description': 'Waschtischarmatur', 'type': 'bestellteil', 'unit': 'Stück', 'price': 120.00, 'formula': ''},
                        {'description': 'Brausegarnitur komplett', 'type': 'bestellteil', 'unit': 'Stück', 'price': 95.00, 'formula': ''},
                        {'description': 'Montage Sanitärobjekte', 'type': 'arbeitsvorgang', 'unit': 'h', 'price': 65.00, 'formula': 'stunden'}
                    ]
                },
                {
                    'name': 'WC-Komplettset Standard',
                    'category': 'WC',
                    'description': 'Standard WC-Set mit Montage und Anschluss',
                    'subitems': [
                        {'description': 'WC-Keramik Komplett-Set', 'type': 'bestellteil', 'unit': 'Stück', 'price': 180.00, 'formula': ''},
                        {'description': 'WC-Sitz', 'type': 'bestellteil', 'unit': 'Stück', 'price': 45.00, 'formula': ''},
                        {'description': 'WC-Montage und Anschluss', 'type': 'arbeitsvorgang', 'unit': 'h', 'price': 65.00, 'formula': 'stunden'},
                        {'description': 'Spülkasten-Installation', 'type': 'arbeitsvorgang', 'unit': 'Stück', 'price': 85.00, 'formula': ''}
                    ]
                },
                {
                    'name': 'Heizkörper Standard',
                    'category': 'Heizung',
                    'description': 'Standard-Heizkörper für Badezimmer mit Anschluss',
                    'subitems': [
                        {'description': 'Handtuchheizkörper', 'type': 'bestellteil', 'unit': 'Stück', 'price': 180.00, 'formula': ''},
                        {'description': 'Heizungsanschluss', 'type': 'arbeitsvorgang', 'unit': 'Stück', 'price': 120.00, 'formula': ''},
                        {'description': 'Thermostatventil', 'type': 'bestellteil', 'unit': 'Stück', 'price': 45.00, 'formula': ''}
                    ]
                },
                {
                    'name': 'Elektroinstallation Bad',
                    'category': 'Elektroarbeiten',
                    'description': 'Standard-Elektroinstallation für Badezimmer',
                    'subitems': [
                        {'description': 'LED-Beleuchtung IP44', 'type': 'bestellteil', 'unit': 'Stück', 'price': 65.00, 'formula': ''},
                        {'description': 'Feuchtraum-Steckdose', 'type': 'bestellteil', 'unit': 'Stück', 'price': 25.00, 'formula': ''},
                        {'description': 'Elektroinstallation', 'type': 'arbeitsvorgang', 'unit': 'h', 'price': 55.00, 'formula': 'stunden'},
                        {'description': 'Lichtschalter wasserdicht', 'type': 'bestellteil', 'unit': 'Stück', 'price': 18.00, 'formula': ''}
                    ]
                }
            ]
            
            created_count = 0
            for template_data in default_templates:
                # Prüfen ob Vorlage bereits existiert
                existing = PositionTemplate.query.filter_by(name=template_data['name']).first()
                if existing:
                    print(f"Vorlage '{template_data['name']}' existiert bereits - überspringe")
                    continue
                
                # Neue Vorlage erstellen
                template = PositionTemplate(
                    name=template_data['name'],
                    category=template_data['category'],
                    description=template_data['description'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.session.add(template)
                db.session.flush()  # Um ID zu bekommen
                
                # Unterpositionen erstellen
                for subitem_data in template_data['subitems']:
                    subitem = PositionTemplateSubItem(
                        template_id=template.id,
                        description=subitem_data['description'],
                        item_type=subitem_data['type'],
                        unit=subitem_data['unit'],
                        price_per_unit=subitem_data['price'],
                        formula=subitem_data['formula']
                    )
                    db.session.add(subitem)
                
                created_count += 1
                print(f"Vorlage '{template_data['name']}' erstellt ({template_data['category']})")
            
            # Änderungen speichern
            db.session.commit()
            print(f"\nErfolgreich {created_count} neue Vorlagen erstellt!")
            
            # Übersicht aller Vorlagen
            print("\nÜbersicht aller Vorlagen nach Kategorien:")
            all_templates = PositionTemplate.query.all()
            category_count = {}
            
            for template in all_templates:
                cat = template.category or 'Keine Kategorie'
                if cat not in category_count:
                    category_count[cat] = []
                category_count[cat].append(template.name)
            
            for category, templates in sorted(category_count.items()):
                print(f"  {category}: {len(templates)} Vorlage(n)")
                for template_name in templates:
                    print(f"    - {template_name}")
            
        except Exception as e:
            print(f"Fehler beim Erstellen der Standard-Vorlagen: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_default_templates()
