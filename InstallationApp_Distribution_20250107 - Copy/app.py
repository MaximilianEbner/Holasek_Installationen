"""
Optimierte Version der InstallationApp mit verbesserter Struktur und Fehlerbehandlung
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from datetime import date, timedelta
import os
import json
from werkzeug.utils import secure_filename

# Lokale Imports
from config import Config
from models import db, Customer, Quote, QuoteItem, QuoteSubItem, Supplier, CompanySettings, QuoteRejection, Order, SupplierOrder, SupplierOrderItem, WorkInstruction
from forms import CustomerForm, QuoteForm, SupplierForm, SettingsForm, QuoteRejectionForm, SupplierOrderUpdateForm, OrderForm, OrderUpdateForm
from utils import get_default_hourly_rate, generate_quote_number, load_position_templates, load_suppliers, update_quote_total, safe_float_conversion, parse_quantity_from_text
from pdf_export import PDFExporter
from work_steps import get_work_steps

# Upload-Konfiguration und Hilfsfunktionen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    """Prüft ob Dateiendung erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    """App Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Datenbank initialisieren
    db.init_app(app)
    
    # Upload-Konfiguration
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Stelle sicher, dass Upload-Ordner existiert
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Template-Filter registrieren
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Konvertiert JSON-String zu Python-Objekt"""
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    # Template-Funktionen registrieren
    @app.context_processor
    def inject_global_vars():
        return {
            'get_default_hourly_rate': get_default_hourly_rate
        }
    
    # Blueprints registrieren (hier vereinfacht als Routen)
    register_routes(app)
    
    return app

def register_routes(app):
    """Registriert alle Routen"""
    
    # Hauptseiten
    @app.route('/')
    def index():
        from models import Customer, Quote, Order, SupplierOrder
        from datetime import datetime, timedelta
        
        # Dashboard-Statistiken berechnen (ohne Preisinformationen)
        total_customers = Customer.query.count()
        pending_quotes = Quote.query.filter_by(status='Entwurf').count()
        active_orders = Order.query.filter(Order.status.in_(['Geplant', 'In Arbeit'])).count()
        
        # Letzte Aktivitäten (letzte 5 Angebote/Aufträge)
        recent_quotes = Quote.query.order_by(Quote.created_at.desc()).limit(3).all()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(3).all()
        
        # Anstehende Termine (Aufträge die in den nächsten 7 Tagen starten)
        upcoming_orders = Order.query.filter(
            Order.start_date >= datetime.now().date(),
            Order.start_date <= (datetime.now() + timedelta(days=7)).date(),
            Order.status.in_(['Geplant', 'In Arbeit'])
        ).order_by(Order.start_date).all()
        
        # Offene Lieferantenbestellungen
        pending_deliveries = SupplierOrder.query.filter(
            SupplierOrder.status.in_(['Bestellt', 'Bestätigt'])
        ).count()
        
        return render_template('index.html', 
                             total_customers=total_customers,
                             pending_quotes=pending_quotes,
                             active_orders=active_orders,
                             recent_quotes=recent_quotes,
                             recent_orders=recent_orders,
                             upcoming_orders=upcoming_orders,
                             pending_deliveries=pending_deliveries,
                             today=datetime.now().strftime('%d.%m.%Y'))
    
    # Kunden-Routen
    @app.route('/customers')
    def customers():
        customers = Customer.query.all()
        return render_template('customers.html', customers=customers)
    
    @app.route('/customer/new', methods=['GET', 'POST'])
    def new_customer():
        form = CustomerForm()
        if form.validate_on_submit():
            try:
                customer = Customer(
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    phone=form.phone.data,
                    address=form.address.data,
                    city=form.city.data,
                    postal_code=form.postal_code.data
                )
                db.session.add(customer)
                db.session.commit()
                flash('Kunde wurde erfolgreich hinzugefügt!', 'success')
                return redirect(url_for('customers'))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('customer_form.html', form=form, title='Neuer Kunde')
    
    @app.route('/customer/<int:id>/edit', methods=['GET', 'POST'])
    def edit_customer(id):
        customer = Customer.query.get_or_404(id)
        form = CustomerForm(obj=customer)
        
        if form.validate_on_submit():
            try:
                form.populate_obj(customer)
                db.session.commit()
                flash('Kunde wurde erfolgreich bearbeitet!', 'success')
                return redirect(url_for('customers'))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('customer_form.html', form=form, title='Kunde bearbeiten', customer=customer)
    
    @app.route('/customer/<int:id>/delete')
    def delete_customer(id):
        customer = Customer.query.get_or_404(id)
        
        # Prüfe ob Kunde Angebote hat
        if customer.quotes:
            flash('Kunde kann nicht gelöscht werden - es existieren noch Angebote für diesen Kunden!', 'error')
            return redirect(url_for('customers'))
        
        try:
            customer_name = customer.full_name
            db.session.delete(customer)
            db.session.commit()
            flash(f'Kunde {customer_name} wurde erfolgreich gelöscht!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Löschen: {str(e)}', 'error')
        
        return redirect(url_for('customers'))

    # Angebots-Routen
    @app.route('/quotes')
    def quotes():
        quotes = Quote.query.all()
        return render_template('quotes.html', quotes=quotes)
    
    @app.route('/quote/new', methods=['GET', 'POST'])
    def new_quote():
        form = QuoteForm()
        
        if form.validate_on_submit():
            try:
                # Validiere dass der Kunde existiert
                customer_id = int(form.customer_id.data)
                customer = Customer.query.get(customer_id)
                if not customer:
                    flash('Ungültiger Kunde ausgewählt!', 'error')
                    return render_template('quote_form.html', form=form, title='Neues Angebot')
                
                quote = Quote(
                    quote_number=generate_quote_number(),
                    customer_id=customer_id,
                    project_description=form.project_description.data,
                    valid_until=form.valid_until.data,
                    include_additional_info=form.include_additional_info.data,
                    markup_percentage=form.markup_percentage.data,
                    status='Entwurf',
                    total_amount=0.0
                )
                db.session.add(quote)
                db.session.commit()
                
                flash('Angebot wurde erfolgreich erstellt!', 'success')
                return redirect(url_for('edit_quote', id=quote.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Erstellen des Angebots: {str(e)}', 'error')
        
        return render_template('quote_form.html', form=form, title='Neues Angebot')
    
    @app.route('/quote/<int:id>/edit')
    def edit_quote(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        suppliers = Supplier.query.all()
        work_steps = get_work_steps()
        return render_template('quote_edit.html', quote=quote, suppliers=suppliers, work_steps=work_steps)
    
    @app.route('/quote/<int:id>/add_detailed_item', methods=['POST'])
    def add_detailed_quote_item(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        try:
            # Hauptposition
            description = request.form.get('description', '').strip()
            position_number = request.form.get('position_number', type=int)
            
            if not description or not position_number:
                flash('Bitte füllen Sie Beschreibung und Positionsnummer ein!', 'error')
                return redirect(url_for('edit_quote', id=id))
            
            # Unterpositionen verarbeiten
            sub_items_data = process_sub_items(request.form)
            
            # Gesamtpreis berechnen
            total_price = sum(item['price'] for item in sub_items_data)
            
            # Hauptposition erstellen
            quote_item = QuoteItem(
                quote_id=quote.id,
                quantity=1,
                unit_price=total_price,
                total_price=total_price,
                description=description,
                position_number=position_number,
                requires_order=False,
                supplier=''
            )
            db.session.add(quote_item)
            db.session.flush()  # Um ID zu bekommen
            
            # Unterpositionen hinzufügen
            create_sub_items(quote_item.id, position_number, sub_items_data)
            
            db.session.commit()
            quote.update_total()
            
            flash('Detaillierte Position wurde hinzugefügt!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Hinzufügen der Position: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))
    
    @app.route('/quote/<int:id>/add_work_position', methods=['POST'])
    def add_work_position(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        try:
            # Hauptposition erstellen
            description = request.form.get('description')
            position_number = int(request.form.get('position_number', 1))
            
            # Arbeitsschritte aus dem Formular lesen
            work_step_categories = request.form.getlist('work_step_categories[]')
            work_step_names = request.form.getlist('work_step_names[]')
            work_step_hours = request.form.getlist('work_step_hours[]')
            work_step_rates = request.form.getlist('work_step_rates[]')
            
            if not work_step_categories:
                flash('Keine Arbeitsschritte ausgewählt!', 'error')
                return redirect(url_for('edit_quote', id=id))
            
            # Hauptposition erstellen
            total_price = 0
            
            # Berechne Gesamtpreis aus allen Arbeitsschritten
            for i in range(len(work_step_categories)):
                hours = float(work_step_hours[i]) if i < len(work_step_hours) else 0
                rate = float(work_step_rates[i]) if i < len(work_step_rates) else get_default_hourly_rate()
                total_price += hours * rate
            
            # Erstelle Hauptposition
            quote_item = QuoteItem(
                quote_id=quote.id,
                description=description,
                quantity=1,
                unit_price=total_price,
                total_price=total_price,
                position_number=position_number,
                requires_order=False,
                item_type='arbeitsposition'  # Neuer Typ für Arbeitspositionen
            )
            db.session.add(quote_item)
            db.session.flush()  # Um die ID zu bekommen
            
            # Erstelle Unterpositionen für jeden Arbeitsschritt
            for i in range(len(work_step_categories)):
                category = work_step_categories[i]
                step_name = work_step_names[i]
                hours = float(work_step_hours[i]) if i < len(work_step_hours) else 0
                rate = float(work_step_rates[i]) if i < len(work_step_rates) else get_default_hourly_rate()
                step_price = hours * rate
                
                sub_item = QuoteSubItem(
                    quote_item_id=quote_item.id,
                    description=f"{category}: {step_name}",
                    sub_number=i + 1,
                    item_type='arbeitsvorgang',
                    hours=hours,
                    hourly_rate=rate,
                    price=step_price
                )
                db.session.add(sub_item)
            
            db.session.commit()
            quote.update_total()
            
            flash('Arbeitsposition wurde hinzugefügt!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Hinzufügen der Arbeitsposition: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))

    @app.route('/quote/<int:id>/remove_item/<int:item_id>')
    def remove_quote_item(id, item_id):
        quote = Quote.query.get_or_404(id)
        item = QuoteItem.query.get_or_404(item_id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        if item.quote_id == quote.id:
            try:
                db.session.delete(item)
                db.session.commit()
                quote.update_total()
                flash('Position wurde entfernt!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Entfernen der Position: {str(e)}', 'error')
        else:
            flash('Ungültige Position!', 'error')
        
        return redirect(url_for('edit_quote', id=id))
    
    @app.route('/quote/<int:id>/delete')
    def delete_quote(id):
        quote = Quote.query.get_or_404(id)
        quote_number = quote.quote_number
        
        try:
            db.session.delete(quote)
            db.session.commit()
            flash(f'Angebot {quote_number} wurde erfolgreich gelöscht!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Löschen des Angebots: {str(e)}', 'error')
        
        return redirect(url_for('quotes'))
    
    # Status-Änderungen
    @app.route('/quote/<int:id>/send')
    def send_quote(id):
        return update_quote_status(id, 'Gesendet')
    
    @app.route('/quote/<int:id>/accept', methods=['GET', 'POST'])
    def accept_quote(id):
        quote = Quote.query.get_or_404(id)
        from forms import OrderForm
        from utils import generate_order_number
        
        # Prüfe ob bereits ein Auftrag existiert (außer bei stornierten)
        if quote.order and quote.status != 'Angenommen, Auftrag storniert':
            flash('Für dieses Angebot existiert bereits ein Auftrag!', 'warning')
            return redirect(url_for('view_order', order_id=quote.order.id))
        
        # Zusätzliche Prüfung für reine Angenommen-Status (ohne Stornierung)
        if quote.status == 'Angenommen' and quote.order:
            flash('Dieses Angebot wurde bereits angenommen und ein Auftrag erstellt.', 'warning')
            return redirect(url_for('view_order', order_id=quote.order.id))
        
        form = OrderForm()
        
        if request.method == 'GET':
            # Zeige Formular für Realisierungszeitraum
            return render_template('order_form.html', quote=quote, form=form, action='accept')
        
        if form.validate_on_submit():
            try:
                # Status auf Angenommen setzen
                quote.status = 'Angenommen'
                
                # Auftrag erstellen
                order_number = generate_order_number()
                order = Order(
                    order_number=order_number,
                    quote_id=quote.id,
                    start_date=form.start_date.data,
                    end_date=form.end_date.data,
                    project_manager=form.project_manager.data,
                    notes=form.notes.data,
                    status='Geplant'
                )
                
                db.session.add(order)
                db.session.flush()  # Um ID zu bekommen
                
                # Sammle alle Bestellteile pro Lieferant
                from utils import collect_supplier_orders, generate_supplier_order_email, get_supplier_email
                from models import SupplierOrder, SupplierOrderItem
                supplier_orders = collect_supplier_orders(quote)
                
                email_info = []
                
                # Generiere E-Mail-Templates für jeden Lieferanten
                for supplier_name, order_items in supplier_orders.items():
                    if order_items:  # Nur wenn Bestellteile vorhanden
                        supplier_email = get_supplier_email(supplier_name)
                        subject, html_body, plain_body = generate_supplier_order_email(quote, supplier_name, order_items, order_number)
                        
                        email_info.append({
                            'supplier': supplier_name,
                            'email': supplier_email,
                            'subject': subject,
                            'body': html_body,
                            'plain_body': plain_body,
                            'items_count': len(order_items)
                        })
                
                # Verknüpfe bestehende Lieferantenbestellungen mit dem Auftrag
                for supplier_order in quote.supplier_orders:
                    supplier_order.order_id = order.id
                
                db.session.commit()
                
                flash(f'Angebot {quote.quote_number} wurde angenommen und Auftrag {order_number} erstellt!', 'success')
                
                if email_info:
                    # Zeige E-Mail-Vorschau für Bestellungen
                    return render_template('quote_order_emails.html', quote=quote, order=order, email_info=email_info)
                else:
                    flash('Keine Bestellteile für Lieferanten gefunden.', 'info')
                    return redirect(url_for('view_order', order_id=order.id))
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Angebot annehmen: {str(e)}', 'error')
                return render_template('order_form.html', quote=quote, form=form, action='accept')
        
        return render_template('order_form.html', quote=quote, form=form, action='accept')
    
    @app.route('/quote/<int:id>/reject', methods=['GET', 'POST'])
    def reject_quote(id):
        quote = Quote.query.get_or_404(id)
        from forms import QuoteRejectionForm
        from models import QuoteRejection
        
        form = QuoteRejectionForm()
        
        if form.validate_on_submit():
            try:
                # Lösche vorherige Ablehnung falls vorhanden
                if quote.rejection:
                    db.session.delete(quote.rejection)
                
                # Erstelle neue Ablehnung
                rejection = QuoteRejection(
                    quote_id=quote.id,
                    rejection_reason=form.rejection_reason.data
                )
                db.session.add(rejection)
                
                # Status auf Abgelehnt setzen
                quote.status = 'Abgelehnt'
                db.session.commit()
                
                flash(f'Angebot {quote.quote_number} wurde als "Abgelehnt" markiert!', 'info')
                return redirect(url_for('edit_quote', id=id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Ablehnen: {str(e)}', 'error')
        
        return render_template('quote_reject.html', quote=quote, form=form)
    
    @app.route('/quote/<int:id>/reset')
    def reset_quote(id):
        return update_quote_status(id, 'Entwurf')
    
    # PDF Export
    @app.route('/quote/<int:id>/pdf')
    def export_quote_pdf(id):
        try:
            pdf_exporter = PDFExporter()
            return pdf_exporter.export_quote(id)
        except Exception as e:
            flash(f'Fehler beim PDF-Export: {str(e)}', 'error')
            return redirect(url_for('edit_quote', id=id))
    
    # Lieferanten-Routen
    @app.route('/suppliers')
    def suppliers():
        suppliers = Supplier.query.all()
        return render_template('suppliers.html', suppliers=suppliers)
    
    @app.route('/supplier/new', methods=['GET', 'POST'])
    def new_supplier():
        form = SupplierForm()
        if form.validate_on_submit():
            try:
                supplier = Supplier(
                    name=form.name.data,
                    contact_person=form.contact_person.data,
                    email=form.email.data,
                    phone=form.phone.data,
                    address=form.address.data,
                    category=form.category.data,
                    notes=form.notes.data
                )
                db.session.add(supplier)
                db.session.commit()
                flash('Lieferant wurde erfolgreich hinzugefügt!', 'success')
                return redirect(url_for('suppliers'))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('supplier_form.html', form=form, title='Neuer Lieferant')
    
    @app.route('/supplier/<int:id>/edit', methods=['GET', 'POST'])
    def edit_supplier(id):
        supplier = Supplier.query.get_or_404(id)
        form = SupplierForm(obj=supplier)
        
        if form.validate_on_submit():
            try:
                form.populate_obj(supplier)
                db.session.commit()
                flash('Lieferant wurde erfolgreich bearbeitet!', 'success')
                return redirect(url_for('suppliers'))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('supplier_form.html', form=form, title='Lieferant bearbeiten', supplier=supplier)
    
    @app.route('/supplier/<int:id>/delete')
    def delete_supplier(id):
        supplier = Supplier.query.get_or_404(id)
        try:
            db.session.delete(supplier)
            db.session.commit()
            flash('Lieferant wurde erfolgreich gelöscht!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Löschen: {str(e)}', 'error')
        
        return redirect(url_for('suppliers'))
    
    # Stammdaten
    @app.route('/stammdaten')
    def stammdaten():
        suppliers = Supplier.query.all()
        current_hourly_rate = get_default_hourly_rate()
        categories = db.session.query(Supplier.category).filter(
            Supplier.category.isnot(None)
        ).filter(Supplier.category != '').distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('stammdaten.html', 
                             suppliers=suppliers, 
                             current_hourly_rate=current_hourly_rate, 
                             categories=categories)
    
    @app.route('/stammdaten/arbeitsschritte')
    def work_steps_management():
        work_steps = get_work_steps()
        return render_template('work_steps_management.html', work_steps=work_steps)
    
    @app.route('/stammdaten/arbeitsschritte/update', methods=['POST'])
    def update_work_steps():
        try:
            # Hier würde normalerweise die work_steps.py Datei aktualisiert werden
            # Für jetzt zeigen wir nur eine Erfolgsmeldung
            flash('Arbeitsschritte wurden aktualisiert! (Funktion noch nicht vollständig implementiert)', 'info')
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
        
        return redirect(url_for('work_steps_management'))
    
    # Einstellungen
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        form = SettingsForm()
        form.default_hourly_rate.data = get_default_hourly_rate()
        
        if form.validate_on_submit():
            try:
                CompanySettings.set_setting(
                    'default_hourly_rate', 
                    form.default_hourly_rate.data,
                    'Standard-Stundensatz für Arbeitsvorgänge'
                )
                flash('Einstellungen wurden erfolgreich gespeichert!', 'success')
                return redirect(url_for('settings'))
            except Exception as e:
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('settings.html', form=form)
    
    # Admin-Routen
    @app.route('/admin/reload_templates')
    def reload_templates():
        success_positions = load_position_templates()
        success_suppliers = load_suppliers()
        
        if success_positions and success_suppliers:
            flash('Excel-Templates wurden erfolgreich neu geladen!', 'success')
        elif success_positions:
            flash('Positionsvorlagen geladen, aber Fehler bei Lieferanten!', 'warning')
        elif success_suppliers:
            flash('Lieferanten geladen, aber Fehler bei Positionsvorlagen!', 'warning')
        else:
            flash('Fehler beim Laden der Excel-Templates!', 'error')
        
        return redirect(url_for('index'))

    @app.route('/admin/reset_database')
    def reset_database():
        """Setzt die Datenbank komplett zurück und erstellt sie neu"""
        try:
            # Lösche alle Tabellen
            db.drop_all()
            
            # Erstelle alle Tabellen neu
            db.create_all()
            
            # Lade Templates
            load_position_templates()
            load_suppliers()
            
            # Erstelle Testkunden
            test_customer = Customer(
                first_name="Max",
                last_name="Mustermann", 
                email="max.mustermann@email.com",
                phone="+43 664 1234567",
                address="Musterstraße 123",
                city="Wien",
                postal_code="1010"
            )
            db.session.add(test_customer)
            db.session.commit()
            
            flash('Datenbank wurde erfolgreich zurückgesetzt und neu erstellt!', 'success')
            
        except Exception as e:
            flash(f'Fehler beim Zurücksetzen der Datenbank: {str(e)}', 'error')
            db.session.rollback()
            
        return redirect(url_for('index'))

    # Einfache Position hinzufügen
    @app.route('/quote/<int:id>/add_item', methods=['POST'])
    def add_quote_item(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        try:
            description = request.form.get('description', '').strip()
            quantity = safe_float_conversion(request.form.get('quantity'), 1.0)
            unit_price = safe_float_conversion(request.form.get('unit_price'), 0.0)
            
            if description and quantity > 0 and unit_price >= 0:
                total_price = unit_price * quantity
                
                quote_item = QuoteItem(
                    quote_id=quote.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    description=description
                )
                db.session.add(quote_item)
                db.session.commit()
                quote.update_total()
                
                flash('Position wurde hinzugefügt!', 'success')
            else:
                flash('Bitte füllen Sie alle Felder korrekt aus!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Hinzufügen der Position: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))

    # Angebot anzeigen
    @app.route('/quote/<int:id>')
    def view_quote(id):
        quote = Quote.query.get_or_404(id)
        return render_template('quote_view.html', quote=quote)

    # Angebot speichern
    @app.route('/quote/<int:id>/save', methods=['POST'])
    def save_quote(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        try:
            # Angebotsdaten aktualisieren
            project_description = request.form.get('project_description', '')
            valid_until = request.form.get('valid_until', '')
            include_additional_info = request.form.get('include_additional_info') == 'on'
            show_subitem_prices = request.form.get('show_subitem_prices') == 'on'
            markup_percentage = safe_float_conversion(request.form.get('markup_percentage'), 15.0)
            
            if project_description:
                quote.project_description = project_description
                
            if valid_until:
                from datetime import datetime
                quote.valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date()
                
            quote.include_additional_info = include_additional_info
            quote.show_subitem_prices = show_subitem_prices
            quote.markup_percentage = markup_percentage
            
            quote.update_total()
            flash('Angebot wurde erfolgreich gespeichert!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))

    # Position bearbeiten
    @app.route('/quote/<int:id>/edit_item/<int:item_id>', methods=['GET', 'POST'])
    def edit_quote_item(id, item_id):
        quote = Quote.query.get_or_404(id)
        item = QuoteItem.query.get_or_404(item_id)
        
        # Sicherheitscheck: Item gehört zum Quote
        if item.quote_id != quote.id:
            flash('Ungültige Position!', 'danger')
            return redirect(url_for('edit_quote', id=id))
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        if request.method == 'POST':
            try:
                if 'simple_edit' in request.form:
                    # Einfache Position bearbeiten
                    description = request.form.get('description', '').strip()
                    quantity = safe_float_conversion(request.form.get('quantity'), 1.0)
                    unit_price = safe_float_conversion(request.form.get('unit_price'), 0.0)
                    position_number = request.form.get('position_number', type=int)
                    
                    if description and quantity > 0 and unit_price >= 0:
                        item.description = description
                        item.quantity = quantity
                        item.unit_price = unit_price
                        item.total_price = quantity * unit_price
                        item.position_number = position_number
                        
                        db.session.commit()
                        quote.update_total()
                        flash('Position wurde erfolgreich aktualisiert!', 'success')
                    else:
                        flash('Bitte füllen Sie alle Pflichtfelder korrekt aus!', 'danger')
                        
                elif 'detailed_edit' in request.form:
                    # Detaillierte Position bearbeiten
                    description = request.form.get('description', '').strip()
                    position_number = request.form.get('position_number', type=int)
                    
                    # Alte Unterpositionen löschen
                    for sub_item in item.sub_items:
                        db.session.delete(sub_item)
                    
                    # Neue Unterpositionen verarbeiten
                    sub_items_data = process_sub_items(request.form)
                    total_price = sum(sub_data['price'] for sub_data in sub_items_data)
                    
                    # Hauptposition aktualisieren
                    item.description = description
                    item.position_number = position_number
                    item.quantity = 1
                    item.unit_price = total_price
                    item.total_price = total_price
                    
                    # Neue Unterpositionen erstellen
                    create_sub_items(item.id, position_number, sub_items_data)
                    
                    db.session.commit()
                    quote.update_total()
                    flash('Detaillierte Position wurde erfolgreich aktualisiert!', 'success')
                
                elif 'work_position_edit' in request.form:
                    # Arbeitsposition bearbeiten
                    description = request.form.get('description', '').strip()
                    position_number = request.form.get('position_number', type=int)
                    
                    if not description or not position_number:
                        flash('Bitte füllen Sie Beschreibung und Positionsnummer ein!', 'error')
                        return redirect(url_for('edit_quote_item', id=id, item_id=item_id))
                    
                    # Arbeitsschritte aus dem Formular lesen
                    work_step_categories = request.form.getlist('work_step_categories[]')
                    work_step_names = request.form.getlist('work_step_names[]')
                    work_step_hours = request.form.getlist('work_step_hours[]')
                    work_step_rates = request.form.getlist('work_step_rates[]')
                    
                    # Alte Unterpositionen löschen
                    for sub_item in item.sub_items:
                        db.session.delete(sub_item)
                    
                    total_price = 0
                    
                    # Berechne Gesamtpreis aus allen Arbeitsschritten
                    for i in range(len(work_step_categories)):
                        hours = float(work_step_hours[i]) if i < len(work_step_hours) else 0
                        rate = float(work_step_rates[i]) if i < len(work_step_rates) else get_default_hourly_rate()
                        total_price += hours * rate
                    
                    # Erstelle neue Unterpositionen für jeden Arbeitsschritt
                    for i in range(len(work_step_categories)):
                        category = work_step_categories[i]
                        step_name = work_step_names[i]
                        hours = float(work_step_hours[i]) if i < len(work_step_hours) else 0
                        rate = float(work_step_rates[i]) if i < len(work_step_rates) else get_default_hourly_rate()
                        step_price = hours * rate
                        
                        sub_item = QuoteSubItem(
                            quote_item_id=item.id,
                            description=f"{category}: {step_name}",
                            sub_number=i + 1,
                            item_type='arbeitsvorgang',
                            hours=hours,
                            hourly_rate=rate,
                            price=step_price
                        )
                        db.session.add(sub_item)
                    
                    # Aktualisiere Hauptposition
                    item.description = description
                    item.position_number = position_number
                    item.quantity = 1
                    item.unit_price = total_price
                    item.total_price = total_price
                    item.item_type = 'arbeitsposition'
                    
                    db.session.commit()
                    quote.update_total()
                    flash('Arbeitsposition wurde erfolgreich aktualisiert!', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Aktualisieren der Position: {str(e)}', 'error')
            
            return redirect(url_for('edit_quote', id=id))
        
        # GET Request - Bearbeitungsformular anzeigen
        suppliers = Supplier.query.all()
        work_steps = get_work_steps()
        return render_template('quote_item_edit.html', quote=quote, item=item, suppliers=suppliers, work_steps=work_steps)

    # Bestellungen bestätigen
    @app.route('/quote/<int:quote_id>/confirm_orders', methods=['POST'])
    def confirm_supplier_orders(quote_id):
        quote = Quote.query.get_or_404(quote_id)
        
        try:
            # Sammle alle Bestellteile pro Lieferant
            from utils import collect_supplier_orders
            from models import SupplierOrder, SupplierOrderItem
            supplier_orders = collect_supplier_orders(quote)
            
            # Automatische Zuordnung zum Auftrag falls vorhanden
            order_id = None
            if quote.order:
                order_id = quote.order.id
            
            # Erstelle SupplierOrder-Einträge
            for supplier_name, order_items in supplier_orders.items():
                if order_items:
                    # Prüfe ob bereits eine Bestellung für diesen Lieferant und Quote existiert
                    existing_order = SupplierOrder.query.filter_by(
                        quote_id=quote.id, 
                        supplier_name=supplier_name
                    ).first()
                    
                    if not existing_order:
                        supplier_order = SupplierOrder(
                            quote_id=quote.id,
                            order_id=order_id,  # Automatische Zuordnung zum Auftrag
                            supplier_name=supplier_name,
                            status='Bestellt'
                        )
                        db.session.add(supplier_order)
                        db.session.flush()  # Um ID zu bekommen
                        
                        # Erstelle die Bestellpositionen für neue Bestellung
                        for item in order_items:
                            order_item = SupplierOrderItem(
                                supplier_order_id=supplier_order.id,
                                sub_number=item['sub_number'],
                                description=item['description'],
                                part_number=item['part_number'],
                                quantity=item['quantity'],
                                quote_sub_item_id=item.get('quote_sub_item_id')
                            )
                            db.session.add(order_item)
                    else:
                        # Aktualisiere bestehende Bestellung mit order_id falls noch nicht gesetzt
                        if order_id and not existing_order.order_id:
                            existing_order.order_id = order_id
            
            db.session.commit()
            flash('Alle Bestellungen wurden erfolgreich erfasst!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erfassen der Bestellungen: {str(e)}', 'error')
        
        return redirect(url_for('supplier_orders'))
    
    # Bestellübersicht
    @app.route('/supplier_orders')
    def supplier_orders():
        from models import SupplierOrder, Order
        from flask import request
        from sqlalchemy.orm import joinedload
        
        # Filter nach Auftrag-ID wenn angegeben
        order_id = request.args.get('order_id', type=int)
        filter_order = None
        
        if order_id:
            filter_order = Order.query.get(order_id)
            orders = SupplierOrder.query.options(joinedload(SupplierOrder.items)).filter_by(order_id=order_id).order_by(SupplierOrder.order_date.desc()).all()
        else:
            orders = SupplierOrder.query.options(joinedload(SupplierOrder.items)).order_by(SupplierOrder.order_date.desc()).all()
        
        return render_template('supplier_orders.html', orders=orders, filter_order=filter_order)
    
    # Einzelne Bestellung bearbeiten
    @app.route('/supplier_order/<int:order_id>/edit', methods=['GET', 'POST'])
    def edit_supplier_order(order_id):
        from models import SupplierOrder
        from forms import SupplierOrderUpdateForm
        
        order = SupplierOrder.query.get_or_404(order_id)
        form = SupplierOrderUpdateForm(obj=order)
        
        if form.validate_on_submit():
            try:
                form.populate_obj(order)
                db.session.commit()
                flash('Bestellung wurde erfolgreich aktualisiert!', 'success')
                return redirect(url_for('supplier_orders'))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
        
        return render_template('supplier_order_edit.html', order=order, form=form)
    
    # Aufträge
    @app.route('/orders')
    def orders():
        from models import Order
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template('orders.html', orders=orders)
    
    @app.route('/quote/<int:quote_id>/create_order', methods=['GET', 'POST'])
    def create_order(quote_id):
        quote = Quote.query.get_or_404(quote_id)
        from forms import OrderForm
        from models import Order
        from utils import generate_order_number
        
        # Prüfe ob bereits ein Auftrag existiert
        if quote.order:
            flash('Für dieses Angebot existiert bereits ein Auftrag!', 'warning')
            return redirect(url_for('edit_order', order_id=quote.order.id))
        
        form = OrderForm()
        
        if form.validate_on_submit():
            try:
                order_number = generate_order_number()
                
                order = Order(
                    order_number=order_number,
                    quote_id=quote.id,
                    start_date=form.start_date.data,
                    end_date=form.end_date.data,
                    project_manager=form.project_manager.data,
                    notes=form.notes.data,
                    status='Geplant'
                )
                
                db.session.add(order)
                db.session.flush()  # Um ID zu bekommen
                
                # Verknüpfe bestehende Lieferantenbestellungen mit dem Auftrag
                for supplier_order in quote.supplier_orders:
                    supplier_order.order_id = order.id
                
                db.session.commit()
                
                flash(f'Auftrag {order_number} wurde erfolgreich erstellt!', 'success')
                return redirect(url_for('edit_order', order_id=order.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Erstellen des Auftrags: {str(e)}', 'error')
        
        return render_template('order_form.html', quote=quote, form=form)
    
    @app.route('/order/<int:order_id>')
    def view_order(order_id):
        from models import Order
        order = Order.query.get_or_404(order_id)
        return render_template('order_view.html', order=order)
    
    @app.route('/order/<int:order_id>/edit', methods=['GET', 'POST'])
    def edit_order(order_id):
        from models import Order
        from forms import OrderUpdateForm
        
        order = Order.query.get_or_404(order_id)
        
        # Prüfe ob Auftrag storniert ist - dann nicht bearbeitbar
        if order.status == 'Storniert':
            flash('Stornierte Aufträge können nicht bearbeitet werden!', 'warning')
            return redirect(url_for('view_order', order_id=order.id))
        
        form = OrderUpdateForm(obj=order)
        
        if form.validate_on_submit():
            try:
                # Spezielle Behandlung für Status-Wechsel zu "Storniert"
                if form.status.data == 'Storniert':
                    # Statt direkt zu stornieren, zeige Warnung an
                    flash('Zum Stornieren des Auftrags verwenden Sie bitte den entsprechenden Button in der Auftragsansicht.', 'warning')
                    return redirect(url_for('view_order', order_id=order.id))
                
                form.populate_obj(order)
                db.session.commit()
                flash('Auftrag wurde erfolgreich aktualisiert!', 'success')
                return redirect(url_for('view_order', order_id=order.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
        
        return render_template('order_edit.html', order=order, form=form)
    
    @app.route('/order/<int:order_id>/cancel', methods=['POST'])
    def cancel_order(order_id):
        """Storniert einen Auftrag und setzt das Angebot zurück"""
        from models import Order, Quote
        
        order = Order.query.get_or_404(order_id)
        quote = order.quote
        
        try:
            # Auftragsstatus auf "Storniert" setzen
            order.status = 'Storniert'
            
            # Angebotsstatus auf "Angenommen, Auftrag storniert" setzen
            quote.status = 'Angenommen, Auftrag storniert'
            
            db.session.commit()
            
            flash('Auftrag wurde erfolgreich storniert. Das Angebot kann nun erneut angenommen werden.', 'success')
            return redirect(url_for('view_order', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Stornieren des Auftrags: {str(e)}', 'error')
            return redirect(url_for('view_order', order_id=order.id))
    
    # Admin-Route zum Reparieren der Order-Tabelle
    @app.route('/admin/repair_order_table')
    def repair_order_table():
        """Repariert die Order-Tabelle und fügt fehlende Spalten hinzu"""
        try:
            # Backup der Datenbank erstellen
            import shutil
            from datetime import datetime
            import sqlite3
            
            db_path = 'instance/installation_business.db'
            backup_path = f'instance/installation_business_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                flash(f'Backup erstellt: {backup_path}', 'info')
            
            # Verwende direkte SQLite-Verbindung
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Prüfe ob order-Tabelle existiert
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
                result = cursor.fetchone()
                
                if not result:
                    # Erstelle Order-Tabelle
                    cursor.execute('''
                        CREATE TABLE "order" (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_number VARCHAR(50) NOT NULL UNIQUE,
                            quote_id INTEGER NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(20) DEFAULT 'Geplant',
                            start_date DATE NOT NULL,
                            end_date DATE NOT NULL,
                            notes TEXT,
                            project_manager VARCHAR(100),
                            FOREIGN KEY (quote_id) REFERENCES quote (id)
                        )
                    ''')
                    flash('Order-Tabelle wurde erstellt!', 'success')
                else:
                    # Prüfe vorhandene Spalten
                    cursor.execute("PRAGMA table_info('order')")
                    columns_result = cursor.fetchall()
                    existing_columns = [row[1] for row in columns_result]
                    
                    # Füge fehlende Spalten hinzu
                    if 'created_at' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                        cursor.execute("UPDATE 'order' SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                        flash('created_at Spalte hinzugefügt!', 'success')
                    
                    if 'status' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN status VARCHAR(20) DEFAULT 'Geplant'")
                        flash('status Spalte hinzugefügt!', 'success')
                    
                    if 'start_date' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN start_date DATE")
                        cursor.execute("UPDATE 'order' SET start_date = date('now') WHERE start_date IS NULL")
                        flash('start_date Spalte hinzugefügt!', 'success')
                    
                    if 'end_date' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN end_date DATE")
                        cursor.execute("UPDATE 'order' SET end_date = date('now', '+7 days') WHERE end_date IS NULL")
                        flash('end_date Spalte hinzugefügt!', 'success')
                    
                    if 'notes' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN notes TEXT")
                        flash('notes Spalte hinzugefügt!', 'success')
                    
                    if 'project_manager' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN project_manager VARCHAR(100)")
                        flash('project_manager Spalte hinzugefügt!', 'success')
                    
                    if 'order_number' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN order_number VARCHAR(50)")
                        # Generiere Auftragsnummern für bestehende Aufträge
                        cursor.execute("SELECT id FROM 'order' WHERE order_number IS NULL")
                        rows = cursor.fetchall()
                        for i, row in enumerate(rows, 1):
                            order_number = f"AUF-2025-{i:03d}"
                            cursor.execute("UPDATE 'order' SET order_number = ? WHERE id = ?", (order_number, row[0]))
                        flash('order_number Spalte hinzugefügt!', 'success')
                    
                    if 'quote_id' not in existing_columns:
                        cursor.execute("ALTER TABLE 'order' ADD COLUMN quote_id INTEGER")
                        flash('quote_id Spalte hinzugefügt!', 'success')
                
                # Erstelle auch andere fehlende Tabellen
                # SupplierOrder
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplier_order'")
                result = cursor.fetchone()
                
                if not result:
                    cursor.execute('''
                        CREATE TABLE supplier_order (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            quote_id INTEGER NOT NULL,
                            order_id INTEGER,
                            supplier_name VARCHAR(200) NOT NULL,
                            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(20) DEFAULT 'Bestellt',
                            confirmation_date DATETIME,
                            delivery_date DATE,
                            notes TEXT,
                            FOREIGN KEY (quote_id) REFERENCES quote (id),
                            FOREIGN KEY (order_id) REFERENCES "order" (id)
                        )
                    ''')
                    flash('SupplierOrder-Tabelle wurde erstellt!', 'success')
                else:
                    # Prüfe und füge fehlende Spalten zu supplier_order hinzu
                    cursor.execute("PRAGMA table_info(supplier_order)")
                    so_columns_result = cursor.fetchall()
                    so_existing_columns = [row[1] for row in so_columns_result]
                    
                    if 'order_id' not in so_existing_columns:
                        cursor.execute("ALTER TABLE supplier_order ADD COLUMN order_id INTEGER")
                        flash('order_id Spalte zu SupplierOrder hinzugefügt!', 'success')
                    
                    if 'order_date' not in so_existing_columns:
                        cursor.execute("ALTER TABLE supplier_order ADD COLUMN order_date DATETIME DEFAULT CURRENT_TIMESTAMP")
                        cursor.execute("UPDATE supplier_order SET order_date = CURRENT_TIMESTAMP WHERE order_date IS NULL")
                        flash('order_date Spalte zu SupplierOrder hinzugefügt!', 'success')
                    
                    if 'status' not in so_existing_columns:
                        cursor.execute("ALTER TABLE supplier_order ADD COLUMN status VARCHAR(20) DEFAULT 'Bestellt'")
                        flash('status Spalte zu SupplierOrder hinzugefügt!', 'success')
                    
                    if 'confirmation_date' not in so_existing_columns:
                        cursor.execute("ALTER TABLE supplier_order ADD COLUMN confirmation_date DATETIME")
                        flash('confirmation_date Spalte zu SupplierOrder hinzugefügt!', 'success')
                    
                    if 'delivery_date' not in so_existing_columns:
                        cursor.execute("ALTER TABLE supplier_order ADD COLUMN delivery_date DATE")
                        flash('delivery_date Spalte zu SupplierOrder hinzugefügt!', 'success')
                    
                    if 'notes' not in so_existing_columns:
                        cursor.execute("ALTER TABLE supplier_order ADD COLUMN notes TEXT")
                        flash('notes Spalte zu SupplierOrder hinzugefügt!', 'success')
                
                # SupplierOrderItem
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplier_order_item'")
                result = cursor.fetchone()
                
                if not result:
                    cursor.execute('''
                        CREATE TABLE supplier_order_item (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            supplier_order_id INTEGER NOT NULL,
                            sub_number VARCHAR(10) NOT NULL,
                            description TEXT NOT NULL,
                            part_number VARCHAR(100),
                            quantity VARCHAR(50) DEFAULT '1',
                            quote_sub_item_id INTEGER,
                            FOREIGN KEY (supplier_order_id) REFERENCES supplier_order (id),
                            FOREIGN KEY (quote_sub_item_id) REFERENCES quote_sub_item (id)
                        )
                    ''')
                    flash('SupplierOrderItem-Tabelle wurde erstellt!', 'success')
                
                # QuoteRejection
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quote_rejection'")
                result = cursor.fetchone()
                
                if not result:
                    cursor.execute('''
                        CREATE TABLE quote_rejection (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            quote_id INTEGER NOT NULL,
                            rejection_reason TEXT NOT NULL,
                            rejected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (quote_id) REFERENCES quote (id)
                        )
                    ''')
                    flash('QuoteRejection-Tabelle wurde erstellt!', 'success')
                
                # Quote status spalte
                cursor.execute("PRAGMA table_info(quote)")
                quote_columns_result = cursor.fetchall()
                quote_existing_columns = [row[1] for row in quote_columns_result]
                
                if 'status' not in quote_existing_columns:
                    cursor.execute("ALTER TABLE quote ADD COLUMN status VARCHAR(20) DEFAULT 'Entwurf'")
                    flash('status Spalte zu Quote hinzugefügt!', 'success')
                
                conn.commit()
                flash('Datenbank-Reparatur erfolgreich abgeschlossen!', 'success')
                
            finally:
                conn.close()
            
        except Exception as e:
            flash(f'Fehler bei der Reparatur: {str(e)}', 'error')
        
        return redirect(url_for('index'))

    # Admin-Route zur Verknüpfung von Lieferantenbestellungen mit Aufträgen
    @app.route('/admin/link_supplier_orders')
    def link_supplier_orders():
        """Verknüpft alle Lieferantenbestellungen mit ihren entsprechenden Aufträgen"""
        try:
            from models import Quote, Order, SupplierOrder
            
            # Hole alle Angebote mit Aufträgen
            quotes_with_orders = Quote.query.join(Order).all()
            
            updated_count = 0
            
            for quote in quotes_with_orders:
                # Hole alle Lieferantenbestellungen für dieses Angebot
                supplier_orders = SupplierOrder.query.filter_by(quote_id=quote.id).all()
                
                for supplier_order in supplier_orders:
                    if supplier_order.order_id is None:
                        # Verknüpfe mit dem Auftrag
                        supplier_order.order_id = quote.order.id
                        updated_count += 1
            
            if updated_count > 0:
                db.session.commit()
                flash(f'{updated_count} Lieferantenbestellungen wurden erfolgreich mit Aufträgen verknüpft!', 'success')
            else:
                flash('Alle Lieferantenbestellungen sind bereits korrekt verknüpft.', 'info')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Verknüpfen: {str(e)}', 'error')
            
        return redirect(url_for('index'))

    # Arbeitsanweisungen
    @app.route('/order/<int:order_id>/work_instruction/create')
    def create_work_instruction(order_id):
        """Erstellt eine neue Arbeitsanweisung für einen Auftrag"""
        from models import Order, WorkInstruction
        from datetime import datetime
        
        order = Order.query.get_or_404(order_id)
        
        # Prüfe ob bereits eine Arbeitsanweisung existiert
        if order.work_instruction:
            flash('Für diesen Auftrag existiert bereits eine Arbeitsanweisung!', 'warning')
            return redirect(url_for('view_order', order_id=order.id))
        
        # Prüfe ob Order eine Quote hat
        if not order.quote:
            flash('Fehler: Auftrag hat kein verknüpftes Angebot!', 'error')
            return redirect(url_for('view_order', order_id=order.id))
        
        try:
            # Bestimme Installationsort
            installation_location = "Kunde vor Ort"
            if order.quote.customer and order.quote.customer.city:
                installation_location = order.quote.customer.city
            
            # Bestimme Projektbeschreibung
            work_description = "Montage und Installation"
            if order.quote.project_description:
                work_description = f"Montage und Installation für Projekt: {order.quote.project_description}"
            
            # Neue Arbeitsanweisung erstellen
            work_instruction = WorkInstruction(
                order_id=order.id,
                created_by='System',  # Hier könnte später ein Benutzer-System integriert werden
                status='Erstellt',
                priority='Normal',
                # Automatische Vorschläge basierend auf dem Auftrag
                work_description=work_description,
                installation_location=installation_location
            )
            
            # Eindeutige Nummer generieren
            work_instruction.instruction_number = work_instruction.generate_instruction_number()
            
            db.session.add(work_instruction)
            db.session.commit()
            
            flash(f'Arbeitsanweisung {work_instruction.instruction_number} wurde erstellt!', 'success')
            return redirect(url_for('view_work_instruction', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Erstellen der Arbeitsanweisung: {str(e)}', 'error')
            return redirect(url_for('view_order', order_id=order.id))
    
    @app.route('/order/<int:order_id>/work_instruction')
    def view_work_instruction(order_id):
        """Zeigt die Arbeitsanweisung für einen Auftrag an"""
        from models import Order
        
        order = Order.query.get_or_404(order_id)
        
        if not order.work_instruction:
            flash('Für diesen Auftrag existiert noch keine Arbeitsanweisung!', 'warning')
            return redirect(url_for('view_order', order_id=order.id))
        
        return render_template('work_instruction_view.html', order=order, 
                             work_instruction=order.work_instruction)
    
    @app.route('/order/<int:order_id>/work_instruction/pdf')
    def export_work_instruction_pdf(order_id):
        """Exportiert die Arbeitsanweisung als PDF"""
        from models import Order
        from pdf_export import PDFExporter
        from flask import make_response
        
        order = Order.query.get_or_404(order_id)
        
        if not order.work_instruction:
            flash('Für diesen Auftrag existiert noch keine Arbeitsanweisung!', 'warning')
            return redirect(url_for('view_order', order_id=order.id))
        
        try:
            exporter = PDFExporter()
            pdf_buffer = exporter.export_work_instruction(order_id)
            
            # PDF als Download senden
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=Arbeitsanweisung_{order.order_number}.pdf'
            
            return response
            
        except Exception as e:
            flash(f'Fehler beim PDF-Export: {str(e)}', 'error')
            return redirect(url_for('view_order', order_id=order.id))
    
    @app.route('/order/<int:order_id>/work_instruction/edit', methods=['GET', 'POST'])
    def edit_work_instruction(order_id):
        """Bearbeitet eine Arbeitsanweisung"""
        from models import Order
        from flask import request
        import uuid
        
        order = Order.query.get_or_404(order_id)
        work_instruction = order.work_instruction
        
        if not work_instruction:
            flash('Für diesen Auftrag existiert noch keine Arbeitsanweisung!', 'warning')
            return redirect(url_for('view_order', order_id=order.id))
        
        if request.method == 'POST':
            try:
                # Aktualisiere die Arbeitsanweisung mit den neuen Daten
                work_instruction.status = request.form.get('status', work_instruction.status)
                work_instruction.priority = request.form.get('priority', work_instruction.priority)
                work_instruction.work_description = request.form.get('work_description', '')
                work_instruction.special_instructions = request.form.get('special_instructions', '')
                work_instruction.safety_notes = request.form.get('safety_notes', '')
                work_instruction.tools_required = request.form.get('tools_required', '')
                work_instruction.estimated_duration = int(request.form.get('estimated_duration', 0)) if request.form.get('estimated_duration') else None
                work_instruction.installation_location = request.form.get('installation_location', '')
                work_instruction.access_requirements = request.form.get('access_requirements', '')
                work_instruction.preparation_work = request.form.get('preparation_work', '')
                work_instruction.notes = request.form.get('notes', '')
                
                # Handle file uploads
                upload_folder = app.config['UPLOAD_FOLDER']
                
                # Handle photo uploads
                photo_files = request.files.getlist('photos')
                if photo_files and any(f.filename for f in photo_files):
                    photo_paths = []
                    
                    # Keep existing photos
                    if work_instruction.photo_paths:
                        try:
                            existing_photos = json.loads(work_instruction.photo_paths)
                            photo_paths.extend(existing_photos)
                        except:
                            pass
                    
                    for photo in photo_files:
                        if photo and photo.filename and allowed_file(photo.filename):
                            # Generate unique filename
                            filename = secure_filename(photo.filename)
                            unique_filename = f"{uuid.uuid4()}_{filename}"
                            file_path = os.path.join(upload_folder, unique_filename)
                            
                            try:
                                photo.save(file_path)
                                photo_paths.append(unique_filename)
                                print(f"Saved photo: {unique_filename}")  # Debug
                            except Exception as e:
                                print(f"Error saving photo {filename}: {str(e)}")  # Debug
                                flash(f'Fehler beim Speichern von {filename}: {str(e)}', 'warning')
                    
                    work_instruction.photo_paths = json.dumps(photo_paths) if photo_paths else work_instruction.photo_paths
                    work_instruction.has_photos = bool(photo_paths)
                    print(f"Final photo_paths: {work_instruction.photo_paths}")  # Debug
                
                # Handle plan upload
                plan_file = request.files.get('plan')
                if plan_file and plan_file.filename and allowed_file(plan_file.filename):
                    # Remove existing plan if it exists
                    if work_instruction.plan_path:
                        old_plan_path = os.path.join(upload_folder, work_instruction.plan_path.split('/')[-1])
                        if os.path.exists(old_plan_path):
                            try:
                                os.remove(old_plan_path)
                                print(f"Removed old plan: {old_plan_path}")  # Debug
                            except:
                                pass
                    
                    # Save new plan
                    filename = secure_filename(plan_file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(upload_folder, unique_filename)
                    
                    try:
                        plan_file.save(file_path)
                        work_instruction.plan_path = unique_filename
                        work_instruction.has_3d_plan = True
                        print(f"Saved plan: {unique_filename}")  # Debug
                    except Exception as e:
                        print(f"Error saving plan: {str(e)}")  # Debug
                        flash(f'Fehler beim Speichern des Plans: {str(e)}', 'warning')
                
                # Handle deletions
                delete_photos = request.form.getlist('delete_photos[]')
                if delete_photos and work_instruction.photo_paths:
                    try:
                        current_photos = json.loads(work_instruction.photo_paths)
                        for delete_photo in delete_photos:
                            if delete_photo in current_photos:
                                # Remove from list
                                current_photos.remove(delete_photo)
                                # Delete file
                                file_path = os.path.join(upload_folder, delete_photo.split('/')[-1])
                                if os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass
                        
                        work_instruction.photo_paths = json.dumps(current_photos) if current_photos else None
                        work_instruction.has_photos = bool(current_photos)
                    except:
                        pass
                
                if request.form.get('delete_plan') == 'true':
                    if work_instruction.plan_path:
                        # Delete file
                        file_path = os.path.join(upload_folder, work_instruction.plan_path.split('/')[-1])
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        
                        work_instruction.plan_path = None
                        work_instruction.has_3d_plan = False
                
                # Debug: Log what we're about to save
                print(f"Before commit - photo_paths: {work_instruction.photo_paths}")
                print(f"Before commit - plan_path: {work_instruction.plan_path}")
                print(f"Before commit - has_photos: {work_instruction.has_photos}")
                print(f"Before commit - has_3d_plan: {work_instruction.has_3d_plan}")
                
                db.session.commit()
                flash('Arbeitsanweisung wurde erfolgreich aktualisiert!', 'success')
                return redirect(url_for('view_work_instruction', order_id=order.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Aktualisieren der Arbeitsanweisung: {str(e)}', 'error')
        
        return render_template('work_instruction_edit.html', order=order, work_instruction=work_instruction)

    # API-Routen für Autocomplete
    @app.route('/api/customers/search')
    def api_customer_search():
        """API für Kunden-Autocomplete"""
        from flask import jsonify
        
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        # Suche Kunden die dem Query entsprechen
        customers = Customer.query.filter(
            db.or_(
                Customer.first_name.ilike(f'%{query}%'),
                Customer.last_name.ilike(f'%{query}%'),
                db.func.concat(Customer.first_name, ' ', Customer.last_name).ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        results = []
        for customer in customers:
            results.append({
                'id': customer.id,
                'name': customer.full_name,
                'email': customer.email or '',
                'city': customer.city or ''
            })
        
        return jsonify(results)

def process_sub_items(form_data):
    """Verarbeitet Unterpositionen aus Formulardaten"""
    sub_descriptions = form_data.getlist('sub_description[]')
    sub_item_types = form_data.getlist('sub_item_type[]')
    sub_requires_orders = form_data.getlist('sub_requires_order[]')
    sub_suppliers = form_data.getlist('sub_supplier[]')
    sub_part_numbers = form_data.getlist('sub_part_number[]')
    sub_part_quantities = form_data.getlist('sub_part_quantity[]')
    sub_part_prices = form_data.getlist('sub_part_price[]')
    sub_hours = form_data.getlist('sub_hours[]')
    sub_hourly_rates = form_data.getlist('sub_hourly_rate[]')
    sub_quantities = form_data.getlist('sub_quantity[]')
    sub_unit_prices = form_data.getlist('sub_unit_price[]')
    
    sub_items_data = []
    
    for i, sub_desc in enumerate(sub_descriptions):
        if not sub_desc.strip():
            continue
            
        item_type = sub_item_types[i] if i < len(sub_item_types) else 'bestellteil'
        
        if item_type == 'arbeitsvorgang':
            hours = safe_float_conversion(sub_hours[i] if i < len(sub_hours) else 0)
            hourly_rate = safe_float_conversion(
                sub_hourly_rates[i] if i < len(sub_hourly_rates) else get_default_hourly_rate()
            )
            sub_price = hours * hourly_rate
            
            sub_items_data.append({
                'description': sub_desc,
                'item_type': 'arbeitsvorgang',
                'hours': hours,
                'hourly_rate': hourly_rate,
                'price': sub_price,
                'requires_order': False,
                'supplier': '',
                'part_number': '',
                'part_quantity': '1',
                'part_price': 0.0,
                'quantity': '',
                'unit_price': 0.0
            })
            
        elif item_type == 'sonstiges':
            quantity_text = sub_quantities[i] if i < len(sub_quantities) else ''
            unit_price = safe_float_conversion(sub_unit_prices[i] if i < len(sub_unit_prices) else 0)
            quantity_num = parse_quantity_from_text(quantity_text)
            sub_price = quantity_num * unit_price
            
            sub_items_data.append({
                'description': sub_desc,
                'item_type': 'sonstiges',
                'quantity': quantity_text,
                'unit_price': unit_price,
                'price': sub_price,
                'requires_order': False,
                'supplier': '',
                'part_number': '',
                'part_quantity': '1',
                'part_price': 0.0,
                'hours': 0.0,
                'hourly_rate': 0.0
            })
            
        else:  # bestellteil
            requires_order = str(i+1) in sub_requires_orders
            supplier = sub_suppliers[i] if i < len(sub_suppliers) else ''
            part_number = sub_part_numbers[i] if i < len(sub_part_numbers) else ''
            part_quantity = sub_part_quantities[i] if i < len(sub_part_quantities) else '1'
            part_price = safe_float_conversion(sub_part_prices[i] if i < len(sub_part_prices) else 0)
            
            sub_items_data.append({
                'description': sub_desc,
                'item_type': 'bestellteil',
                'requires_order': requires_order,
                'supplier': supplier,
                'part_number': part_number,
                'part_quantity': part_quantity,
                'part_price': part_price,
                'price': part_price,
                'hours': 0.0,
                'hourly_rate': 0.0,
                'quantity': '',
                'unit_price': 0.0
            })
    
    return sub_items_data

def create_sub_items(quote_item_id, position_number, sub_items_data):
    """Erstellt Unterpositionen in der Datenbank"""
    for i, sub_data in enumerate(sub_items_data, 1):
        sub_item = QuoteSubItem(
            quote_item_id=quote_item_id,
            sub_number=f"{position_number}.{i}",
            description=sub_data['description'],
            item_type=sub_data['item_type'],
            requires_order=sub_data['requires_order'],
            supplier=sub_data['supplier'],
            part_number=sub_data['part_number'],
            part_quantity=sub_data['part_quantity'],
            part_price=sub_data['part_price'],
            hours=sub_data['hours'],
            hourly_rate=sub_data['hourly_rate'],
            quantity=sub_data['quantity'],
            unit_price=sub_data['unit_price'],
            price=sub_data['price']
        )
        db.session.add(sub_item)

def update_quote_status(quote_id, new_status):
    """Aktualisiert den Status eines Angebots"""
    quote = Quote.query.get_or_404(quote_id)
    
    # Prüfe ob Angebot angenommen wurde - dann kann Status nicht mehr geändert werden
    if quote.status == 'Angenommen' and new_status != 'Angenommen':
        flash('Angenommene Angebote können nicht mehr geändert werden!', 'warning')
        return redirect(url_for('view_quote', id=quote_id))
    
    try:
        quote.status = new_status
        db.session.commit()
        flash(f'Angebot {quote.quote_number} wurde als "{new_status}" markiert!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler beim Aktualisieren des Status: {str(e)}', 'error')
    
    return redirect(url_for('edit_quote', id=quote_id))

# App erstellen und starten
app = create_app()

if __name__ == '__main__':
    # Cloud-Hosting-Erkennung
    is_production = bool(os.environ.get('DATABASE_URL'))
    
    if is_production:
        # Produktion: Einfacher Start ohne Browser-Öffnung
        with app.app_context():
            db.create_all()
        
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    
    else:
        # Entwicklung: Wie bisher mit Browser-Öffnung
        import webbrowser
        import threading
        import time
        
        def open_browser():
            """Öffnet automatisch den Browser nach kurzer Verzögerung"""
            time.sleep(2)  # Warten bis Server vollständig gestartet ist
            webbrowser.open('http://localhost:5000')
        
        print("\n" + "="*60)
        print("🏢 INSTALLATIONS BUSINESS APP")
        print("="*60)
        print("📋 Initialisiere Anwendung...")
        
        with app.app_context():
            # Datenbank erstellen falls nicht vorhanden
            db.create_all()
            print("✓ Datenbank initialisiert")
            
            # Lade Excel-Templates beim Start
            try:
                if load_position_templates():
                    print("✓ Positionsvorlagen erfolgreich geladen")
                else:
                    print("⚠ Positionsvorlagen konnten nicht geladen werden")
            except Exception as e:
                print("⚠ Positionsvorlagen nicht gefunden (normal bei Erstinstallation)")
            
            try:
                if load_suppliers():
                    print("✓ Lieferanten erfolgreich geladen")
                else:
                    print("⚠ Lieferanten konnten nicht geladen werden")
            except Exception as e:
                print("⚠ Lieferanten nicht gefunden (normal bei Erstinstallation)")
        
        print("🚀 Starte Webserver...")
        print("🌐 Die App öffnet sich automatisch in Ihrem Browser")
        print("\nFalls der Browser nicht automatisch öffnet:")
        print("👉 Gehen Sie zu: http://localhost:5000")
        print("\n⚠️  WICHTIG: Lassen Sie dieses Fenster geöffnet!")
        print("   Zum Beenden der App drücken Sie Strg+C")
        print("="*60)
        
        # Browser automatisch öffnen
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Server starten
        try:
            app.run(
                host='127.0.0.1',  # Nur lokaler Zugriff für Sicherheit
                port=5000,
                debug=False,  # Debug aus für Endbenutzer
                use_reloader=False  # Reloader aus für Stabilität
            )
        except KeyboardInterrupt:
            print("\n\n💤 App wurde beendet. Auf Wiedersehen!")
        except Exception as e:
            print(f"\n❌ Fehler beim Starten der App: {e}")
            print("\nMögliche Lösungen:")
            print("- Port 5000 könnte bereits belegt sein")
            print("- Starten Sie die App als Administrator")
            print("- Prüfen Sie die Firewall-Einstellungen")
            input("\nDrücken Sie Enter zum Beenden...")
