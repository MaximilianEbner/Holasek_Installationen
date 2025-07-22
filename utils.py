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
    """Lädt Positionsvorlagen aus CSV - DEAKTIVIERT da neues Template-System verwendet wird"""
    try:
        print("CSV-Import von Positionsvorlagen wurde deaktiviert - verwende neues Template-System")
        return True
    except Exception as e:
        print(f"Fehler beim Laden der Positionsvorlagen: {e}")
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
    # E-Mail Betreff: BVH: <Projekt> & <Nachname des Kunden>
    subject = f"Bestellung für {supplier_name} - BVH: {quote.customer.last_name}"

    # Lieferort und Liefertermin berechnen
    lieferort = "Lager"
    angestrebter_liefertermin = ""
    # Versuche das zugehörige Order-Objekt zu finden
    order_obj = getattr(quote, 'order', None)
    if not order_obj and order_number:
        # Suche das Order-Objekt über die order_number
        from models import Order
        order_obj = Order.query.filter_by(order_number=order_number).first()
    start_date = getattr(order_obj, 'start_date', None) if order_obj else None
    if start_date:
        from datetime import timedelta
        zieltermin = start_date - timedelta(weeks=2)
        cw = zieltermin.isocalendar()[1]
        angestrebter_liefertermin = f"KW {cw}"

    # Plain Text E-Mail Body für mailto-Link
    plain_body = f"""Sehr geehrte Damen und Herren,

hiermit bestellen wir folgende Positionen für das Projekt:
"""
    if order_number:
        plain_body += f"\nAuftrag: {order_number}"
    plain_body += f"""
BVH: {quote.customer.last_name}
Lieferort: {lieferort}
Angestrebter Liefertermin: {angestrebter_liefertermin}

Bestellpositionen:
"""

    # Neue Formatierung: Jeder Artikel als ' <Stückzahl> x <Teilenummer> <Teilebeschreibung>'
    plain_body += "\n"
    for item in order_items:
        quantity = str(item['quantity'])
        part_number = item['part_number'] if item['part_number'] else ''
        description = item['description']
        plain_body += f"{quantity}x {part_number}: {description}\n"
    plain_body += f"""

Bitte bestätigen Sie den Erhalt dieser Bestellung und teilen Sie uns die Lieferzeit mit.

Mit freundlichen Grüßen
Ing. Michael Holasek
InnSan"""

    # HTML E-Mail Body für Anzeige
    html_body = f"""
Sehr geehrte Damen und Herren,

hiermit bestellen wir folgende Positionen für das Projekt:
"""
    if order_number:
        html_body += f"<br>Auftrag: {order_number}"
    html_body += f"""

<br>BVH: {quote.customer.last_name}
<br>Lieferort: {lieferort}
<br>Angestrebter Liefertermin: {angestrebter_liefertermin}
<br><br>Bestellpositionen:

<table border=\"1\" cellpadding=\"8\" cellspacing=\"0\" style=\"border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;\">
    <thead>
        <tr style=\"background-color: #f8f9fa;\">
            <th style=\"text-align: left; padding: 10px;\">Unterposition</th>
            <th style=\"text-align: left; padding: 10px;\">Beschreibung</th>
            <th style=\"text-align: left; padding: 10px;\">Teilenummer</th>
            <th style=\"text-align: center; padding: 10px;\">Anzahl</th>
        </tr>
    </thead>
    <tbody>
"""
    for item in order_items:
        html_body += f"        <tr>\n            <td style=\"padding: 8px; border: 1px solid #ddd;\">{item['sub_number']}</td>\n            <td style=\"padding: 8px; border: 1px solid #ddd;\">{item['description']}</td>\n            <td style=\"padding: 8px; border: 1px solid #ddd;\">{item['part_number']}</td>\n            <td style=\"padding: 8px; border: 1px solid #ddd; text-align: center;\">{item['quantity']}</td>\n        </tr>\n"
    html_body += "    </tbody>\n</table>\n\n"
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
