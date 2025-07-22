"""
Optimierte Version der InstallationApp mit verbesserter Struktur und Fehlerbehandlung
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from datetime import date, timedelta, datetime
import os
import json
import secrets
from werkzeug.utils import secure_filename

# Lokale Imports
from config import Config
from models import db, Customer, Quote, QuoteItem, QuoteSubItem, Supplier, CompanySettings, QuoteRejection, Order, SupplierOrder, SupplierOrderItem, WorkInstruction, AcquisitionChannel, PositionTemplate, PositionTemplateSubItem, Invoice
from flask_migrate import Migrate
from forms import CustomerForm, QuoteForm, SupplierForm, SettingsForm, QuoteRejectionForm, SupplierOrderUpdateForm, OrderForm, OrderUpdateForm, AcquisitionChannelForm, CustomerWorkflowForm, AppointmentForm
from utils import get_default_hourly_rate, generate_quote_number, load_position_templates, load_suppliers, update_quote_total, safe_float_conversion, parse_quantity_from_text
from pdf_export import PDFExporter
from work_steps import get_work_steps

# Upload-Konfiguration und Hilfsfunktionen
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    """Prüft ob Dateiendung erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_rollback():
    """Führt einen sicheren Rollback nur durch wenn eine aktive Transaktion existiert"""
    try:
        if db.session.is_active:
            db.session.rollback()
    except Exception:
        # Falls auch der Rollback fehlschlägt, Session komplett neu erstellen
        db.session.close()

def safe_float_conversion_strict(value, default=0.0):
    """Sichere Float-Konvertierung mit strikter Validierung für kritische Bereiche"""
    if value is None or value == '':
        return default
    
    try:
        result = float(value)
        # Validiere dass es eine gültige positive Zahl ist (für Stunden/Preise)
        if result < 0:
            return default
        return result
    except (ValueError, TypeError):
        return default

def safe_sqlite_operation(db_path, operation_func, *args, **kwargs):
    """
    Führt SQLite-Operationen mit sicherer Connection-Behandlung durch
    
    Args:
        db_path: Pfad zur SQLite-Datenbank
        operation_func: Funktion die mit (connection, cursor) aufgerufen wird
        *args, **kwargs: Zusätzliche Parameter für operation_func
    
    Returns:
        Ergebnis der operation_func oder None bei Fehler
    """
    import sqlite3
    from contextlib import closing
    
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            with closing(conn.cursor()) as cursor:
                result = operation_func(conn, cursor, *args, **kwargs)
                conn.commit()
                return result
    except Exception as e:
        print(f"SQLite operation failed: {str(e)}")
        raise e

def create_app():
    """App Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Session-Konfiguration für Login-System
    app.secret_key = secrets.token_hex(16)  # Für Produktion: Festen Key verwenden
    
    # Datenbank initialisieren
    db.init_app(app)
    # Flask-Migrate initialisieren
    migrate = Migrate(app, db)
    
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
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Formatiert einen Wert als Währung"""
        if value is None:
            return "0,00 €"
        try:
            return f"{float(value):,.2f} €".replace(",", " ").replace(".", ",").replace(" ", ".")
        except (ValueError, TypeError):
            return "0,00 €"
    
    # Template-Funktionen registrieren
    @app.context_processor
    def inject_global_vars():
        from datetime import date
        return {
            'get_default_hourly_rate': get_default_hourly_rate,
            'today': date.today
        }
    
    # Blueprints registrieren (hier vereinfacht als Routen)
    register_routes(app)
    
    return app

# ===============================
# LOGIN-SYSTEM DECORATOR
# ===============================

def login_required(login_function):
    """Decorator für Routen die Login erfordern"""
    from functools import wraps
    
    @wraps(login_function)
    def login_decorated_function(*args, **kwargs):
        if 'login_admin_id' not in session:
            return redirect(url_for('login'))
        return login_function(*args, **kwargs)
    return login_decorated_function

def register_routes(app):
    # Bestellung per E-Mail senden (nachträglich)
    @app.route('/supplier_order/<int:order_id>/send_email', methods=['POST'])
    @login_required
    def send_supplier_order_email(order_id):
        from models import SupplierOrder, SupplierOrderItem, Quote
        from utils import generate_supplier_order_email, get_supplier_email
        order = SupplierOrder.query.get_or_404(order_id)
        quote = order.quote
        # Sammle Bestellpositionen
        order_items = []
        for item in order.items:
            order_items.append({
                'sub_number': item.sub_number,
                'description': item.description,
                'part_number': item.part_number or '',
                'quantity': item.quantity,
                'quote_sub_item_id': item.quote_sub_item_id
            })
        supplier_email = get_supplier_email(order.supplier_name)
        subject, html_body, plain_body = generate_supplier_order_email(quote, order.supplier_name, order_items, order.order_id)
        # Hier könnte ein echter E-Mail-Versand erfolgen, aktuell nur Anzeige
        # Status auf 'Bestellt' setzen
        order.status = 'Bestellt'
        db.session.commit()
        flash('Die Bestellung wurde als "Bestellt" markiert. E-Mail-Text wird angezeigt.', 'success')
        return render_template('quote_order_emails.html', quote=quote, order=order, email_info=[{
            'supplier': order.supplier_name,
            'email': supplier_email,
            'subject': subject,
            'body': html_body,
            'plain_body': plain_body,
            'items_count': len(order_items)
        }])
    """Registriert alle Routen"""
    
    # Hauptseiten
    @app.route('/')
    @login_required
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
    
    # ===============================
    # USER MANAGEMENT (ADMIN)
    # ===============================
    
    @app.route('/admin/users')
    @login_required
    def manage_users():
        """Benutzer-Verwaltungsseite anzeigen"""
        from models import LoginAdmin
        admins = LoginAdmin.query.all()
        return render_template('admin_users.html', admins=admins)
    
    @app.route('/admin/users/add', methods=['POST'])
    @login_required
    def add_user():
        """Neuen Admin hinzufügen"""
        from models import LoginAdmin
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            # Validierung
            if not username or not password:
                flash('Benutzername und Passwort sind erforderlich!', 'error')
                return redirect(url_for('manage_users'))
            
            if len(password) < 6:
                flash('Passwort muss mindestens 6 Zeichen lang sein!', 'error')
                return redirect(url_for('manage_users'))
            
            # Prüfe ob Benutzername bereits existiert
            existing = LoginAdmin.query.filter_by(login_username=username).first()
            if existing:
                flash('Benutzername bereits vergeben!', 'error')
                return redirect(url_for('manage_users'))
            
            # Erstelle neuen Admin
            new_admin = LoginAdmin.create_login_admin(username, password)
            db.session.add(new_admin)
            db.session.commit()
            
            flash(f'Admin-Benutzer "{username}" wurde erfolgreich erstellt!', 'success')
            
        except Exception as e:
            safe_rollback()
            flash(f'Fehler beim Erstellen des Benutzers: {str(e)}', 'error')
        
        return redirect(url_for('manage_users'))
    
    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    def delete_user(user_id):
        """Admin löschen"""
        from models import LoginAdmin
        try:
            admin = LoginAdmin.query.get_or_404(user_id)
            
            # Verhindere dass sich der aktuelle Benutzer selbst löscht
            if admin.login_id == session.get('login_admin_id'):
                flash('Sie können sich nicht selbst löschen!', 'error')
                return redirect(url_for('manage_users'))
            
            # Verhindere Löschung wenn es der einzige Admin ist
            admin_count = LoginAdmin.query.filter_by(login_is_active=True).count()
            if admin_count <= 1:
                flash('Der letzte Admin kann nicht gelöscht werden!', 'error')
                return redirect(url_for('manage_users'))
            
            username = admin.login_username
            db.session.delete(admin)
            db.session.commit()
            
            flash(f'Admin-Benutzer "{username}" wurde erfolgreich gelöscht!', 'success')
            
        except Exception as e:
            safe_rollback()
            flash(f'Fehler beim Löschen des Benutzers: {str(e)}', 'error')
        
        return redirect(url_for('manage_users'))
    
    @app.route('/admin/users/<int:user_id>/change_password', methods=['POST'])
    @login_required
    def change_password(user_id):
        """Passwort ändern"""
        from models import LoginAdmin
        try:
            admin = LoginAdmin.query.get_or_404(user_id)
            new_password = request.form.get('new_password', '').strip()
            
            # Validierung
            if not new_password:
                flash('Neues Passwort ist erforderlich!', 'error')
                return redirect(url_for('manage_users'))
            
            if len(new_password) < 6:
                flash('Passwort muss mindestens 6 Zeichen lang sein!', 'error')
                return redirect(url_for('manage_users'))
            
            # Passwort setzen
            admin.set_login_password(new_password)
            db.session.commit()
            
            flash(f'Passwort für "{admin.login_username}" wurde erfolgreich geändert!', 'success')
            
        except Exception as e:
            safe_rollback()
            flash(f'Fehler beim Ändern des Passworts: {str(e)}', 'error')
        
        return redirect(url_for('manage_users'))

    # Kunden-Routen
    @app.route('/customers')
    @login_required
    def customers():
        from flask import request
        
        # Filter-Parameter aus URL lesen
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'last_name')
        sort_dir = request.args.get('dir', 'asc')
        
        # Basis-Query aufbauen
        query = Customer.query
        
        # Suchfilter anwenden
        if search_query:
            query = query.filter(
                db.or_(
                    Customer.first_name.ilike(f'%{search_query}%'),
                    Customer.last_name.ilike(f'%{search_query}%'),
                    db.func.concat(Customer.first_name, ' ', Customer.last_name).ilike(f'%{search_query}%'),
                    Customer.email.ilike(f'%{search_query}%'),
                    Customer.city.ilike(f'%{search_query}%')
                )
            )
        
        # Sortierung anwenden
        sort_column = None
        if sort_by == 'first_name':
            sort_column = Customer.first_name
        elif sort_by == 'last_name':
            sort_column = Customer.last_name
        elif sort_by == 'email':
            sort_column = Customer.email
        elif sort_by == 'city':
            sort_column = Customer.city
        elif sort_by == 'created_at':
            sort_column = Customer.id  # Als Ersatz für created_at
        else:
            sort_column = Customer.last_name
        
        if sort_dir == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Sekundäre Sortierung für bessere Konsistenz
        if sort_by != 'last_name':
            query = query.order_by(Customer.last_name.asc())
        
        customers = query.all()
        
        return render_template('customers.html', 
                             customers=customers, 
                             search_query=search_query,
                             sort_by=sort_by,
                             sort_dir=sort_dir)
    
    @app.route('/customer/new', methods=['GET', 'POST'])
    @login_required
    def new_customer():
        form = CustomerForm()
        
        # Akquisekanäle für das SelectField laden
        acquisition_channels = AcquisitionChannel.query.filter_by(is_active=True).all()
        form.acquisition_channel.choices = [(0, 'Nicht ausgewählt')] + [(c.id, c.name) for c in acquisition_channels]
        
        if form.validate_on_submit():
            try:
                customer = Customer(
                    salutation=form.salutation.data if form.salutation.data else None,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    phone=form.phone.data,
                    address=form.address.data,
                    city=form.city.data,
                    postal_code=form.postal_code.data,
                    customer_manager=form.customer_manager.data if form.customer_manager.data else None,
                    acquisition_channel_id=form.acquisition_channel.data if form.acquisition_channel.data != 0 else None,
                    comments=form.comments.data if form.comments.data else None
                )
                db.session.add(customer)
                db.session.commit()
                flash('Kunde wurde erfolgreich hinzugefügt!', 'success')
                return redirect(url_for('customers'))
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('customer_form.html', form=form, title='Neuer Kunde')
    
    @app.route('/customer/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_customer(id):
        customer = Customer.query.get_or_404(id)
        form = CustomerForm(obj=customer)
        
        # Akquisekanäle für das SelectField laden
        acquisition_channels = AcquisitionChannel.query.filter_by(is_active=True).all()
        form.acquisition_channel.choices = [(0, 'Nicht ausgewählt')] + [(c.id, c.name) for c in acquisition_channels]
        
        # Aktuellen Wert setzen
        if customer.acquisition_channel_id:
            form.acquisition_channel.data = customer.acquisition_channel_id
        else:
            form.acquisition_channel.data = 0
        
        if form.validate_on_submit():
            try:
                customer.salutation = form.salutation.data if form.salutation.data else None
                customer.first_name = form.first_name.data
                customer.last_name = form.last_name.data
                customer.email = form.email.data
                customer.phone = form.phone.data
                customer.address = form.address.data
                customer.city = form.city.data
                customer.postal_code = form.postal_code.data
                customer.customer_manager = form.customer_manager.data if form.customer_manager.data else None
                customer.acquisition_channel_id = form.acquisition_channel.data if form.acquisition_channel.data != 0 else None
                customer.comments = form.comments.data if form.comments.data else None
                
                db.session.commit()
                flash('Kunde wurde erfolgreich bearbeitet!', 'success')
                return redirect(url_for('customers'))
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('customer_form.html', form=form, title='Kunde bearbeiten', customer=customer)
    
    @app.route('/customer/<int:id>/delete')
    @login_required
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
            safe_rollback()
            flash(f'Fehler beim Löschen: {str(e)}', 'error')
        
        return redirect(url_for('customers'))

    # Angebots-Routen
    @app.route('/quotes')
    @login_required
    def quotes():
        from flask import request
        from sqlalchemy.orm import joinedload
        
        # Filter-Parameter aus URL lesen
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'created_at')
        sort_dir = request.args.get('dir', 'desc')
        
        # Basis-Query mit JOIN aufbauen
        query = Quote.query.options(joinedload(Quote.customer))
        
        # Suchfilter anwenden
        if search_query:
            query = query.filter(
                db.or_(
                    Quote.quote_number.ilike(f'%{search_query}%'),
                    Quote.project_description.ilike(f'%{search_query}%'),
                    Quote.customer.has(Customer.first_name.ilike(f'%{search_query}%')),
                    Quote.customer.has(Customer.last_name.ilike(f'%{search_query}%')),
                    Quote.customer.has(
                        db.func.concat(Customer.first_name, ' ', Customer.last_name).ilike(f'%{search_query}%')
                    )
                )
            )
        
        # Sortierung anwenden
        sort_column = None
        if sort_by == 'quote_number':
            sort_column = Quote.quote_number
        elif sort_by == 'customer':
            sort_column = Customer.last_name
            query = query.join(Customer)
        elif sort_by == 'project_description':
            sort_column = Quote.project_description
        elif sort_by == 'total_amount':
            sort_column = Quote.total_amount
        elif sort_by == 'status':
            sort_column = Quote.status
        elif sort_by == 'valid_until':
            sort_column = Quote.valid_until
        elif sort_by == 'created_at':
            sort_column = Quote.created_at
        else:
            sort_column = Quote.created_at
        
        if sort_dir == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        quotes = query.all()
        
        return render_template('quotes.html', 
                             quotes=quotes, 
                             search_query=search_query,
                             sort_by=sort_by,
                             sort_dir=sort_dir)
    
    @app.route('/quote/new', methods=['GET', 'POST'])
    @login_required
    def new_quote():
        form = QuoteForm()
        
        # Prüfe ob eine customer_id über URL-Parameter übergeben wurde
        customer_id = request.args.get('customer_id', type=int)
        if customer_id:
            customer = Customer.query.get(customer_id)
            if customer:
                # Formular mit Kundendaten vorausfüllen
                form.customer_id.data = customer_id
                form.customer_search.data = customer.full_name
        
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
                safe_rollback()
                flash(f'Fehler beim Erstellen des Angebots: {str(e)}', 'error')
        
        return render_template('quote_form.html', form=form, title='Neues Angebot')
    
    @app.route('/quote/<int:id>/edit')
    @login_required
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
    @login_required
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
            safe_rollback()
            flash(f'Fehler beim Hinzufügen der Position: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))
    
    @app.route('/quote/<int:id>/add_work_position', methods=['POST'])
    @login_required
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
                hours = safe_float_conversion_strict(work_step_hours[i] if i < len(work_step_hours) else 0)
                rate = safe_float_conversion_strict(work_step_rates[i] if i < len(work_step_rates) else get_default_hourly_rate(), get_default_hourly_rate())
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
                hours = safe_float_conversion_strict(work_step_hours[i] if i < len(work_step_hours) else 0)
                rate = safe_float_conversion_strict(work_step_rates[i] if i < len(work_step_rates) else get_default_hourly_rate(), get_default_hourly_rate())
                step_price = hours * rate
                
                sub_item = QuoteSubItem(
                    quote_item_id=quote_item.id,
                    description=f"{category}: {step_name}",
                    sub_number=f"{position_number}.{i + 1}",
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
            safe_rollback()
            flash(f'Fehler beim Hinzufügen der Arbeitsposition: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))

    @app.route('/quote/<int:id>/remove_item/<int:item_id>')
    @login_required
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
                safe_rollback()
                flash(f'Fehler beim Entfernen der Position: {str(e)}', 'error')
        else:
            flash('Ungültige Position!', 'error')
        
        return redirect(url_for('edit_quote', id=id))

    @app.route('/quotes/<int:id>/template-selector')
    @login_required
    def quote_template_selector(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            flash('Angenommene Angebote können nicht mehr bearbeitet werden!', 'warning')
            return redirect(url_for('view_quote', id=id))
        
        # Alle verfügbaren Positionsvorlagen laden
        templates = PositionTemplate.query.all()
        # Lieferanten für Dropdown laden
        suppliers = Supplier.query.all()
        return render_template('quote_template_selector.html', quote=quote, templates=templates, suppliers=suppliers)

    @app.route('/quotes/<int:id>/add_template', methods=['POST'])
    @login_required
    def add_template_to_quote(id):
        quote = Quote.query.get_or_404(id)
        
        # Prüfe ob Angebot angenommen wurde - dann eingefroren
        if quote.status == 'Angenommen':
            return jsonify({'success': False, 'message': 'Angenommene Angebote können nicht mehr bearbeitet werden!'})
        
        try:
            data = request.get_json()
            template_id = data.get('template_id')
            calculation_parameters = data.get('calculation_parameters', {})
            subitems_data = data.get('subitems', [])
            
            # Template laden für Informationen
            template = PositionTemplate.query.get_or_404(template_id)
            
            # Neue Position erstellen basierend auf der bearbeiteten Vorlage
            position_number = len(quote.quote_items) + 1
            
            # Berechnungsparameter extrahieren
            length = float(calculation_parameters.get('length', 0))
            width = float(calculation_parameters.get('width', 0))
            height = float(calculation_parameters.get('height', 0))
            area = float(calculation_parameters.get('area', 0))
            calculated_price = float(calculation_parameters.get('calculatedPrice', 0))
            
            # Hauptposition erstellen
            quote_item = QuoteItem(
                quote_id=quote.id,
                position_number=position_number,
                description=f"{template.name} (L:{length}cm, B:{width}cm, H:{height}cm)",
                quantity=1,
                unit_price=calculated_price,
                total_price=calculated_price
            )
            
            db.session.add(quote_item)
            db.session.flush()  # Um die ID zu erhalten
            
            # Unterpositionen aus den bearbeiteten Daten erstellen
            sub_position = 1
            for subitem_data in subitems_data:
                # Basis-Daten
                description = subitem_data.get('description', '')
                item_type = subitem_data.get('item_type', 'sonstiges')  # quote_edit verwendet kleinschreibung
                calculated_subitem_price = float(subitem_data.get('calculated_price', 0))
                
                # Erstelle QuoteSubItem mit berechneten Werten
                quote_subitem = QuoteSubItem(
                    quote_item_id=quote_item.id,
                    sub_number=f"{position_number}.{sub_position}",
                    description=description,
                    item_type=item_type,  # Direkt verwenden, da Template-Selector angepasst wird
                    price=calculated_subitem_price
                )
                
                # Typ-spezifische Felder setzen
                if item_type == 'bestellteil':
                    quote_subitem.supplier = subitem_data.get('supplier', '')
                    quote_subitem.part_number = subitem_data.get('supplier_part_number', '')
                    quote_subitem.part_quantity = subitem_data.get('part_quantity', '1')
                    quote_subitem.requires_order = subitem_data.get('requires_order', False)
                    quote_subitem.part_price = calculated_subitem_price
                    
                elif item_type == 'arbeitsvorgang':
                    quote_subitem.hours = float(subitem_data.get('hours', 0))
                    quote_subitem.hourly_rate = float(subitem_data.get('hourly_rate', 95))
                    
                else:  # sonstiges
                    quote_subitem.quantity = subitem_data.get('quantity', '1')
                    quote_subitem.unit_price = float(subitem_data.get('base_price', 0))
                
                db.session.add(quote_subitem)
                sub_position += 1
            
            db.session.commit()
            quote.update_total()
            
            return jsonify({
                'success': True,
                'message': f'Vorlage "{template.name}" wurde erfolgreich mit {len(subitems_data)} Unterpositionen hinzugefügt!',
                'position_number': position_number,
                'total_price': calculated_price,
                'subitems_count': len(subitems_data)
            })
            
        except Exception as e:
            safe_rollback()
            return jsonify({'success': False, 'message': f'Fehler beim Hinzufügen der Vorlage: {str(e)}'})
    
    @app.route('/quote/<int:id>/delete')
    @login_required
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
    @login_required
    def send_quote(id):
        return update_quote_status(id, 'Gesendet')
    
    @app.route('/quote/<int:id>/accept', methods=['GET', 'POST'])
    @login_required
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
                

                # Erstelle SupplierOrder-Einträge mit Status 'Noch nicht bestellt', falls noch nicht vorhanden
                from models import SupplierOrder, SupplierOrderItem
                for supplier_name, order_items in supplier_orders.items():
                    if order_items:
                        existing_order = SupplierOrder.query.filter_by(
                            quote_id=quote.id,
                            supplier_name=supplier_name
                        ).first()
                        if not existing_order:
                            supplier_order = SupplierOrder(
                                quote_id=quote.id,
                                order_id=order.id,
                                supplier_name=supplier_name,
                                status='Noch nicht bestellt'
                            )
                            db.session.add(supplier_order)
                            db.session.flush()
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
                            # Falls schon vorhanden, nur Auftrag zuordnen
                            existing_order.order_id = order.id

                db.session.commit()


                flash(f'Angebot {quote.quote_number} wurde angenommen und Auftrag {order_number} erstellt!', 'success')
                return redirect(url_for('supplier_orders'))
                    
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Angebot annehmen: {str(e)}', 'error')
                return render_template('order_form.html', quote=quote, form=form, action='accept')
        
        return render_template('order_form.html', quote=quote, form=form, action='accept')
    
    @app.route('/quote/<int:id>/reject', methods=['GET', 'POST'])
    @login_required
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
    @login_required
    def reset_quote(id):
        return update_quote_status(id, 'Entwurf')
    
    # PDF Export
    @app.route('/quote/<int:id>/pdf')
    @login_required
    def export_quote_pdf(id):
        try:
            pdf_exporter = PDFExporter()
            return pdf_exporter.export_quote(id)
        except Exception as e:
            flash(f'Fehler beim PDF-Export: {str(e)}', 'error')
            return redirect(url_for('edit_quote', id=id))
    
    # Lieferanten-Routen
    @app.route('/suppliers')
    @login_required
    def suppliers():
        suppliers = Supplier.query.all()
        return render_template('suppliers.html', suppliers=suppliers)
    
    @app.route('/supplier/new', methods=['GET', 'POST'])
    @login_required
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
    @login_required
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
    @login_required
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
    @login_required
    def stammdaten():
        suppliers = Supplier.query.all()
        current_hourly_rate = get_default_hourly_rate()
        categories = db.session.query(Supplier.category).filter(
            Supplier.category.isnot(None)
        ).filter(Supplier.category != '').distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]

        # Akquisekanäle laden
        acquisition_channels = AcquisitionChannel.query.all()

        # PositionTemplates laden
        from models import PositionTemplate
        templates = PositionTemplate.query.all()

        return render_template('stammdaten.html', 
                             suppliers=suppliers, 
                             current_hourly_rate=current_hourly_rate, 
                             categories=categories,
                             acquisition_channels=acquisition_channels,
                             templates=templates)
    # --- PositionTemplate Stammdaten-UI ---
    from models import PositionTemplate, PositionTemplateSubItem

    @app.route('/stammdaten/templates/new', methods=['GET', 'POST'])
    @login_required
    def add_template():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Bitte einen Namen für die Vorlage angeben!', 'error')
                return redirect(url_for('stammdaten'))
            template = PositionTemplate(name=name)
            db.session.add(template)
            db.session.commit()
            flash('Vorlage wurde angelegt!', 'success')
            return redirect(url_for('stammdaten'))
        return render_template('add_template.html')

    @app.route('/stammdaten/templates/<int:template_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_template(template_id):
        template = PositionTemplate.query.get_or_404(template_id)
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Bitte einen Namen für die Vorlage angeben!', 'error')
                return redirect(url_for('edit_template', template_id=template_id))
            
            # Template-Name aktualisieren
            template.name = name
            
            # Kalkulationsfelder aktualisieren
            template.enable_length = 'enable_length' in request.form
            template.enable_width = 'enable_width' in request.form
            template.enable_height = 'enable_height' in request.form
            template.enable_area = 'enable_area' in request.form
            template.enable_volume = 'enable_volume' in request.form
            
            db.session.commit()
            flash('Vorlage wurde aktualisiert!', 'success')
            return redirect(url_for('stammdaten'))
        return render_template('edit_template.html', template=template)

    @app.route('/stammdaten/templates/<int:template_id>/delete', methods=['POST'])
    @login_required
    def delete_template(template_id):
        template = PositionTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        flash('Vorlage wurde gelöscht!', 'success')
        return redirect(url_for('stammdaten'))

    @app.route('/stammdaten/templates/<int:template_id>/add_subitem', methods=['POST'])
    @login_required
    def add_template_subitem(template_id):
        template = PositionTemplate.query.get_or_404(template_id)
        description = request.form.get('description', '').strip()
        item_type = request.form.get('item_type', '').strip()
        unit = request.form.get('unit', '').strip()
        price_per_unit = request.form.get('price_per_unit', type=float)
        formula = request.form.get('formula', '').strip()
        if not description or not item_type:
            flash('Bitte Beschreibung und Typ angeben!', 'error')
            return redirect(url_for('edit_template', template_id=template_id))
        
        # Get next position
        max_position = db.session.query(db.func.max(PositionTemplateSubItem.position)).filter_by(template_id=template_id).scalar() or 0
        
        subitem = PositionTemplateSubItem(
            template_id=template.id,
            description=description,
            item_type=item_type,
            unit=unit,
            price_per_unit=price_per_unit,
            formula=formula,
            position=max_position + 1
        )
        db.session.add(subitem)
        db.session.commit()
        flash('Unterposition hinzugefügt!', 'success')
        return redirect(url_for('edit_template', template_id=template_id))

    @app.route('/stammdaten/templates/<int:template_id>/delete_subitem/<int:subitem_id>', methods=['POST'])
    @login_required
    def delete_template_subitem(template_id, subitem_id):
        subitem = PositionTemplateSubItem.query.get_or_404(subitem_id)
        db.session.delete(subitem)
        db.session.commit()
        
        # Check if this is an AJAX request
        if request.headers.get('Content-Type') == 'application/json' or request.is_json:
            return jsonify({'success': True})
        
        flash('Unterposition gelöscht!', 'success')
        return redirect(url_for('edit_template', template_id=template_id))

    @app.route('/update_template_subitem_order/<int:template_id>', methods=['POST'])
    @login_required
    def update_template_subitem_order(template_id):
        try:
            data = request.get_json()
            order_data = data.get('order', [])
            
            # Update position for each subitem
            for item in order_data:
                subitem_id = item['id']
                new_position = item['position']
                
                subitem = PositionTemplateSubItem.query.get(subitem_id)
                if subitem and subitem.template_id == template_id:
                    subitem.position = new_position
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/update_template_subitem/<int:subitem_id>', methods=['POST'])
    @login_required
    def update_template_subitem(subitem_id):
        try:
            subitem = PositionTemplateSubItem.query.get_or_404(subitem_id)
            data = request.get_json()
            
            # Update fields
            if 'description' in data:
                subitem.description = data['description']
            if 'item_type' in data:
                subitem.item_type = data['item_type']
            if 'unit' in data:
                subitem.unit = data['unit'] if data['unit'] else None
            if 'price_per_unit' in data:
                subitem.price_per_unit = float(data['price_per_unit']) if data['price_per_unit'] else None
            if 'formula' in data:
                subitem.formula = data['formula'] if data['formula'] else None
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/stammdaten/arbeitsschritte')
    @login_required
    def work_steps_management():
        work_steps = get_work_steps()
        return render_template('work_steps_management.html', work_steps=work_steps)
    
    @app.route('/stammdaten/arbeitsschritte/update', methods=['POST'])
    @login_required
    def update_work_steps():
        try:
            from work_steps import WORK_STEPS
            import os
            
            # Sammle alle Formulardaten
            form_data = request.form
            new_work_steps = {}
            
            # Verarbeite existierende Arbeitsschritte
            for key, value in form_data.items():
                if key.startswith('step_name_'):
                    # Extrahiere Kategorie und Index aus dem Key
                    parts = key.replace('step_name_', '').rsplit('_', 1)
                    if len(parts) == 2:
                        category = parts[0]
                        index = parts[1]
                        
                        step_name = value
                        step_hours = float(form_data.get(f'step_hours_{category}_{index}', 0))
                        
                        if step_name.strip():  # Nur wenn Name nicht leer ist
                            if category not in new_work_steps:
                                new_work_steps[category] = []
                            
                            step = {
                                "name": step_name,
                                "default_hours": step_hours
                            }
                            
                            new_work_steps[category].append(step)
            
            # Aktualisiere die work_steps.py Datei
            work_steps_content = f'''# Arbeitsschritte-Konfiguration für Angebotserstellung
# Diese Datei definiert alle verfügbaren Arbeitsschritte mit Standardzeiten

WORK_STEPS = {repr(new_work_steps)}

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
'''
            
            # Schreibe die neue Datei
            with open('work_steps.py', 'w', encoding='utf-8') as f:
                f.write(work_steps_content)
            
            # Lade das Modul neu
            import importlib
            import work_steps
            importlib.reload(work_steps)
            
            flash('Arbeitsschritte wurden erfolgreich gespeichert!', 'success')
            
        except Exception as e:
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return redirect(url_for('work_steps_management'))
    
    # Einstellungen
    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        form = SettingsForm()
        
        if request.method == 'GET':
            # Beim GET Request: Aktuellen Wert aus DB laden
            form.default_hourly_rate.data = get_default_hourly_rate()
        
        if form.validate_on_submit():
            try:
                # Validiere den eingegeben Wert
                hourly_rate = float(form.default_hourly_rate.data)
                if hourly_rate <= 0:
                    flash('Stundensatz muss größer als 0 sein!', 'error')
                    return render_template('settings.html', form=form)
                
                # Speichere die Einstellung
                CompanySettings.set_setting(
                    'default_hourly_rate', 
                    hourly_rate,
                    'Standard-Stundensatz für Arbeitsvorgänge'
                )
                
                # Debug: Prüfe ob der Wert wirklich gespeichert wurde
                saved_value = get_default_hourly_rate()
                if saved_value == hourly_rate:
                    flash(f'Einstellungen wurden erfolgreich gespeichert! Neuer Stundensatz: {hourly_rate:.2f} €', 'success')
                else:
                    flash(f'Warnung: Gespeicherter Wert ({saved_value:.2f} €) entspricht nicht dem eingegebenen Wert ({hourly_rate:.2f} €)!', 'warning')
                
                return redirect(url_for('settings'))
            except ValueError:
                flash('Ungültiger Stundensatz! Bitte geben Sie eine gültige Zahl ein.', 'error')
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('settings.html', form=form)
    
    # Debug-Route für Settings (nur in Entwicklung)
    @app.route('/admin/debug_settings')
    @login_required
    def debug_settings():
        """Debug-Informationen für Settings anzeigen"""
        from flask import jsonify
        
        try:
            # Alle Settings aus der Datenbank
            all_settings = CompanySettings.query.all()
            settings_data = []
            
            for setting in all_settings:
                settings_data.append({
                    'name': setting.setting_name,
                    'value': setting.setting_value,
                    'description': setting.description,
                    'created_at': setting.created_at.isoformat() if setting.created_at else None,
                    'updated_at': setting.updated_at.isoformat() if setting.updated_at else None
                })
            
            # Aktueller Wert über get_default_hourly_rate()
            current_rate = get_default_hourly_rate()
            
            return jsonify({
                'current_hourly_rate': current_rate,
                'all_settings': settings_data,
                'settings_count': len(settings_data)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Admin-Routen
    @app.route('/admin/reload_templates')
    @login_required
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
    @login_required
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
    @login_required
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
    @login_required
    def view_quote(id):
        quote = Quote.query.get_or_404(id)
        return render_template('quote_view.html', quote=quote)

    # Angebot speichern
    @app.route('/quote/<int:id>/save', methods=['POST'])
    @login_required
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
            price_display_mode = request.form.get('price_display_mode', 'standard')  # Neues Feld
            markup_percentage = safe_float_conversion(request.form.get('markup_percentage'), 15.0)
            
            if project_description:
                quote.project_description = project_description
                
            if valid_until:
                from datetime import datetime
                quote.valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date()
                
            quote.include_additional_info = include_additional_info
            quote.show_subitem_prices = show_subitem_prices  # Kompatibilität beibehalten
            quote.price_display_mode = price_display_mode  # Neues Feld speichern
            quote.markup_percentage = markup_percentage
            
            quote.update_total()
            flash('Angebot wurde erfolgreich gespeichert!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return redirect(url_for('edit_quote', id=id))

    # Position bearbeiten
    @app.route('/quote/<int:id>/edit_item/<int:item_id>', methods=['GET', 'POST'])
    @login_required
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
                        flash('Bitte füllen Sie alle Felder korrekt aus!', 'error')

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

                    # Alte Unterpositionen löschen
                    for sub_item in item.sub_items:
                        db.session.delete(sub_item)

                    # Arbeitsschritte aus dem Formular lesen
                    work_step_categories = request.form.getlist('work_step_categories[]')
                    work_step_names = request.form.getlist('work_step_names[]')
                    work_step_hours = request.form.getlist('work_step_hours[]')
                    work_step_rates = request.form.getlist('work_step_rates[]')

                    total_price = 0
                    for i in range(len(work_step_categories)):
                        hours = safe_float_conversion_strict(work_step_hours[i] if i < len(work_step_hours) else 0)
                        rate = safe_float_conversion_strict(work_step_rates[i] if i < len(work_step_rates) else get_default_hourly_rate(), get_default_hourly_rate())
                        total_price += hours * rate

                    # Hauptposition aktualisieren
                    item.description = description
                    item.position_number = position_number
                    item.quantity = 1
                    item.unit_price = total_price
                    item.total_price = total_price

                    # Neue Unterpositionen erstellen
                    for i in range(len(work_step_categories)):
                        category = work_step_categories[i]
                        step_name = work_step_names[i]
                        hours = safe_float_conversion_strict(work_step_hours[i] if i < len(work_step_hours) else 0)
                        rate = safe_float_conversion_strict(work_step_rates[i] if i < len(work_step_rates) else get_default_hourly_rate(), get_default_hourly_rate())
                        step_price = hours * rate

                        sub_item = QuoteSubItem(
                            quote_item_id=item.id,
                            description=f"{category}: {step_name}",
                            sub_number=f"{position_number}.{i + 1}",
                            item_type='arbeitsvorgang',
                            hours=hours,
                            hourly_rate=rate,
                            price=step_price
                        )
                        db.session.add(sub_item)

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
        return render_template(
            'quote_item_edit.html',
            quote=quote,
            item=item,
            suppliers=suppliers,
            work_steps=work_steps,
            get_default_hourly_rate=get_default_hourly_rate
        )

    # Bestellungen bestätigen
    @app.route('/quote/<int:quote_id>/confirm_orders', methods=['POST'])
    @login_required
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
    @login_required
    def supplier_orders():
        from models import SupplierOrder, Order
        from flask import request
        from sqlalchemy.orm import joinedload
        
        # Filter-Parameter aus URL lesen
        order_id = request.args.get('order_id', type=int)
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'order_date')
        sort_dir = request.args.get('dir', 'desc')
        filter_order = None
        
        # Basis-Query mit JOINs aufbauen
        base_query = SupplierOrder.query.options(
            joinedload(SupplierOrder.items),
            joinedload(SupplierOrder.quote).joinedload(Quote.customer),
            joinedload(SupplierOrder.order)
        )
        
        # Filter nach Auftrag-ID wenn angegeben
        if order_id:
            filter_order = Order.query.get(order_id)
            base_query = base_query.filter_by(order_id=order_id)
        
        # Suchfilter anwenden
        if search_query:
            base_query = base_query.filter(
                db.or_(
                    SupplierOrder.supplier_name.ilike(f'%{search_query}%'),
                    SupplierOrder.notes.ilike(f'%{search_query}%'),
                    SupplierOrder.quote.has(Quote.quote_number.ilike(f'%{search_query}%')),
                    SupplierOrder.quote.has(Quote.project_description.ilike(f'%{search_query}%')),
                    SupplierOrder.quote.has(Quote.customer.has(Customer.first_name.ilike(f'%{search_query}%'))),
                    SupplierOrder.quote.has(Quote.customer.has(Customer.last_name.ilike(f'%{search_query}%'))),
                    SupplierOrder.quote.has(Quote.customer.has(
                        db.func.concat(Customer.first_name, ' ', Customer.last_name).ilike(f'%{search_query}%')
                    )),
                    SupplierOrder.order.has(Order.order_number.ilike(f'%{search_query}%'))
                )
            )
        
        # Sortierung anwenden
        sort_column = None
        if sort_by == 'order_date':
            sort_column = SupplierOrder.order_date
        elif sort_by == 'supplier_name':
            sort_column = SupplierOrder.supplier_name
        elif sort_by == 'quote_number':
            sort_column = Quote.quote_number
            base_query = base_query.join(Quote)
        elif sort_by == 'order_number':
            sort_column = Order.order_number
            base_query = base_query.join(Order)
        elif sort_by == 'customer':
            sort_column = Customer.last_name
            base_query = base_query.join(Quote).join(Customer)
        elif sort_by == 'status':
            sort_column = SupplierOrder.status
        elif sort_by == 'delivery_date':
            sort_column = SupplierOrder.delivery_date
        else:
            sort_column = SupplierOrder.order_date
        
        if sort_dir == 'desc':
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())
        
        orders = base_query.all()
        
        return render_template('supplier_orders.html', 
                             orders=orders, 
                             filter_order=filter_order, 
                             search_query=search_query,
                             sort_by=sort_by,
                             sort_dir=sort_dir)
    
    # Einzelne Bestellung bearbeiten
    @app.route('/supplier_order/<int:order_id>/edit', methods=['GET', 'POST'])
    @login_required
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
    @login_required
    def orders():
        from models import Order
        from flask import request
        from sqlalchemy.orm import joinedload
        
        # Filter-Parameter aus URL lesen
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'created_at')
        sort_dir = request.args.get('dir', 'desc')
        
        # Basis-Query mit JOINs aufbauen
        query = Order.query.options(
            joinedload(Order.quote).joinedload(Quote.customer)
        )
        
        # Suchfilter anwenden
        if search_query:
            query = query.filter(
                db.or_(
                    Order.order_number.ilike(f'%{search_query}%'),
                    Order.project_manager.ilike(f'%{search_query}%'),
                    Order.quote.has(Quote.project_description.ilike(f'%{search_query}%')),
                    Order.quote.has(Quote.customer.has(Customer.first_name.ilike(f'%{search_query}%'))),
                    Order.quote.has(Quote.customer.has(Customer.last_name.ilike(f'%{search_query}%'))),
                    Order.quote.has(Quote.customer.has(
                        db.func.concat(Customer.first_name, ' ', Customer.last_name).ilike(f'%{search_query}%')
                    ))
                )
            )
        
        # Sortierung anwenden
        sort_column = None
        if sort_by == 'order_number':
            sort_column = Order.order_number
        elif sort_by == 'customer':
            sort_column = Customer.last_name
            query = query.join(Quote).join(Customer)
        elif sort_by == 'project_description':
            sort_column = Quote.project_description
            query = query.join(Quote)
        elif sort_by == 'total_amount':
            sort_column = Quote.total_amount
            query = query.join(Quote)
        elif sort_by == 'status':
            sort_column = Order.status
        elif sort_by == 'start_date':
            sort_column = Order.start_date
        elif sort_by == 'created_at':
            sort_column = Order.created_at
        else:
            sort_column = Order.created_at
        
        if sort_dir == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        orders = query.all()
        
        return render_template('orders.html', 
                             orders=orders, 
                             search_query=search_query,
                             sort_by=sort_by,
                             sort_dir=sort_dir)
    
    @app.route('/quote/<int:quote_id>/create_order', methods=['GET', 'POST'])
    @login_required
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
    @login_required
    def view_order(order_id):
        from models import Order
        order = Order.query.get_or_404(order_id)
        return render_template('order_view.html', order=order)
    
    @app.route('/order/<int:order_id>/edit', methods=['GET', 'POST'])
    @login_required
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
    @login_required
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
    @login_required
    def repair_order_table():
        """Repariert die Order-Tabelle und fügt fehlende Spalten hinzu"""
        try:
            # Backup der Datenbank erstellen
            import shutil
            from datetime import datetime
            import sqlite3
            from contextlib import closing
            
            db_path = 'instance/installation_business.db'
            backup_path = f'instance/installation_business_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                flash(f'Backup erstellt: {backup_path}', 'info')
            
            # Verwende Context Manager für sichere Connection-Behandlung
            with closing(sqlite3.connect(db_path)) as conn:
                with closing(conn.cursor()) as cursor:
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
                    
                    # Commit alle Änderungen - wird automatisch gerollt zurück bei Exception
                    conn.commit()
                    flash('Datenbank-Reparatur erfolgreich abgeschlossen!', 'success')
            
            # Connection wird automatisch durch Context Manager geschlossen
            
        except Exception as e:
            # Detailliertere Fehlerbehandlung
            import traceback
            error_details = traceback.format_exc()
            flash(f'Fehler bei der Reparatur: {str(e)}', 'error')
            # Log für Debugging (nur in Development)
            print(f"Database repair error: {error_details}")
        
        return redirect(url_for('index'))

    # Admin-Route zur Verknüpfung von Lieferantenbestellungen mit Aufträgen
    @app.route('/admin/link_supplier_orders')
    @login_required
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
            safe_rollback()
            flash(f'Fehler beim Verknüpfen: {str(e)}', 'error')
            
        return redirect(url_for('index'))

    # Arbeitsanweisungen
    @app.route('/order/<int:order_id>/work_instruction/create')
    @login_required
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
    @login_required
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
    @login_required
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
    @login_required
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
    @login_required
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

    # Debug-Route zum Testen
    @app.route('/test')
    @login_required
    def test_route():
        return "<h1>Test erfolgreich!</h1><p>Flask funktioniert korrekt.</p>"
    
    @app.route('/test-template')
    @login_required
    def test_template():
        try:
            return render_template('base.html')
        except Exception as e:
            return f"Template-Fehler: {str(e)}"
    
    # Akquisekanal-Verwaltung
    @app.route('/stammdaten/akquise/new', methods=['GET', 'POST'])
    @login_required
    def new_acquisition_channel():
        form = AcquisitionChannelForm()
        
        if form.validate_on_submit():
            try:
                channel = AcquisitionChannel(
                    name=form.name.data,
                    description=form.description.data,
                    is_active=form.is_active.data
                )
                db.session.add(channel)
                db.session.commit()
                flash('Akquisekanal wurde erfolgreich hinzugefügt!', 'success')
                return redirect(url_for('stammdaten'))
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('acquisition_channel_form.html', form=form, title='Neuer Akquisekanal')
    
    @app.route('/stammdaten/akquise/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_acquisition_channel(id):
        channel = AcquisitionChannel.query.get_or_404(id)
        form = AcquisitionChannelForm(obj=channel)
        
        if form.validate_on_submit():
            try:
                form.populate_obj(channel)
                db.session.commit()
                flash('Akquisekanal wurde erfolgreich bearbeitet!', 'success')
                return redirect(url_for('stammdaten'))
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('acquisition_channel_form.html', form=form, title='Akquisekanal bearbeiten', channel=channel)
    
    @app.route('/stammdaten/akquise/<int:id>/delete')
    @login_required
    def delete_acquisition_channel(id):
        channel = AcquisitionChannel.query.get_or_404(id)
        
        # Prüfe ob Kanal von Kunden verwendet wird
        customers_using_channel = Customer.query.filter_by(acquisition_channel_id=id).count()
        if customers_using_channel > 0:
            flash(f'Akquisekanal kann nicht gelöscht werden - er wird von {customers_using_channel} Kunde(n) verwendet!', 'error')
            return redirect(url_for('stammdaten'))
        
        try:
            channel_name = channel.name
            db.session.delete(channel)
            db.session.commit()
            flash(f'Akquisekanal "{channel_name}" wurde erfolgreich gelöscht!', 'success')
        except Exception as e:
            safe_rollback()
            flash(f'Fehler beim Löschen: {str(e)}', 'error')
        
        return redirect(url_for('stammdaten'))

    # Customer Workflow-Routen
    @app.route('/customer/<int:id>/workflow', methods=['GET', 'POST'])
    @login_required
    def customer_workflow(id):
        customer = Customer.query.get_or_404(id)
        form = CustomerWorkflowForm(obj=customer)
        
        if form.validate_on_submit():
            try:
                old_status = customer.status
                customer.status = form.status.data
                customer.appointment_date = form.appointment_date.data
                customer.appointment_notes = form.appointment_notes.data
                customer.comments = form.comments.data
                
                # Automatische Status-Updates basierend auf Aktionen
                if form.appointment_date.data and customer.status == '1. Termin vereinbaren':
                    customer.status = '2. Termin vereinbart'
                
                db.session.commit()
                flash(f'Workflow-Status wurde von "{old_status}" auf "{customer.status}" aktualisiert!', 'success')
                return redirect(url_for('customer_detail', id=id))
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Aktualisieren: {str(e)}', 'error')
        
        return render_template('customer_workflow.html', form=form, customer=customer, title='Workflow verwalten')
    
    @app.route('/customer/<int:id>/appointment', methods=['GET', 'POST'])
    @login_required
    def schedule_appointment(id):
        customer = Customer.query.get_or_404(id)
        form = AppointmentForm()
        
        # Vorhandenen Termin laden
        if customer.appointment_date:
            form.appointment_date.data = customer.appointment_date
            form.appointment_notes.data = customer.appointment_notes
        
        if form.validate_on_submit():
            try:
                customer.appointment_date = form.appointment_date.data
                customer.appointment_notes = form.appointment_notes.data
                
                # Status automatisch auf "2. Termin vereinbart" setzen
                if customer.status == '1. Termin vereinbaren':
                    customer.status = '2. Termin vereinbart'
                
                db.session.commit()
                flash('Termin wurde erfolgreich gespeichert!', 'success')
                return redirect(url_for('customer_detail', id=id))
            except Exception as e:
                safe_rollback()
                flash(f'Fehler beim Speichern: {str(e)}', 'error')
        
        return render_template('appointment_form.html', form=form, customer=customer, title='Termin vereinbaren')
    
    @app.route('/customer/<int:id>/create_quote')
    @login_required
    def create_quote_for_customer(id):
        customer = Customer.query.get_or_404(id)
        
        # Automatisch Angebots-Formular mit vorausgefülltem Kunden öffnen
        return redirect(url_for('new_quote', customer_id=id))
    
    @app.route('/customer/<int:id>/detail')
    @login_required
    def customer_detail(id):
        customer = Customer.query.get_or_404(id)
        quotes = Quote.query.filter_by(customer_id=id).order_by(Quote.created_at.desc()).all()
        
        return render_template('customer_detail.html', customer=customer, quotes=quotes, title=f'Kunde: {customer.full_name}')

    # --- Neue Template-Verwaltungsseite ---
    @app.route('/stammdaten/templates')
    @login_required
    def template_management():
        """Hauptseite für Template-Verwaltung"""
        templates = PositionTemplate.query.all()
        return render_template('template_management.html', templates=templates)
    
    @app.route('/stammdaten/templates/create', methods=['GET', 'POST'])
    @login_required
    def create_template():
        """Erstelle neue Vorlage mit allen Funktionen"""
        if request.method == 'POST':
            try:
                name = request.form.get('name', '').strip()
                description = request.form.get('description', '').strip()
                
                if not name:
                    return jsonify({'success': False, 'message': 'Name ist erforderlich'})
                
                # Erstelle Template mit Kalkulationsfeldern
                template = PositionTemplate(
                    name=name,
                    description=description,
                    enable_length='enable_length' in request.form,
                    enable_width='enable_width' in request.form,
                    enable_height='enable_height' in request.form,
                    enable_area='enable_area' in request.form,
                    enable_volume='enable_volume' in request.form
                )
                
                print(f"DEBUG: Template object created:")
                print(f"  enable_length: {template.enable_length}")
                print(f"  enable_width: {template.enable_width}")
                print(f"  enable_height: {template.enable_height}")
                print(f"  enable_area: {template.enable_area}")
                print(f"  enable_volume: {template.enable_volume}")
                db.session.add(template)
                db.session.flush()  # Um ID zu bekommen
                
                # Verarbeite Unterpositionen
                sub_descriptions = request.form.getlist('sub_description[]')
                sub_types = request.form.getlist('sub_type[]')
                sub_units = request.form.getlist('sub_unit[]')
                sub_prices = request.form.getlist('sub_price[]')
                sub_formulas = request.form.getlist('sub_formula[]')
                
                for i in range(len(sub_descriptions)):
                    if sub_descriptions[i].strip() and sub_types[i].strip():
                        subitem = PositionTemplateSubItem(
                            template_id=template.id,
                            description=sub_descriptions[i].strip(),
                            item_type=sub_types[i].strip(),
                            unit=sub_units[i].strip() if i < len(sub_units) else '',
                            price_per_unit=float(sub_prices[i]) if i < len(sub_prices) and sub_prices[i] else 0,
                            formula=sub_formulas[i].strip() if i < len(sub_formulas) else ''
                        )
                        db.session.add(subitem)
                
                db.session.commit()
                
                flash('Vorlage wurde erfolgreich erstellt!', 'success')
                return redirect(url_for('template_management'))
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Fehler beim Erstellen der Vorlage: {str(e)}', 'error')
                return redirect(url_for('template_management'))
        
        # GET Request - zeige Formular
        templates = PositionTemplate.query.all()
        return render_template('template_management.html', templates=templates, title='Neue Vorlage erstellen')
    
    @app.route('/stammdaten/templates/<int:template_id>/duplicate', methods=['POST'])
    @login_required
    def duplicate_template(template_id):
        """Dupliziere eine bestehende Vorlage"""
        try:
            original = PositionTemplate.query.get_or_404(template_id)
            
            # Erstelle Kopie
            duplicate = PositionTemplate(
                name=f"{original.name} (Kopie)",
                category=original.category,
                description=original.description
            )
            db.session.add(duplicate)
            db.session.flush()
            
            # Kopiere Unterpositionen
            for subitem in original.subitems:
                new_subitem = PositionTemplateSubItem(
                    template_id=duplicate.id,
                    description=subitem.description,
                    item_type=subitem.item_type,
                    unit=subitem.unit,
                    price_per_unit=subitem.price_per_unit,
                    formula=subitem.formula
                )
                db.session.add(new_subitem)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Vorlage dupliziert'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Fehler beim Duplizieren: {str(e)}'})
    
    @app.route('/stammdaten/templates/<int:template_id>/delete_ajax', methods=['POST'])
    @login_required
    def delete_template_ajax(template_id):
        """Lösche Template via AJAX"""
        try:
            template = PositionTemplate.query.get_or_404(template_id)
            db.session.delete(template)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Vorlage gelöscht'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Fehler beim Löschen: {str(e)}'})

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
            hours = safe_float_conversion_strict(sub_hours[i] if i < len(sub_hours) else 0)
            hourly_rate = safe_float_conversion_strict(
                sub_hourly_rates[i] if i < len(sub_hourly_rates) else get_default_hourly_rate(), get_default_hourly_rate()
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
            unit_price = safe_float_conversion_strict(sub_unit_prices[i] if i < len(sub_unit_prices) else 0)
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
            part_price = safe_float_conversion_strict(sub_part_prices[i] if i < len(sub_part_prices) else 0)
            
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
        
        # Wenn Angebot auf "Gesendet" gesetzt wird, Kunden-Status aktualisieren
        if new_status == 'Gesendet':
            customer = quote.customer
            if customer.status in ['3. Angebot erstellen', '2. Termin vereinbart']:
                customer.status = 'Angebot wurde erstellt'
        
        db.session.commit()
        flash(f'Angebot {quote.quote_number} wurde als "{new_status}" markiert!', 'success')
    except Exception as e:
        safe_rollback()
        flash(f'Fehler beim Aktualisieren des Status: {str(e)}', 'error')
    
    return redirect(url_for('edit_quote', id=quote_id))

# App erstellen und starten
app = create_app()

# ===============================
# LOGIN-SYSTEM
# ===============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin Login"""
    if request.method == 'POST':
        login_username = request.form['login_username']
        login_password = request.form['login_password']
        
        from models import LoginAdmin
        login_admin = LoginAdmin.query.filter_by(
            login_username=login_username, 
            login_is_active=True
        ).first()
        
        if login_admin and login_admin.check_login_password(login_password):
            session['login_admin_id'] = login_admin.login_id
            session['login_admin_username'] = login_admin.login_username
            
            # Last login aktualisieren
            login_admin.login_last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Erfolgreich angemeldet!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin Logout"""
    session.clear()
    flash('Sie wurden erfolgreich abgemeldet.', 'info')
    return redirect(url_for('login'))

@app.route('/init-admin')
def init_admin():
    """Erstellt den ersten Admin-Account (nur beim ersten Start)"""
    from models import LoginAdmin
    
    # Prüfen ob bereits ein Admin existiert
    if LoginAdmin.query.first():
        return "Admin bereits vorhanden. Bitte /login verwenden."
    
    # Standard-Admin erstellen
    login_admin = LoginAdmin.create_login_admin('admin', 'admin123')  # WICHTIG: Passwort später ändern!
    db.session.add(login_admin)
    db.session.commit()
    
    return """
    <h2>Admin-Account erstellt!</h2>
    <p><strong>Benutzername:</strong> admin</p>
    <p><strong>Passwort:</strong> admin123</p>
    <p><strong>WICHTIG:</strong> Bitte ändern Sie das Passwort nach dem ersten Login!</p>
    <p><a href="/login">Zum Login</a></p>
    """

# ===============================
# RECHNUNGS-ROUTEN 
# ===============================

@app.route('/invoices')
@login_required
def invoices():
    """Rechnungsübersicht mit Filter- und Suchfunktionen"""
    from models import Invoice, Order, Customer, Quote
    from datetime import datetime, date, timedelta
    from sqlalchemy import and_, or_
    
    # Filter-Parameter
    status_filter = request.args.get('status', '')
    invoice_type_filter = request.args.get('invoice_type', '')
    period_filter = request.args.get('period', '')
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    
    # Base Query - einfacher ohne komplexe Joins
    query = Invoice.query
    
    # Status-Filter
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    # Typ-Filter
    if invoice_type_filter:
        query = query.filter(Invoice.invoice_type == invoice_type_filter)
    
    # Zeitraum-Filter
    if period_filter:
        today = date.today()
        if period_filter == 'today':
            query = query.filter(Invoice.created_at >= today)
        elif period_filter == 'week':
            week_start = today - timedelta(days=today.weekday())
            query = query.filter(Invoice.created_at >= week_start)
        elif period_filter == 'month':
            month_start = today.replace(day=1)
            query = query.filter(Invoice.created_at >= month_start)
        elif period_filter == 'quarter':
            quarter_start = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)
            query = query.filter(Invoice.created_at >= quarter_start)
    
    # Suchfilter - vereinfacht
    if search_query:
        query = query.join(Order).join(Quote).join(Customer).filter(
            or_(
                Invoice.invoice_number.ilike(f'%{search_query}%'),
                Customer.first_name.ilike(f'%{search_query}%'),
                Customer.last_name.ilike(f'%{search_query}%'),
                Order.order_number.ilike(f'%{search_query}%')
            )
        )
    
    # Pagination
    invoices = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiken für Dashboard
    stats = {
        'open_count': Invoice.query.filter(Invoice.status.in_(['erstellt', 'versendet'])).count(),
        'paid_count': Invoice.query.filter_by(status='bezahlt').count(),
        'overdue_count': Invoice.query.filter(
            and_(Invoice.status != 'bezahlt', Invoice.due_date < date.today())
        ).count(),
        'total_amount': sum(
            invoice.gross_amount for invoice in Invoice.query.filter_by(status='bezahlt').all()
        ) or 0
    }
    
    # Verfügbare Aufträge für neue Rechnungen
    available_orders = Order.query.filter(
        Order.status.in_(['Angenommen', 'Geplant', 'In Arbeit', 'Abgeschlossen'])
    ).all()
    
    return render_template('invoices.html',
                         invoices=invoices,
                         stats=stats,
                         available_orders=available_orders,
                         today=date.today)

@app.route('/invoices/create', methods=['POST'])
@login_required
def create_invoice():
    """Erstellt eine neue Rechnung"""
    from models import Invoice, Order
    from datetime import datetime, date, timedelta
    
    try:
        # Sichere Formular-Daten-Extraktion
        order_id = request.form.get('order_id')
        invoice_type = request.form.get('invoice_type')
        percentage_str = request.form.get('percentage')
        due_date_str = request.form.get('due_date')
        
        # Validierung der Eingabedaten
        if not order_id:
            return jsonify({'success': False, 'message': 'Auftrag ist erforderlich'})
        if not invoice_type:
            return jsonify({'success': False, 'message': 'Rechnungstyp ist erforderlich'})
        if not percentage_str:
            return jsonify({'success': False, 'message': 'Prozentsatz ist erforderlich'})
        if not due_date_str:
            return jsonify({'success': False, 'message': 'Fälligkeitsdatum ist erforderlich'})
        
        # Sichere Konvertierung
        try:
            order_id = int(order_id)
            percentage = float(percentage_str)
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'message': f'Ungültige Eingabedaten: {str(e)}'})
        
        # Prozentsatz-Validierung
        if percentage <= 0 or percentage > 100:
            return jsonify({'success': False, 'message': 'Prozentsatz muss zwischen 1 und 100 liegen'})
        
        order = Order.query.get_or_404(order_id)
        
        # Prüfen ob Rechnung bereits existiert
        existing = Invoice.query.filter_by(order_id=order_id, invoice_type=invoice_type).first()
        if existing:
            return jsonify({'success': False, 'message': f'{invoice_type.title()}rechnung existiert bereits'})
        
        # Grundbetrag aus Angebot holen
        base_amount = order.quote.calculate_net_total()
        if base_amount is None or base_amount <= 0:
            return jsonify({'success': False, 'message': 'Auftragswert konnte nicht ermittelt werden'})
        
        # Neue Rechnung erstellen
        invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            order_id=order_id,
            invoice_type=invoice_type,
            percentage=percentage,
            base_amount=base_amount,
            due_date=due_date,
            payment_terms=14,
            vat_rate=20.0,           # Explizit 20% MwSt setzen
            invoice_amount=0.0,      # Wird in calculate_amounts gesetzt
            final_amount=0.0,        # Wird in calculate_amounts gesetzt
            vat_amount=0.0,          # Wird in calculate_amounts gesetzt
            gross_amount=0.0         # Wird in calculate_amounts gesetzt
        )
        
        # Für Schlussrechnung: Bereits erhaltene Anzahlungen berechnen
        if invoice_type == 'schluss':
            anzahlung_invoices = Invoice.query.filter_by(
                order_id=order_id, 
                invoice_type='anzahlung'
            ).all()
            invoice.previous_payments = sum(inv.final_amount for inv in anzahlung_invoices if inv.final_amount)
        
        # Beträge berechnen
        invoice.calculate_amounts()
        
        db.session.add(invoice)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Rechnung wurde erfolgreich erstellt'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Erstellen der Rechnung: {str(e)}'})

@app.route('/invoices/<int:id>/mark_paid', methods=['POST'])
@login_required
def mark_invoice_paid(id):
    """Markiert eine Rechnung als bezahlt"""
    from models import Invoice
    from datetime import datetime, date
    
    try:
        invoice = Invoice.query.get_or_404(id)
        
        paid_date_str = request.form.get('paid_date')
        payment_reference = request.form.get('payment_reference', '')
        comment = request.form.get('comment', '')
        
        paid_date = datetime.strptime(paid_date_str, '%Y-%m-%d').date() if paid_date_str else date.today()
        
        invoice.mark_as_paid(paid_date, payment_reference, comment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Rechnung wurde als bezahlt markiert'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'})

@app.route('/invoices/<int:id>', methods=['GET'])
@login_required
def invoice_details(id):
    """Liefert Rechnungsdetails als HTML Modal"""
    from models import Invoice
    
    invoice = Invoice.query.get_or_404(id)
    
    # HTML für Modal zurückgeben
    return render_template('invoice_details.html', invoice=invoice)

@app.route('/invoices/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_invoice(id):
    """Löscht eine Rechnung"""
    from models import Invoice
    
    try:
        invoice = Invoice.query.get_or_404(id)
        
        # Prüfen ob Rechnung gelöscht werden kann
        if invoice.status == 'bezahlt':
            return jsonify({'success': False, 'message': 'Bezahlte Rechnungen können nicht gelöscht werden'})
        
        invoice_number = invoice.invoice_number
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Rechnung {invoice_number} wurde erfolgreich gelöscht'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Löschen: {str(e)}'})

@app.route('/invoices/<int:id>/update_status', methods=['POST'])
@login_required
def update_invoice_status(id):
    """Aktualisiert den Status einer Rechnung - mit Retour-Möglichkeit"""
    from models import Invoice
    
    try:
        invoice = Invoice.query.get_or_404(id)
        new_status = request.json.get('status')
        
        # Erweiterte Status-Möglichkeiten
        valid_statuses = ['erstellt', 'versendet', 'bezahlt']
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Ungültiger Status'})
        
        # Status-Wechsel validieren und erlauben
        current_status = invoice.status
        
        # Retour-Logik: Bezahlt kann zurück zu versendet, versendet zurück zu erstellt
        if (current_status == 'bezahlt' and new_status in ['versendet', 'erstellt']) or \
           (current_status == 'versendet' and new_status == 'erstellt') or \
           (current_status == 'erstellt' and new_status in ['versendet', 'bezahlt']) or \
           (current_status == 'versendet' and new_status == 'bezahlt'):
            
            invoice.status = new_status
            
            # Bezahlt-Daten zurücksetzen wenn Status von bezahlt geändert wird
            if current_status == 'bezahlt' and new_status != 'bezahlt':
                invoice.paid_date = None
                invoice.payment_reference = None
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'Status auf "{new_status}" geändert'})
        else:
            return jsonify({'success': False, 'message': 'Status-Wechsel nicht erlaubt'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'})

@app.route('/invoices/<int:id>/comments')
@login_required
def invoice_comments(id):
    """API für Rechnungskommentare"""
    from models import Invoice
    
    invoice = Invoice.query.get_or_404(id)
    return jsonify({'comments': invoice.comments or ''})

@app.route('/invoices/<int:id>/add_comment', methods=['POST'])
@login_required
def add_invoice_comment(id):
    """Fügt einen Kommentar zur Rechnung hinzu"""
    from models import Invoice
    from datetime import datetime
    
    try:
        invoice = Invoice.query.get_or_404(id)
        comment = request.form.get('comment', '').strip()
        
        if not comment:
            return jsonify({'success': False, 'message': 'Kommentar darf nicht leer sein'})
        
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')
        new_comment = f"[{timestamp}] {comment}"
        
        if invoice.comments:
            invoice.comments += f"\n\n{new_comment}"
        else:
            invoice.comments = new_comment
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Kommentar wurde hinzugefügt'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'})

@app.route('/invoices/<int:id>/pdf')
@login_required
def download_invoice_pdf(id):
    """Lädt das Rechnungs-PDF herunter"""
    from models import Invoice
    from invoice_pdf import InvoicePDFGenerator
    from flask import send_file
    
    try:
        invoice = Invoice.query.get_or_404(id)
        
        # PDF generieren
        pdf_generator = InvoicePDFGenerator()
        pdf_buffer = pdf_generator.generate_invoice_pdf(invoice)
        
        # Dateiname erstellen
        filename = f"Rechnung_{invoice.invoice_number}_{invoice.order.quote.customer.last_name}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Fehler beim Erstellen des PDFs: {str(e)}', 'error')
        return redirect(url_for('invoices'))

# ===============================
# STANDALONE BACKUP-FUNKTIONALITÄT
# ===============================

@app.route('/download_backup/<format>')
@login_required
def download_backup(format):
    """Standalone Backup Download - außerhalb der Haupt-App-Struktur"""
    from backup_system import DatabaseBackup
    from flask import send_file, flash, redirect, url_for
    
    try:
        backup_system = DatabaseBackup()
        
        if format == 'csv':
            buffer, filename = backup_system.create_csv_backup()
            mimetype = 'application/zip'
        elif format == 'excel':
            buffer, filename = backup_system.create_excel_backup()
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif format == 'sqlite':
            buffer, filename = backup_system.create_sqlite_backup()
            if buffer is None:
                flash('Datenbank-Datei konnte nicht gefunden werden!', 'error')
                return redirect(url_for('index'))
            mimetype = 'application/x-sqlite3'
        else:
            flash('Ungültiges Backup-Format!', 'error')
            return redirect(url_for('index'))
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        flash(f'Fehler beim Erstellen des Backups: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Cloud-Hosting-Erkennung
    is_production = bool(os.environ.get('DATABASE_URL'))
    
    # Admin-Initialisierung (Railway/Cloud & lokal)
    def ensure_admin():
        from models import LoginAdmin, db
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        existing_admin = LoginAdmin.query.filter_by(login_username=admin_username).first()
        if not existing_admin:
            admin = LoginAdmin.create_login_admin(admin_username, admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Admin-Benutzer initialisiert: {admin_username} / {admin_password}")
        else:
            # Im Entwicklungsmodus Passwort immer setzen
            if not is_production:
                existing_admin.set_login_password(admin_password)
                db.session.commit()
                print(f"✓ Admin-Passwort aktualisiert: {admin_username} / {admin_password}")
            else:
                print(f"✓ Admin-Benutzer vorhanden: {existing_admin.login_username}")

    if is_production:
        # Produktion: Einfacher Start ohne Browser-Öffnung
        with app.app_context():
            db.create_all()
            ensure_admin()
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
            ensure_admin()
            # Initialisiere Standard-Einstellungen falls nicht vorhanden
            if not CompanySettings.query.filter_by(setting_name='default_hourly_rate').first():
                CompanySettings.set_setting(
                    'default_hourly_rate', 
                    95.0,
                    'Standard-Stundensatz für Arbeitsvorgänge'
                )
                print("✓ Standard-Stundensatz initialisiert (95.00 €)")
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
                debug=False,  # Debug AUS für Produktion
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
