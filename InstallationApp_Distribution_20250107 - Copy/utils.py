"""
Utility-Funktionen für die InstallationApp
"""
import os
import csv
from datetime import date
from models import db, PositionTemplate, Supplier, CompanySettings, Quote

def get_default_hourly_rate():
    """Lädt den aktuellen Standard-Stundensatz"""
    return CompanySettings.get_setting('default_hourly_rate', 95.0)

def generate_quote_number():
    """Generiert eine neue Angebotsnummer"""
    quote_count = Quote.query.count() + 1
    return f"ANG-{date.today().strftime('%Y')}-{quote_count:03d}"

def load_position_templates():
    """Lädt Positionsvorlagen aus CSV"""
    try:
        templates_path = os.path.join(os.path.dirname(__file__), 'templates_excel', 'positionen_template.csv')
        
        if not os.path.exists(templates_path):
            print(f"CSV-Datei nicht gefunden: {templates_path}")
            return False
        
        # Lösche vorhandene Templates
        PositionTemplate.query.delete()
        
        with open(templates_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                template = PositionTemplate(
                    position=int(row['Position']),
                    sub_position=row['Subposition'],
                    description=row['Beschreibung'],
                    category=row['Kategorie'],
                    requires_order=row['Bestellung_notwendig'].lower() == 'ja',
                    standard_supplier=row['Standard_Lieferant']
                )
                db.session.add(template)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Fehler beim Laden der Positionsvorlagen: {e}")
        db.session.rollback()
        return False

def load_suppliers():
    """Lädt Lieferanten aus CSV"""
    try:
        suppliers_path = os.path.join(os.path.dirname(__file__), 'templates_excel', 'lieferanten_template.csv')
        
        if not os.path.exists(suppliers_path):
            print(f"CSV-Datei nicht gefunden: {suppliers_path}")
            return False
        
        # Lösche vorhandene Lieferanten
        Supplier.query.delete()
        
        with open(suppliers_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                supplier = Supplier(
                    name=row['Lieferant_Name'],
                    category=row['Kategorie'],
                    contact_person=row['Kontakt_Person'],
                    phone=row['Telefon'],
                    email=row['Email'],
                    address=row['Adresse'],
                    notes=row['Bemerkung']
                )
                db.session.add(supplier)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Fehler beim Laden der Lieferanten: {e}")
        db.session.rollback()
        return False

def update_quote_total(quote_id):
    """Aktualisiert die Gesamtsumme eines Angebots"""
    quote = Quote.query.get(quote_id)
    if quote:
        quote.update_total()

def safe_float_conversion(value, default=0.0):
    """Sichere Konvertierung zu Float mit Fallback"""
    if not value:
        return default
    try:
        # Ersetze Komma durch Punkt für deutsche Zahlenformate
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value)
    except (ValueError, TypeError):
        return default

def parse_quantity_from_text(quantity_text):
    """Extrahiert numerischen Wert aus Text (z.B. "2.5m²" -> 2.5)"""
    if not quantity_text:
        return 0.0
    
    # Versuche direkte Konvertierung
    try:
        return float(quantity_text.replace(',', '.'))
    except ValueError:
        pass
    
    # Extrahiere Zahlen am Anfang des Textes
    import re
    match = re.match(r'^([\d,\.]+)', quantity_text.strip())
    if match:
        try:
            return float(match.group(1).replace(',', '.'))
        except ValueError:
            pass
    
    return 0.0

def generate_supplier_order_email(quote, supplier_name, order_items, order_number=None):
    """Generiert E-Mail-Template für Lieferantenbestellung"""
    
    # E-Mail Betreff
    subject = f"{quote.quote_number} - {quote.project_description[:50]}..."
    if order_number:
        subject = f"{order_number} / {subject}"
    
    # Plain Text E-Mail Body für mailto-Link
    plain_body = f"""Sehr geehrte Damen und Herren,

hiermit bestellen wir folgende Positionen für das Projekt:

Angebot: {quote.quote_number}"""
    
    if order_number:
        plain_body += f"""
Auftrag: {order_number}"""
    
    plain_body += f"""
Projekt: {quote.project_description}
Kunde: {quote.customer.full_name}

Bestellpositionen:
"""
    
    # Plain Text Tabelle - optimiert für E-Mail-Clients mit Tabs
    plain_body += "\n"
    plain_body += "Unterposition\t\tBeschreibung\t\t\t\t\tTeilenummer\t\t\tAnzahl\n"
    plain_body += "-" * 80 + "\n"
    
    for item in order_items:
        # Formatierung mit Tabs für bessere Ausrichtung
        sub_number = item['sub_number'][:12]
        description = item['description'][:35]
        part_number = item['part_number'][:15] if item['part_number'] else ''
        quantity = str(item['quantity'])
        
        # Tabs basierend auf Länge anpassen
        sub_tabs = "\t\t" if len(sub_number) < 8 else "\t"
        desc_tabs = "\t\t\t" if len(description) < 20 else ("\t\t" if len(description) < 30 else "\t")
        part_tabs = "\t\t" if len(part_number) < 8 else "\t"
        
        plain_body += f"{sub_number}{sub_tabs}{description}{desc_tabs}{part_number}{part_tabs}{quantity}\n"
    
    plain_body += "-" * 80
    
    plain_body += f"""

Bitte bestätigen Sie den Erhalt dieser Bestellung und teilen Sie uns die Lieferzeit mit.

Mit freundlichen Grüßen
Ing. Michael Holasek
InnSan"""

    # HTML E-Mail Body für Anzeige
    html_body = f"""
Sehr geehrte Damen und Herren,

hiermit bestellen wir folgende Positionen für das Projekt:

Angebot: {quote.quote_number}"""
    
    if order_number:
        html_body += f"""
Auftrag: {order_number}"""
    
    html_body += f"""
Projekt: {quote.project_description}
Kunde: {quote.customer.full_name}

Bestellpositionen:

<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="text-align: left; padding: 10px;">Unterposition</th>
            <th style="text-align: left; padding: 10px;">Beschreibung</th>
            <th style="text-align: left; padding: 10px;">Teilenummer</th>
            <th style="text-align: center; padding: 10px;">Anzahl</th>
        </tr>
    </thead>
    <tbody>
"""
    
    for item in order_items:
        html_body += f"""        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{item['sub_number']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{item['description']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{item['part_number']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
        </tr>
"""
    
    html_body += """    </tbody>
</table>

"""
    
    html_body += f"""
Bitte bestätigen Sie den Erhalt dieser Bestellung und teilen Sie uns die Lieferzeit mit.

Mit freundlichen Grüßen
Ing. Michael Holasek
InnSan"""
    
    return subject, html_body, plain_body

def collect_supplier_orders(quote):
    """Sammelt alle Bestellteile pro Lieferant für ein Angebot"""
    supplier_orders = {}
    
    for quote_item in quote.quote_items:
        for sub_item in quote_item.sub_items:
            if (sub_item.item_type == 'bestellteil' and 
                sub_item.requires_order and 
                sub_item.supplier):
                
                supplier = sub_item.supplier
                if supplier not in supplier_orders:
                    supplier_orders[supplier] = []
                
                supplier_orders[supplier].append({
                    'sub_number': sub_item.sub_number,
                    'description': sub_item.description,
                    'part_number': sub_item.part_number or '',
                    'quantity': sub_item.part_quantity or '1',
                    'quote_sub_item_id': sub_item.id  # Für Referenz
                })
    
    return supplier_orders

def get_supplier_email(supplier_name):
    """Holt die E-Mail-Adresse eines Lieferanten"""
    from models import Supplier
    supplier = Supplier.query.filter_by(name=supplier_name).first()
    if supplier and supplier.email:
        return supplier.email
    return None

def generate_order_number():
    """Generiert eine eindeutige Auftragsnummer"""
    from models import Order
    from datetime import datetime
    
    # Format: AUF-2025-001
    year = datetime.now().year
    prefix = f"AUF-{year}-"
    
    # Finde die höchste Nummer für das aktuelle Jahr
    latest_order = Order.query.filter(
        Order.order_number.like(f"{prefix}%")
    ).order_by(Order.order_number.desc()).first()
    
    if latest_order:
        try:
            # Extrahiere die letzten 3 Ziffern
            last_number = int(latest_order.order_number.split('-')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}{new_number:03d}"
