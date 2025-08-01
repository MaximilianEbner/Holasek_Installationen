
"""
Datenbankmodelle für die InstallationApp
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salutation = db.Column(db.String(100))  # Anrede (optional)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    customer_manager = db.Column(db.String(100))  # Kundenbetreuer (optional)
    acquisition_channel_id = db.Column(db.Integer, db.ForeignKey('acquisition_channel.id'))  # Akquisekanal
    detailed_acquisition_channel = db.Column(db.Text)  # Detaillierter Akquisekanal (Textfeld)
    
    # Workflow-Felder
    status = db.Column(db.String(50), default='1. Termin vereinbaren')  # Status im Workflow
    appointment_date = db.Column(db.Date)  # Datum des 1. Termins
    appointment_notes = db.Column(db.Text)  # Notizen zum 1. Termin
    second_appointment_date = db.Column(db.Date)  # Datum des 2. Termins
    second_appointment_notes = db.Column(db.Text)  # Notizen zum 2. Termin
    comments = db.Column(db.Text)  # Allgemeine Kommentare zum Kunden
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehungen
    quotes = db.relationship('Quote', backref='customer', lazy=True)
    acquisition_channel = db.relationship('AcquisitionChannel', backref='customers')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_status_badge_class(self):
        """Gibt die Bootstrap-Badge-Klasse für den aktuellen Status zurück"""
        status_classes = {
            '1. Termin vereinbaren': 'bg-warning',
            '1. Termin vereinbart': 'bg-info',
            'Angebot erstellen': 'bg-primary',
            '2. Termin vereinbaren': 'bg-warning',
            'Warten auf Rückmeldung': 'bg-success',
            'Kein Interesse': 'bg-secondary'
        }
        return status_classes.get(self.status, 'bg-light')
    
    def get_next_action(self):
        """Gibt die nächste erforderliche Aktion zurück"""
        if self.status == '1. Termin vereinbaren':
            return 'Ersten Termin im Kalender eintragen'
        elif self.status == '1. Termin vereinbart':
            return 'Kundentermin wahrnehmen'
        elif self.status == 'Angebot erstellen':
            return 'Angebot basierend auf 1. Termin erstellen'
        elif self.status == '2. Termin vereinbaren':
            return 'Zweiten Termin für Angebotsvorstellung vereinbaren'
        elif self.status == 'Warten auf Rückmeldung':
            return 'Auf Kundenentscheidung warten'
        elif self.status == 'Kein Interesse':
            return 'Kunde hat aktuell kein Interesse'
        return 'Unbekannter Status'
    
    def check_auto_status_update(self):
        """Prüft und führt automatische Status-Updates durch"""
        from datetime import date, timedelta
        
        # Automatisches Update: 1. Termin war gestern -> "Angebot erstellen"
        if (self.status == '1. Termin vereinbart' and 
            self.appointment_date and 
            self.appointment_date < date.today()):
            self.status = 'Angebot erstellen'
            return True
        
        return False

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    project_description = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Entwurf')  # Entwurf, Gesendet, Angenommen, Abgelehnt, Auftrag storniert
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.Date)
    include_additional_info = db.Column(db.Boolean, default=True)
    # Neue PDF-Preistransparenz Modi: 'standard', 'detailed', 'total_only'
    price_display_mode = db.Column(db.String(20), default='standard')  
    # Alte Kompatibilität beibehalten (deprecated, wird durch price_display_mode ersetzt)
    show_subitem_prices = db.Column(db.Boolean, default=False)  # Preistransparenz Unterpositionen
    markup_percentage = db.Column(db.Float, default=15.0)  # Aufschlag in Prozent (Standard: 15%)
    
    # Editierbare Zusatzinformationen für PDF
    leistungsumfang = db.Column(db.Text, default='• Demontage der bestehenden Produkte inklusive Entsorgung\n• Montage der im Angebot angeführten Produkte\n• Anschluss an bestehendes Gebäudeleitungssystem im unmittelbaren Umbaubereich ab Badezimmer oder in der Dusche\n• Diverse Ausgleichs- und Abdichtungsarbeiten')
    objektinformationen = db.Column(db.Text, default='• Einfamilienhaus\n• Zuschnitt vor dem Gebäude möglich\n• Parken vor dem Gebäude möglich')
    installationsleistungen = db.Column(db.Text, default='• Abfluss Dusche herrichten\n• Armatur Dusche versetzen\n\nNebenabsprache mit dem Kunden:\n• Demontage, Vorbereitung und Entsorgung erfolgt durch Innsan')
    
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
    
    def calculate_price_with_markup(self):
        """Berechnet den Preis der Unterposition inklusive Aufschlag - für PDF-Export"""
        base_price = self.calculate_price()
        if self.quote_item and self.quote_item.quote and self.quote_item.quote.markup_percentage and self.quote_item.quote.markup_percentage > 0:
            markup_factor = 1 + (self.quote_item.quote.markup_percentage / 100)
            return base_price * markup_factor
        return base_price

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
    __tablename__ = 'position_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    # category = db.Column(db.String(64))  # Kategorie (UmbauWanneZurDusche, etc.) - REMOVED
    description = db.Column(db.Text)  # Beschreibung der Vorlage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Kalkulationsfelder - welche Parameter sind für diese Vorlage aktiviert
    enable_length = db.Column(db.Boolean, default=False)  # Länge aktiviert
    enable_width = db.Column(db.Boolean, default=False)   # Breite aktiviert
    enable_height = db.Column(db.Boolean, default=False)  # Höhe aktiviert
    enable_area = db.Column(db.Boolean, default=False)    # Fläche aktiviert (wird automatisch berechnet)
    enable_volume = db.Column(db.Boolean, default=False)  # Volumen aktiviert (wird automatisch berechnet)
    
    subitems = db.relationship('PositionTemplateSubItem', backref='template', cascade='all, delete-orphan', lazy=True, order_by='PositionTemplateSubItem.position')

class PositionTemplateSubItem(db.Model):
    __tablename__ = 'position_template_subitems'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('position_templates.id'), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    item_type = db.Column(db.String(32), nullable=False)  # bestellteil, arbeitsvorgang, sonstiges
    unit = db.Column(db.String(32))  # z.B. qm, m, Stück
    price_per_unit = db.Column(db.Float)
    formula = db.Column(db.String(128))  # Optional: Formel für Berechnung (z.B. hoehe*breite/10000)
    position = db.Column(db.Integer, default=0)  # Position für Sortierung per Drag & Drop
    
    # Felder für Bestellteil (konsistent mit QuoteSubItem)
    requires_order = db.Column(db.Boolean, default=False)
    supplier = db.Column(db.String(200))
    part_number = db.Column(db.String(100))  # Mapping: supplier_part_number -> part_number
    part_quantity = db.Column(db.String(50), default='1')
    part_price = db.Column(db.Float, default=0.0)
    
    # Felder für Arbeitsvorgang (konsistent mit QuoteSubItem)
    hours = db.Column(db.Float, default=0.0)
    hourly_rate = db.Column(db.Float, default=95.0)
    
    # Felder für Sonstiges (konsistent mit QuoteSubItem)
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
    
    @property
    def supplier_part_number(self):
        """Alias für part_number für Template-Kompatibilität"""
        return self.part_number
    
    @supplier_part_number.setter
    def supplier_part_number(self, value):
        """Setter für part_number über supplier_part_number Alias"""
        self.part_number = value
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
        try:
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
            
            # Erst hier committen nach allen Änderungen
            db.session.commit()
            return setting
        except Exception as e:
            db.session.rollback()
            raise e  # Exception weiterwerfen für bessere Fehlerbehandlung

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
    
    @property
    def net_amount(self):
        """Nettosumme des Auftrags (ohne MwSt.)"""
        return self.quote.calculate_net_total() if self.quote else 0.0
    
    def has_anzahlung_invoice(self):
        """Prüft, ob bereits eine Anzahlungsrechnung existiert"""
        return any(invoice.invoice_type == 'anzahlung' for invoice in self.invoices)
    
    def has_schluss_invoice(self):
        """Prüft, ob bereits eine Schlussrechnung existiert"""
        return any(invoice.invoice_type == 'schluss' for invoice in self.invoices)
    
    def can_create_anzahlung(self):
        """Prüft, ob eine Anzahlungsrechnung erstellt werden kann"""
        return (self.status in ['Angenommen', 'Geplant', 'In Arbeit'] and 
                not self.has_anzahlung_invoice())
    
    def can_create_schluss(self):
        """Prüft, ob eine Schlussrechnung erstellt werden kann"""
        return (self.status == 'Abgeschlossen' and 
                self.has_anzahlung_invoice() and 
                not self.has_schluss_invoice())
    
    def get_total_invoiced_amount(self):
        """Gibt den Gesamtbetrag aller erstellten Rechnungen zurück"""
        return sum(invoice.final_amount for invoice in self.invoices)
    
    def get_outstanding_amount(self):
        """Gibt den noch offenen Rechnungsbetrag zurück"""
        total_invoiced = sum(invoice.final_amount for invoice in self.invoices if invoice.status == 'bezahlt')
        return self.net_amount - total_invoiced
    
    def get_invoice_status_summary(self):
        """Gibt eine Zusammenfassung des Rechnungsstatus zurück"""
        anzahlung = next((inv for inv in self.invoices if inv.invoice_type == 'anzahlung'), None)
        schluss = next((inv for inv in self.invoices if inv.invoice_type == 'schluss'), None)
        
        return {
            'anzahlung_created': anzahlung is not None,
            'anzahlung_paid': anzahlung.status == 'bezahlt' if anzahlung else False,
            'schluss_created': schluss is not None,
            'schluss_paid': schluss.status == 'bezahlt' if schluss else False,
            'total_paid': sum(inv.final_amount for inv in self.invoices if inv.status == 'bezahlt'),
            'total_outstanding': self.get_outstanding_amount()
        }

class SupplierOrder(db.Model):
    """Model für Lieferantenbestellungen"""
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # Verknüpfung zum Auftrag
    supplier_name = db.Column(db.String(200), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Noch nicht bestellt')  # Noch nicht bestellt, Bestellt, Bestätigt, Geliefert
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
    sonstiges = db.Column(db.Text)  # Sonstiges (früher Sicherheitshinweise)
    tools_required = db.Column(db.Text)  # Benötigte Werkzeuge
    estimated_duration = db.Column(db.Integer)  # Geschätzte Dauer in Stunden
    priority = db.Column(db.String(20), default='Normal')  # Niedrig, Normal, Hoch, Dringend
    
    # Montage-spezifisch
    installation_location = db.Column(db.String(255))  # Montageort (z.B. Raum)
    access_requirements = db.Column(db.Text)  # Zugangserfordernisse
    
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
    
    # Gespeicherte Arbeitsschritte und Teile (als JSON)
    work_steps_data = db.Column(db.Text)  # JSON-Array mit bearbeiteten Arbeitsschritten
    work_parts_data = db.Column(db.Text)  # JSON-Array mit bearbeiteten Teilen
    
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


class AcquisitionChannel(db.Model):
    """Akquisekanäle für Kunden"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AcquisitionChannel {self.name}>'

class Invoice(db.Model):
    """Rechnungsmodell für Anzahlungs- und Schlussrechnungen"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)  # z.B. "R-2025-001"
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # Für allgemeine Rechnungen optional
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # Für allgemeine Rechnungen
    invoice_type = db.Column(db.String(20), nullable=False)  # 'anzahlung', 'schluss', 'allgemein'
    percentage = db.Column(db.Float, nullable=False)  # 30.0, 70.0
    base_amount = db.Column(db.Float, nullable=False)  # Grundbetrag des Auftrags (netto)
    invoice_amount = db.Column(db.Float, nullable=False)  # Rechnungsbetrag (% vom Grundbetrag)
    previous_payments = db.Column(db.Float, default=0.0)  # Bereits erhaltene Anzahlungen
    final_amount = db.Column(db.Float, nullable=False)  # Finaler Rechnungsbetrag
    vat_rate = db.Column(db.Float, default=20.0)  # MwSt.-Satz in Prozent
    vat_amount = db.Column(db.Float, nullable=False)  # MwSt.-Betrag
    gross_amount = db.Column(db.Float, nullable=False)  # Bruttogesamtbetrag
    
    # Nur das project_name Feld für flexible Schlussrechnung-Struktur
    # Alle anderen Werte werden aus bestehenden Models berechnet:
    # - material_costs → Summe aus QuoteItem (item_type = bestellteil + sonstiges)
    # - labor_costs → Summe aus QuoteItem (item_type = arbeitsvorgang)
    # - labor_rate → Default aus Stammdaten
    # - downpayment_deduction → previous_payments (bereits vorhanden)
    # - net_total → invoice_amount (bereits vorhanden)
    # - vat_total → vat_amount (bereits vorhanden)
    project_name = db.Column(db.String(255))  # Wird aus Quote.project_description übernommen
    
    # Zusätzliche Felder für "Detaillierte Schlussrechnung"
    material_costs_editable = db.Column(db.Float, nullable=True)  # Editierbare Materialkosten
    labor_hours_editable = db.Column(db.Float, nullable=True)  # Editierbare Arbeitsstunden
    labor_rate_editable = db.Column(db.Float, nullable=True)  # Editierbarer Stundensatz
    labor_costs_editable = db.Column(db.Float, nullable=True)  # Berechnete Arbeitskosten (stunden * satz)
    material_description = db.Column(db.String(255), default='Materialkosten')  # Materialbezeichnung
    labor_description = db.Column(db.String(255), default='Arbeitsleistung')  # Arbeitsbezeichnung
    
    due_date = db.Column(db.Date, nullable=False)  # Fälligkeitsdatum
    payment_terms = db.Column(db.Integer, default=14)  # Zahlungsziel in Tagen
    status = db.Column(db.String(20), default='erstellt')  # 'erstellt', 'versendet', 'teilweise_bezahlt', 'bezahlt', 'ueberfaellig'
    paid_date = db.Column(db.Date, nullable=True)  # Bezahldatum
    payment_reference = db.Column(db.String(100), nullable=True)  # Zahlungsreferenz
    comments = db.Column(db.Text, nullable=True)  # Kommentare und Notizen
    
    # Neue Felder für Teilzahlungen
    paid_amount = db.Column(db.Float, default=0.0)  # Bereits bezahlter Betrag
    payment_comment = db.Column(db.Text, nullable=True)  # Kommentar zur Teilzahlung
    service_description = db.Column(db.Text, nullable=True)  # Leistungsbeschreibung für allgemeine Rechnungen
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref=db.backref('invoices', lazy=True, cascade='all, delete-orphan'))
    customer = db.relationship('Customer', backref=db.backref('invoices', lazy=True))
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number} - {self.invoice_type.title()} - {self.final_amount}€>'
    
    @staticmethod
    def generate_invoice_number():
        """Generiert eine neue, fortlaufende Rechnungsnummer"""
        from datetime import datetime
        year = datetime.now().year
        
        # Finde die höchste Rechnungsnummer des aktuellen Jahres
        latest_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f'R-{year}-%')
        ).order_by(Invoice.invoice_number.desc()).first()
        
        if latest_invoice:
            # Extrahiere die Nummer aus dem Format "R-YYYY-XXX"
            try:
                last_number = int(latest_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f'R-{year}-{new_number:03d}'
    
    def calculate_amounts(self):
        """Berechnet alle Beträge basierend auf Grundbetrag und Prozentsatz"""
        # Sichere Behandlung von None-Werten
        if self.base_amount is None:
            raise ValueError("Grundbetrag darf nicht None sein")
        if self.vat_rate is None:
            self.vat_rate = 20.0  # Standard-MwSt.-Satz
        if self.previous_payments is None:
            self.previous_payments = 0.0
        
        if self.invoice_type == 'allgemein':
            # Bei allgemeinen Rechnungen: final_amount = base_amount
            self.percentage = 100.0  # Immer 100% bei allgemeinen Rechnungen
            self.invoice_amount = self.base_amount
            self.final_amount = self.base_amount
        else:
            # Für Anzahlungs- und Schlussrechnungen
            if self.percentage is None:
                raise ValueError("Prozentsatz darf nicht None sein")
            
            self.invoice_amount = self.base_amount * (self.percentage / 100)
            
            if self.invoice_type == 'schluss':
                # Bei Schlussrechnung: Restbetrag = Auftragssumme - bereits erhaltene Anzahlungen
                self.final_amount = self.base_amount - self.previous_payments
            else:
                # Bei Anzahlungsrechnungen: final_amount ist der Prozentsatz-Betrag
                self.final_amount = self.invoice_amount
        
        # MwSt. berechnen auf final_amount
        self.vat_amount = self.final_amount * (self.vat_rate / 100)
        self.gross_amount = self.final_amount + self.vat_amount
    
    def is_overdue(self):
        """Prüft, ob die Rechnung überfällig ist"""
        from datetime import date
        return (self.status not in ['bezahlt'] and 
                self.due_date and 
                self.due_date < date.today())
    
    def days_overdue(self):
        """Gibt die Anzahl der überfälligen Tage zurück"""
        if not self.is_overdue():
            return 0
        from datetime import date
        return (date.today() - self.due_date).days
    
    def mark_as_paid(self, paid_date=None, payment_reference=None, comment=None):
        """Markiert die Rechnung als vollständig bezahlt"""
        from datetime import date
        self.status = 'bezahlt'
        self.paid_date = paid_date or date.today()
        self.paid_amount = self.gross_amount  # Vollständig bezahlt
        if payment_reference:
            self.payment_reference = payment_reference
        if comment:
            if self.comments:
                self.comments += f"\n\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {comment}"
            else:
                self.comments = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {comment}"
        self.updated_at = datetime.utcnow()
    
    def mark_as_partially_paid(self, paid_amount, paid_date=None, payment_reference=None, comment=None):
        """Markiert die Rechnung als teilweise bezahlt"""
        from datetime import date
        
        if paid_amount <= 0:
            raise ValueError("Bezahlter Betrag muss größer als 0 sein")
        if paid_amount > self.gross_amount:
            raise ValueError("Bezahlter Betrag kann nicht größer als der Gesamtbetrag sein")
        
        self.paid_amount = paid_amount
        self.paid_date = paid_date or date.today()
        
        # Status basierend auf bezahltem Betrag setzen
        if paid_amount >= self.gross_amount:
            self.status = 'bezahlt'
        else:
            self.status = 'teilweise_bezahlt'
        
        if payment_reference:
            self.payment_reference = payment_reference
        
        # Kommentar hinzufügen
        payment_info = f"Teilzahlung: {paid_amount:.2f}€ von {self.gross_amount:.2f}€"
        if comment:
            payment_info += f" - {comment}"
        
        if self.payment_comment:
            self.payment_comment += f"\n\n[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {payment_info}"
        else:
            self.payment_comment = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {payment_info}"
        
        self.updated_at = datetime.utcnow()
    
    def get_remaining_amount(self):
        """Gibt den noch ausstehenden Betrag zurück"""
        return max(0, self.gross_amount - (self.paid_amount or 0))
    
    def get_payment_percentage(self):
        """Gibt den bezahlten Prozentsatz zurück"""
        if self.gross_amount == 0:
            return 0
        return min(100, (self.paid_amount or 0) / self.gross_amount * 100)
    
    def get_status_badge_class(self):
        """Gibt die Bootstrap-Klasse für den Status-Badge zurück"""
        status_classes = {
            'erstellt': 'bg-light text-dark border',
            'versendet': 'bg-primary',
            'teilweise_bezahlt': 'bg-info',
            'bezahlt': 'bg-success',
            'ueberfaellig': 'bg-danger'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_type_display(self):
        """Gibt den anzeigbaren Typ zurück"""
        type_map = {
            'anzahlung': 'Anzahlungsrechnung',
            'schluss': 'Schlussrechnung',
            'allgemein': 'Rechnung'
        }
        return type_map.get(self.invoice_type, 'Rechnung')
    
    # Neue Berechnungsmethoden für flexible Schlussrechnung-Struktur
    def get_material_costs(self):
        """Berechnet Materialkosten aus QuoteItems (bestellteil + sonstiges)"""
        if not self.order or not self.order.quote:
            return 0.0
        
        material_cost = 0.0
        for item in self.order.quote.quote_items:
            for sub_item in item.sub_items:
                if sub_item.item_type in ['bestellteil', 'sonstiges']:
                    material_cost += sub_item.calculate_price()
        return material_cost
    
    def get_labor_costs(self):
        """Berechnet Arbeitskosten aus QuoteItems (arbeitsvorgang)"""
        if not self.order or not self.order.quote:
            return 0.0
        
        labor_cost = 0.0
        for item in self.order.quote.quote_items:
            for sub_item in item.sub_items:
                if sub_item.item_type == 'arbeitsvorgang':
                    labor_cost += sub_item.calculate_price()
        return labor_cost
    
    def get_labor_hours(self):
        """Berechnet Gesamtstunden aus QuoteItems (arbeitsvorgang)"""
        if not self.order or not self.order.quote:
            return 0.0
        
        total_hours = 0.0
        for item in self.order.quote.quote_items:
            for sub_item in item.sub_items:
                if sub_item.item_type == 'arbeitsvorgang':
                    total_hours += sub_item.hours or 0.0
        return total_hours
    
    def get_default_labor_rate(self):
        """Holt den Standard-Stundensatz aus den Stammdaten"""
        return CompanySettings.get_setting('default_hourly_rate', 95.0)
    
    def get_project_name(self):
        """Holt den Projektnamen aus dem verknüpften Angebot"""
        if self.project_name:
            return self.project_name
        elif self.order and self.order.quote:
            return self.order.quote.project_description or f"Auftrag {self.order.order_number}"
        elif self.customer:
            return f"Rechnung für {self.customer.full_name}"
        return "Allgemeine Rechnung"
    
    def get_subtotal_net(self):
        """Berechnet Zwischensumme netto (Material + Arbeitskosten)"""
        return self.get_material_costs() + self.get_labor_costs()
    
    def get_downpayment_deduction(self):
        """Anzahlungsabzug ist previous_payments"""
        return self.previous_payments or 0.0
    
    def get_net_total(self):
        """Netto-Gesamtsumme ist invoice_amount"""
        return self.invoice_amount or 0.0
    
    def get_vat_total(self):
        """MwSt.-Gesamtsumme ist vat_amount"""
        return self.vat_amount or 0.0


class LoginAdmin(db.Model):
    """Login-Admin-Model für Authentifizierung"""
    __tablename__ = 'login_admins'
    
    login_id = db.Column(db.Integer, primary_key=True)
    login_username = db.Column(db.String(50), unique=True, nullable=False)
    login_password_hash = db.Column(db.String(255), nullable=False)
    login_created_at = db.Column(db.DateTime, default=datetime.utcnow)
    login_last_login = db.Column(db.DateTime)
    login_is_active = db.Column(db.Boolean, default=True)
    
    def set_login_password(self, password):
        """Setzt ein gehashtes Passwort"""
        from werkzeug.security import generate_password_hash
        self.login_password_hash = generate_password_hash(password)
    
    def check_login_password(self, password):
        """Überprüft das Passwort"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.login_password_hash, password)
    
    @staticmethod
    def create_login_admin(username, password):
        """Erstellt einen neuen Admin"""
        login_admin = LoginAdmin(login_username=username)
        login_admin.set_login_password(password)
        return login_admin
    
    def __repr__(self):
        return f'<LoginAdmin {self.login_username}>'

class InvoiceReminder(db.Model):
    """Reminder für fällige Rechnungserstellung"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # 'anzahlung' oder 'schluss'
    due_date = db.Column(db.Date, nullable=False)  # Wann der Reminder fällig ist
    is_dismissed = db.Column(db.Boolean, default=False)  # Wurde der Reminder ausgeblendet?
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Beziehung
    order = db.relationship('Order', backref='invoice_reminders')
    
    @staticmethod
    def create_reminders_for_order(order):
        """Erstellt Reminder für einen neuen Auftrag"""
        from datetime import timedelta
        
        reminders = []
        
        # Anzahlungsreminder: 8 Wochen vor Auftragsbeginn
        if order.start_date:
            anzahlung_date = order.start_date - timedelta(weeks=8)
            # Nur erstellen wenn das Datum in der Zukunft liegt
            if anzahlung_date >= datetime.now().date():
                anzahlung_reminder = InvoiceReminder(
                    order_id=order.id,
                    reminder_type='anzahlung',
                    due_date=anzahlung_date
                )
                reminders.append(anzahlung_reminder)
        
        # Endrechnung: Nach Auftragsabschluss (end_date + 1 Tag)
        if order.end_date:
            schluss_date = order.end_date + timedelta(days=1)
            schluss_reminder = InvoiceReminder(
                order_id=order.id,
                reminder_type='schluss',
                due_date=schluss_date
            )
            reminders.append(schluss_reminder)
        
        return reminders
    
    @staticmethod
    def get_active_reminders():
        """Holt alle aktiven Reminder die fällig sind"""
        from datetime import date
        return InvoiceReminder.query.filter(
            InvoiceReminder.due_date <= date.today(),
            InvoiceReminder.is_dismissed == False
        ).join(Order).filter(Order.status.in_(['Geplant', 'In Arbeit', 'Abgeschlossen'])).all()
    
    def get_existing_invoice_count(self):
        """Prüft ob bereits Rechnungen vom entsprechenden Typ existieren"""
        return Invoice.query.filter_by(
            order_id=self.order_id,
            invoice_type=self.reminder_type
        ).count()
    
    def is_invoice_needed(self):
        """Prüft ob tatsächlich eine Rechnung erstellt werden muss"""
        return self.get_existing_invoice_count() == 0
    
    def __repr__(self):
        return f'<InvoiceReminder {self.reminder_type} for Order {self.order_id}>'
