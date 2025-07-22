#!/usr/bin/env python3
"""
Skript zum Aktualisieren der Kategorien für bestehende Positionsvorlagen
Lädt alle Vorlagen und weist ihnen basierend auf dem Namen passende Kategorien zu
"""
from app import app, db
from models import PositionTemplate

# Mapping von Schlüsselwörtern zu Kategorien
CATEGORY_MAPPING = {
    'UmbauWanneZurDusche': [
        'wanne', 'dusche', 'umbau', 'duschtasse', 'wannen', 'barrierefrei', 'badumbau'
    ],
    'Wandflaeche': [
        'wand', 'fliesen', 'verfliesungen', 'wandfläche', 'wandbelag', 'rückwand'
    ],
    'Boden': [
        'boden', 'bodenbelag', 'fußboden', 'estrich', 'bodenverlegung', 'fußbodenheizung'
    ],
    'Sanitaerprodukte': [
        'armaturen', 'brause', 'wasserhahn', 'duschkopf', 'sanitär', 'waschtisch', 
        'waschbecken', 'haltegriff', 'klappsitz'
    ],
    'Badmoebel': [
        'möbel', 'schrank', 'unterschrank', 'spiegelschrank', 'badmöbel', 'waschtischunterschrank'
    ],
    'WC': [
        'wc', 'toilette', 'spülkasten', 'bidet', 'urinal'
    ],
    'Heizung': [
        'heizung', 'heizkörper', 'fußbodenheizung', 'handtuchheizung', 'handtuchwärmer'
    ],
    'Elektroarbeiten': [
        'elektro', 'beleuchtung', 'steckdose', 'schalter', 'led', 'licht', 'verkabelung'
    ],
    'Decke': [
        'decke', 'deckenbekleidung', 'deckenverkleidung', 'abgehängte', 'spanndecke'
    ],
    'Sonderleistungen': [
        'entsorgung', 'abbruch', 'demontage', 'sonderleistung', 'zusatz', 'montage'
    ]
}

def categorize_template(template_name):
    """
    Bestimmt die passende Kategorie basierend auf dem Template-Namen
    """
    name_lower = template_name.lower()
    
    # Gehe durch alle Kategorien und prüfe Schlüsselwörter
    for category, keywords in CATEGORY_MAPPING.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category
    
    # Standard-Kategorie falls keine Zuordnung gefunden wird
    return 'sonstiges'

def update_template_categories():
    """
    Aktualisiert alle bestehenden Vorlagen mit passenden Kategorien
    """
    with app.app_context():
        try:
            # Alle Vorlagen ohne Kategorie laden
            templates = PositionTemplate.query.filter(
                (PositionTemplate.category.is_(None)) | 
                (PositionTemplate.category == '') |
                (PositionTemplate.category == 'Allgemein')
            ).all()
            
            print(f"Gefunden: {len(templates)} Vorlagen ohne Kategorie")
            
            updated_count = 0
            
            for template in templates:
                old_category = template.category or 'Keine'
                new_category = categorize_template(template.name)
                
                template.category = new_category
                print(f"Vorlage '{template.name}': {old_category} -> {new_category}")
                updated_count += 1
            
            # Änderungen speichern
            db.session.commit()
            print(f"\nErfolgreich {updated_count} Vorlagen aktualisiert!")
            
            # Übersicht der aktualisierten Kategorien
            print("\nÜbersicht aller Vorlagen nach Kategorien:")
            all_templates = PositionTemplate.query.all()
            category_count = {}
            
            for template in all_templates:
                cat = template.category or 'Keine Kategorie'
                if cat not in category_count:
                    category_count[cat] = 0
                category_count[cat] += 1
            
            for category, count in sorted(category_count.items()):
                print(f"  {category}: {count} Vorlage(n)")
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Kategorien: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    update_template_categories()
