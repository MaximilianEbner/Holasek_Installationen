# Arbeitsschritte-Konfiguration für Angebotserstellung
# Diese Datei definiert alle verfügbaren Arbeitsschritte mit Standardzeiten

WORK_STEPS = {
    "Abbruch": [
        {"name": "Wanne raus", "default_hours": 4},
        {"name": "Dusche raus", "default_hours": 4},
        {"name": "WC abbauen", "default_hours": 1},
        {"name": "WT abbauen je Teil", "default_hours": 1},
        {"name": "Duschglas abbauen", "default_hours": 1},
        {"name": "Sockel / Vorwand abbauen", "default_hours": 1},
        {"name": "Heizkörper", "default_hours": 2},
        {"name": "Bodenfliesen raus", "default_hours": 4},
        {"name": "Wandfliesen raus", "default_hours": 8},
        {"name": "Therme demonieren", "default_hours": 2},
        {"name": "Zwischenwand entfernen", "default_hours": 2},
        {"name": "Decke abbauen", "default_hours": 3},
    ],
    "Duschtasse": [
        {"name": "Abfluss stemmen Versetzen", "default_hours": 2},
        {"name": "Abfluss stemmen Bodengleich", "default_hours": 4},
        {"name": "Tasse setzen", "default_hours": 4},
        {"name": "Tasse zuscheiden", "default_hours": 2},
        {"name": "Duschkabine schwer", "default_hours": 6},
        {"name": "Duschkabine leicht", "default_hours": 2},
        {"name": "Armatur montieren", "default_hours": 2},
        {"name": "Klappsitz", "default_hours": 1},
        {"name": "Haltegriff montieren", "default_hours": 1},
        {"name": "Duschnische einbauen", "default_hours": 2},
        {"name": "Duschrinne installieren", "default_hours": 4},
        {"name": "geflieste Rinne setzen", "default_hours": 4},
    ],
    "Badewanne": [
        {"name": "setzen", "default_hours": 4},
        {"name": "verkleiden", "default_hours": 4},
        {"name": "Armatur", "default_hours": 2},
        {"name": "Glasaufsatz", "default_hours": 2},
    ],
    "WC": [
        {"name": "UP-Gestell", "default_hours": 6},
        {"name": "WC installieren", "default_hours": 2},
        {"name": "Dusch WC installieren", "default_hours": 4},
        {"name": "Haltegriff montieren", "default_hours": 1},
    ],
    "Waschtisch/Möbel": [
        {"name": "Waschtisch", "default_hours": 2},
        {"name": "Möbel je Teil", "default_hours": 2},
    ],
    "Heizkörper": [
        {"name": "Heizkörper installieren", "default_hours": 6},
        {"name": "Heizkörper montieren", "default_hours": 2},
        {"name": "Therme montieren", "default_hours": 4},
    ],
    "Weg & Entsorgung": [
        {"name": "Weg", "default_hours": 1},
        {"name": "Entsorgung in €", "default_hours": 0},  # Wird als Pauschale behandelt
    ],
}

def get_work_steps():
    """Gibt alle verfügbaren Arbeitsschritte zurück"""
    return WORK_STEPS

def get_work_step_by_category_and_name(category, name):
    """Gibt einen spezifischen Arbeitsschritt zurück"""
    if category in WORK_STEPS:
        for step in WORK_STEPS[category]:
            if step["name"] == name:
                return step
    return None
