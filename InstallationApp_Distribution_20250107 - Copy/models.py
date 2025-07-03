"""
Datenbankmodelle für die InstallationApp
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehungen
    quotes = db.relationship('Quote', backref='customer', lazy=True)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    project_description = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Entwurf')  # Entwurf, Gesendet, Angenommen, Abgelehnt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.Date)
    include_additional_info = db.Column(db.Boolean, default=True)
    show_subitem_prices = db.Column(db.Boolean, default=False)  # Preistransparenz Unterpositionen
    markup_percentage = db.Column(db.Float, default=15.0)  # Aufschlag in Prozent (Standard: 15%)
    
    # Beziehungen
    quote_items = db.relationship('QuoteItem', backref='quote', lazy=True, cascade='all, delete-orphan')
    
    def calculate_base_total(self):
        """Berechnet die Gesamtsumme ohne Aufschlag - einfach die Summe aller Gesamtpreise der Hauptpositionen"""
        return sum(item.total_price for item in self.quote_items)
    
    def calculate_net_total(self):
        """Berechnet die echte Nettosumme (Basis ohne Aufschlag) - für die Anzeige als 'Nettosumme'"""
        # Berechne die Basis ohne Aufschlag: Summe der Sub-Item Preise bzw. Menge × Einzelpreis
        base_total = 0.0
        for item in self.quote_items:
            if item.sub_items:
                # Für Items mit Unterpositionen: Summe der Sub-Item Preise (ohne Aufschlag)
                base_total += sum(sub_item.price for sub_item in item.sub_items)
            else:
                # Für normale Items: quantity × unit_price (ohne Aufschlag)
                base_total += item.quantity * item.unit_price
        return base_total
    
    def calculate_total(self):
        """Berechnet die Gesamtsumme aller Positionen mit Aufschlag"""
        net_total = self.calculate_net_total()
        markup_amount = self.calculate_markup_amount()
        return net_total + markup_amount
    
    def calculate_markup_amount(self):
        """Berechnet den Aufschlagsbetrag basierend auf der echten Nettosumme"""
        net_total = self.calculate_net_total()
        if self.markup_percentage and self.markup_percentage > 0:
            return net_total * (self.markup_percentage / 100)
        return 0.0
    
    def update_total(self):
        """Aktualisiert die Gesamtsumme und speichert sie"""
        self.total_amount = self.calculate_total()
        db.session.commit()

class QuoteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text, nullable=False)
    position_number = db.Column(db.Integer, nullable=False, default=1)
    requires_order = db.Column(db.Boolean, default=False)
    supplier = db.Column(db.String(200))
    item_type = db.Column(db.String(20), default='standard')  # standard, arbeitsposition, etc.
    
    # Beziehung
    sub_items = db.relationship('QuoteSubItem', backref='quote_item', lazy=True, cascade='all, delete-orphan')
    
    def calculate_price(self):
        """Berechnet den Preis basierend auf Menge und Einzelpreis"""
        if self.sub_items:
            # Wenn Unterpositionen vorhanden sind, summiere diese
            return sum(sub_item.price for sub_item in self.sub_items)
        else:
            # Normale Berechnung: Menge × Einzelpreis
            return self.quantity * self.unit_price
    
    def update_price(self):
        """Aktualisiert den Gesamtpreis"""
        self.total_price = self.calculate_price()
    
    def calculate_price_with_markup(self):
        """Berechnet den Preis der Position inklusive Aufschlag - für PDF-Export"""
        base_price = self.calculate_price()
        if self.quote and self.quote.markup_percentage and self.quote.markup_percentage > 0:
            markup_factor = 1 + (self.quote.markup_percentage / 100)
            return base_price * markup_factor
        return base_price

class QuoteSubItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_item_id = db.Column(db.Integer, db.ForeignKey('quote_item.id'), nullable=False)
    sub_number = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    item_type = db.Column(db.String(20), nullable=False, default='bestellteil')
    
    # Felder für Bestellteil
    requires_order = db.Column(db.Boolean, default=False)
    supplier = db.Column(db.String(200))
    part_number = db.Column(db.String(100))
    part_quantity = db.Column(db.String(50), default='1')
    part_price = db.Column(db.Float, default=0.0)
    
    # Felder für Arbeitsvorgang
    hours = db.Column(db.Float, default=0.0)
    hourly_rate = db.Column(db.Float, default=95.0)
    
    # Felder für Sonstiges
    quantity = db.Column(db.String(50), default='')
    unit_price = db.Column(db.Float, default=0.0)
    
    # Berechneter Preis
    price = db.Column(db.Float, default=0.0)
    
    def calculate_price(self):
        """Berechnet den Preis basierend auf dem Typ der Unterposition"""
        if self.item_type == 'arbeitsvorgang':
            return self.hours * self.hourly_rate
        elif self.item_type == 'sonstiges':
            try:
                quantity_num = float(self.quantity.replace(',', '.')) if self.quantity else 0.0
                return quantity_num * self.unit_price
            except (ValueError, AttributeError):
                return self.unit_price
        else:  # bestellteil
            return self.part_price
    
    def update_price(self):
        """Aktualisiert den berechneten Preis"""
        self.price = self.calculate_price()

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class PositionTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)
    sub_position = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    requires_order = db.Column(db.Boolean, default=False)
    standard_supplier = db.Column(db.String(200))

class CompanySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(name, default_value=None):
        """Hilfsfunktion zum Laden einer Einstellung"""
        setting = CompanySettings.query.filter_by(setting_name=name).first()
        if setting:
            try:
                # Versuche numerische Werte zu konvertieren
                if default_value is not None and isinstance(default_value, (int, float)):
                    return type(default_value)(setting.setting_value)
                return setting.setting_value
            except (ValueError, TypeError):
                return default_value
        return default_value
    
    @staticmethod
    def set_setting(name, value, description=None):
        """Hilfsfunktion zum Setzen einer Einstellung"""
        setting = CompanySettings.query.filter_by(setting_name=name).first()
        if setting:
            setting.setting_value = str(value)
            setting.updated_at = datetime.utcnow()
        else:
            setting = CompanySettings(
                setting_name=name,
                setting_value=str(value),
                description=description
            )
            db.session.add(setting)
        db.session.commit()
        return setting

class QuoteRejection(db.Model):
    """Model für Angebots-Ablehnungen mit Grund"""
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    rejection_reason = db.Column(db.Text, nullable=False)
    rejected_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung
    quote = db.relationship('Quote', backref=db.backref('rejection', uselist=False))

class Order(db.Model):
    """Model für Aufträge - Realisierung von Angeboten"""
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Geplant')  # Geplant, In Arbeit, Abgeschlossen
    
    # Realisierungszeitraum
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Zusätzliche Felder
    notes = db.Column(db.Text)
    project_manager = db.Column(db.String(100))
    
    # Beziehung
    quote = db.relationship('Quote', backref=db.backref('order', uselist=False))
    
    @property
    def customer(self):
        """Direkter Zugriff auf den Kunden über das verknüpfte Angebot"""
        return self.quote.customer if self.quote else None
    
    @property
    def total_amount(self):
        """Gesamtsumme des Auftrags (aus dem Angebot)"""
        return self.quote.total_amount if self.quote else 0.0

class SupplierOrder(db.Model):
    """Model für Lieferantenbestellungen"""
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # Verknüpfung zum Auftrag
    supplier_name = db.Column(db.String(200), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Bestellt')  # Bestellt, Bestätigt, Geliefert
    confirmation_date = db.Column(db.DateTime)
    delivery_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    
    # Beziehungen
    quote = db.relationship('Quote', backref='supplier_orders')
    order = db.relationship('Order', backref='supplier_orders')
    items = db.relationship('SupplierOrderItem', backref='supplier_order', lazy=True, cascade='all, delete-orphan')

class SupplierOrderItem(db.Model):
    """Model für einzelne Positionen einer Lieferantenbestellung"""
    id = db.Column(db.Integer, primary_key=True)
    supplier_order_id = db.Column(db.Integer, db.ForeignKey('supplier_order.id'), nullable=False)
    sub_number = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    part_number = db.Column(db.String(100))
    quantity = db.Column(db.String(50), default='1')
    quote_sub_item_id = db.Column(db.Integer, db.ForeignKey('quote_sub_item.id'))
    
    # Beziehung zu ursprünglicher Unterposition
    quote_sub_item = db.relationship('QuoteSubItem', backref='supplier_order_items')

class WorkInstruction(db.Model):
    """Model für Arbeitsanweisungen"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    instruction_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))  # Wer hat die Anweisung erstellt
    status = db.Column(db.String(20), default='Erstellt')  # Erstellt, In Bearbeitung, Abgeschlossen
    
    # Arbeitsinhalt
    work_description = db.Column(db.Text)  # Detaillierte Arbeitsbeschreibung
    special_instructions = db.Column(db.Text)  # Besondere Hinweise/Anweisungen
    safety_notes = db.Column(db.Text)  # Sicherheitshinweise
    tools_required = db.Column(db.Text)  # Benötigte Werkzeuge
    estimated_duration = db.Column(db.Integer)  # Geschätzte Dauer in Stunden
    priority = db.Column(db.String(20), default='Normal')  # Niedrig, Normal, Hoch, Dringend
    
    # Montage-spezifisch
    installation_location = db.Column(db.String(255))  # Montageort (z.B. Raum)
    access_requirements = db.Column(db.Text)  # Zugangserfordernisse
    preparation_work = db.Column(db.Text)  # Vorarbeiten
    
    # PDF und Medien
    pdf_path = db.Column(db.String(255))  # Pfad zur gespeicherten PDF-Datei
    has_photos = db.Column(db.Boolean, default=False)  # Wurden Fotos eingefügt
    has_3d_plan = db.Column(db.Boolean, default=False)  # Wurde 3D-Plan eingefügt
    photo_paths = db.Column(db.Text)  # JSON-Array mit Foto-Pfaden
    plan_path = db.Column(db.String(255))  # Pfad zum 3D-Plan oder technischen Plan
    
    # Ausführung/Dokumentation
    actual_start_time = db.Column(db.DateTime)  # Tatsächlicher Beginn
    actual_end_time = db.Column(db.DateTime)  # Tatsächliches Ende
    actual_duration = db.Column(db.Integer)  # Tatsächliche Dauer in Minuten
    completion_notes = db.Column(db.Text)  # Notizen nach Abschluss
    quality_check = db.Column(db.Boolean, default=False)  # Qualitätskontrolle durchgeführt
    customer_signature = db.Column(db.Boolean, default=False)  # Kunde hat abgenommen
    
    # Allgemeine Notizen
    notes = db.Column(db.Text)  # Zusätzliche Notizen
    
    # Beziehung
    order = db.relationship('Order', backref=db.backref('work_instruction', uselist=False))
    
    def generate_instruction_number(self):
        """Generiert eine eindeutige Arbeitsanweisungs-Nummer"""
        from datetime import datetime
        date_part = datetime.now().strftime('%Y%m%d')
        # Sichere Generierung auch wenn Order keine Quote hat
        if self.order_id:
            order_part = f"A{self.order_id:04d}"
        else:
            order_part = f"A{datetime.now().strftime('%H%M%S')}"
        return f"AW-{date_part}-{order_part}"
    
    @property
    def status_color(self):
        """Gibt eine CSS-Klasse für den Status zurück"""
        status_colors = {
            'Erstellt': 'text-primary',
            'In Bearbeitung': 'text-warning',
            'Abgeschlossen': 'text-success',
            'Pausiert': 'text-secondary',
            'Abgebrochen': 'text-danger'
        }
        return status_colors.get(self.status, 'text-muted')
    
    @property
    def priority_color(self):
        """Gibt eine CSS-Klasse für die Priorität zurück"""
        priority_colors = {
            'Niedrig': 'text-success',
            'Normal': 'text-primary',
            'Hoch': 'text-warning',
            'Dringend': 'text-danger'
        }
        return priority_colors.get(self.priority, 'text-muted')
    
    def get_progress_percentage(self):
        """Berechnet den Fortschritt basierend auf Status"""
        progress_map = {
            'Erstellt': 0,
            'In Bearbeitung': 50,
            'Abgeschlossen': 100,
            'Pausiert': 25,
            'Abgebrochen': 0
        }
        return progress_map.get(self.status, 0)
