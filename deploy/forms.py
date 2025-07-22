"""
Formulare für die InstallationApp
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, DateField, SelectField, SubmitField, BooleanField, HiddenField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, NumberRange, Optional
from datetime import date, timedelta, datetime

class CustomerSearchField(StringField):
    """Custom Field für Kunden-Autocomplete"""
    pass

class CustomerForm(FlaskForm):
    salutation = StringField('Anrede', validators=[Optional()])
    first_name = StringField('Vorname *', validators=[DataRequired()])
    last_name = StringField('Nachname *', validators=[DataRequired()])
    email = StringField('E-Mail *', validators=[DataRequired(), Email()])
    phone = StringField('Telefon', validators=[Optional()])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Stadt', validators=[Optional()])
    postal_code = StringField('PLZ', validators=[Optional()])
    customer_manager = StringField('Kundenbetreuer', validators=[Optional()])
    acquisition_channel = SelectField('Akquisekanal', coerce=int, validators=[Optional()])
    comments = TextAreaField('Kommentare zum Kunden', validators=[Optional()])
    submit = SubmitField('Speichern')

class QuoteForm(FlaskForm):
    customer_search = CustomerSearchField('Kunde suchen *', 
                                        validators=[DataRequired()],
                                        render_kw={"placeholder": "Kundenname eingeben...", 
                                                  "autocomplete": "off"})
    customer_id = HiddenField('Customer ID', validators=[DataRequired()])
    project_description = TextAreaField('Projektbeschreibung *', validators=[DataRequired()])
    valid_until = DateField('Gültig bis', validators=[DataRequired()], 
                           default=lambda: date.today() + timedelta(days=90))
    include_additional_info = BooleanField('Zusätzliche Informationen einschließen', default=True)
    markup_percentage = FloatField('Aufschlag (%)', validators=[DataRequired(), NumberRange(min=0, max=100)], default=15.0)
    submit = SubmitField('Angebot erstellen')

class QuoteItemForm(FlaskForm):
    quantity = FloatField('Menge', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    description = TextAreaField('Beschreibung', validators=[DataRequired()])
    submit = SubmitField('Speichern')

class SupplierForm(FlaskForm):
    name = StringField('Firmenname *', validators=[DataRequired()])
    contact_person = StringField('Ansprechpartner', validators=[Optional()])
    email = StringField('E-Mail', validators=[Optional(), Email(message='Ungültige E-Mail-Adresse')])
    phone = StringField('Telefon', validators=[Optional()])
    address = TextAreaField('Adresse', validators=[Optional()])
    category = StringField('Kategorie', validators=[Optional()])
    notes = TextAreaField('Notizen', validators=[Optional()])
    submit = SubmitField('Speichern')

class SettingsForm(FlaskForm):
    default_hourly_rate = FloatField('Standard-Stundensatz (€)', 
                                   validators=[DataRequired(), NumberRange(min=0.1)], 
                                   default=95.0)
    submit = SubmitField('Speichern')

class QuoteRejectionForm(FlaskForm):
    rejection_reason = TextAreaField('Grund der Ablehnung *', 
                                   validators=[DataRequired()],
                                   render_kw={"rows": 4, "placeholder": "Bitte geben Sie den Grund für die Ablehnung an..."})
    submit = SubmitField('Ablehnung bestätigen')

class SupplierOrderUpdateForm(FlaskForm):
    confirmation_date = DateField('Bestätigungsdatum', validators=[Optional()])
    delivery_date = DateField('Liefertermin', validators=[Optional()])
    notes = TextAreaField('Notizen', validators=[Optional()],
                         render_kw={"rows": 3, "placeholder": "Zusätzliche Informationen zur Bestellung..."})
    status = SelectField('Status', choices=[
        ('Noch nicht bestellt', 'Noch nicht bestellt'),
        ('Bestellt', 'Bestellt'),
        ('Bestätigt', 'Bestätigt'),
        ('Geliefert', 'Geliefert')
    ], validators=[DataRequired()])
    submit = SubmitField('Bestellung aktualisieren')

class OrderForm(FlaskForm):
    start_date = DateField('Projektstart', validators=[], 
                          default=lambda: date.today() + timedelta(days=7))
    end_date = DateField('Projektende', validators=[],
                        default=lambda: date.today() + timedelta(days=21))
    project_manager = StringField('Projektleiter', validators=[Optional()],
                                 default='Michael Holasek')
    notes = TextAreaField('Projektnotizen', validators=[Optional()],
                         render_kw={"rows": 4, "placeholder": "Besondere Anweisungen oder Hinweise für die Ausführung..."})
    submit = SubmitField('Auftrag erstellen')

class OrderUpdateForm(FlaskForm):
    start_date = DateField('Projektstart', validators=[])
    end_date = DateField('Projektende', validators=[])
    project_manager = StringField('Projektleiter', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Geplant', 'Geplant'),
        ('In Arbeit', 'In Arbeit'),
        ('Abgeschlossen', 'Abgeschlossen'),
        ('Storniert', 'Storniert')
    ], validators=[DataRequired()])
    notes = TextAreaField('Projektnotizen', validators=[Optional()],
                         render_kw={"rows": 4})
    submit = SubmitField('Auftrag aktualisieren')

class AcquisitionChannelForm(FlaskForm):
    name = StringField('Name *', validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[Optional()])
    is_active = BooleanField('Aktiv', default=True)
    submit = SubmitField('Speichern')

class CustomerWorkflowForm(FlaskForm):
    """Form für Workflow-Updates des Kunden"""
    status = SelectField('Status', choices=[
        ('1. Termin vereinbaren', '1. Termin vereinbaren'),
        ('2. Termin vereinbart', '2. Termin vereinbart'),
        ('3. Angebot erstellen', '3. Angebot erstellen'),
        ('Angebot wurde erstellt', 'Angebot wurde erstellt'),
        ('Kein Interesse', 'Kein Interesse')
    ], validators=[DataRequired()])
    appointment_date = DateField('Termindatum', validators=[Optional()])
    appointment_notes = TextAreaField('Terminnotizen', validators=[Optional()])
    comments = TextAreaField('Kommentare zum Kunden', validators=[Optional()])
    submit = SubmitField('Status aktualisieren')

class AppointmentForm(FlaskForm):
    """Form für Terminvereinbarung"""
    appointment_date = DateField('Termindatum *', validators=[DataRequired()])
    appointment_notes = TextAreaField('Notizen zum Termin', validators=[Optional()], 
                                    render_kw={"placeholder": "Zusätzliche Informationen zum Termin..."})
    submit = SubmitField('Termin speichern')
