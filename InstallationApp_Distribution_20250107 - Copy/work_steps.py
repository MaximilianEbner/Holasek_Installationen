# Arbeitsschritte-Konfiguration für Angebotserstellung
# Diese Datei definiert alle verfügbaren Arbeitsschritte mit Standardzeiten

WORK_STEPS = {'Abbruch': [{'name': 'Wanne raus', 'default_hours': 4.0}, {'name': 'Dusche raus', 'default_hours': 4.0}, {'name': 'WC abbauen', 'default_hours': 1.0}, {'name': 'WT abbauen je Teil', 'default_hours': 1.0}, {'name': 'Duschglas abbauen', 'default_hours': 1.0}, {'name': 'Sockel / Vorwand abbauen', 'default_hours': 1.0}, {'name': 'Heizkörper', 'default_hours': 2.0}, {'name': 'Bodenfliesen raus', 'default_hours': 4.0}, {'name': 'Wandfliesen raus', 'default_hours': 8.0}, {'name': 'Therme demonieren', 'default_hours': 2.0}, {'name': 'Zwischenwand entfernen', 'default_hours': 2.0}, {'name': 'Decke abbauen', 'default_hours': 3.0}], 'Duschtasse': [{'name': 'Abfluss stemmen Versetzen', 'default_hours': 2.0}, {'name': 'Abfluss stemmen Bodengleich', 'default_hours': 4.0}, {'name': 'Tasse setzen', 'default_hours': 4.0}, {'name': 'Tasse zuscheiden', 'default_hours': 2.0}, {'name': 'Duschkabine schwer', 'default_hours': 6.0}, {'name': 'Duschkabine leicht', 'default_hours': 2.0}, {'name': 'Armatur montieren', 'default_hours': 2.0}, {'name': 'Klappsitz', 'default_hours': 1.0}, {'name': 'Haltegriff montieren', 'default_hours': 1.0}, {'name': 'Duschnische einbauen', 'default_hours': 2.0}, {'name': 'Duschrinne installieren', 'default_hours': 4.0}, {'name': 'geflieste Rinne setzen', 'default_hours': 4.0}], 'Badewanne': [{'name': 'setzen', 'default_hours': 4.0}, {'name': 'verkleiden', 'default_hours': 4.0}, {'name': 'Armatur', 'default_hours': 2.0}, {'name': 'Glasaufsatz', 'default_hours': 2.0}], 'WC': [{'name': 'UP-Gestell', 'default_hours': 6.0}, {'name': 'WC installieren', 'default_hours': 2.0}, {'name': 'Dusch WC installieren', 'default_hours': 4.0}, {'name': 'Haltegriff montieren', 'default_hours': 1.0}], 'Waschtisch/Möbel': [{'name': 'Waschtisch', 'default_hours': 2.0}, {'name': 'Möbel je Teil', 'default_hours': 2.0}], 'Heizkörper': [{'name': 'Heizkörper installieren', 'default_hours': 6.0}, {'name': 'Heizkörper montieren', 'default_hours': 2.0}, {'name': 'Therme montieren', 'default_hours': 4.0}], 'Entsorgung': [{'name': 'Pauschale klein', 'default_hours': 1.1}, {'name': 'Pauschale normal', 'default_hours': 5.1}]}

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
