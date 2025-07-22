"""
PDF-Generator für Rechnungen mit speziellem Layout
Angepasst an InnSAN Corporate Design
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import black, darkgrey
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
from io import BytesIO
from datetime import datetime
import os
from models import CompanySettings

class InvoicePDFGenerator:
    def __init__(self):
        self.width, self.height = A4
        self.margin = 2 * cm
        self.content_width = self.width - 2 * self.margin
        
        # Header und Footer werden einmal initialisiert
        self.company_data = self._get_company_data()
        # Logo laden genau wie in pdf_export.py
        self.logo_path = os.path.join(os.path.dirname(__file__), 'innSAN_Logo.png')
        self.logo_element = None
        
        if os.path.exists(self.logo_path):
            try:
                # Logo mit angemessener Größe laden wie in pdf_export.py
                self.logo_element = Image(self.logo_path, width=4*cm, height=2*cm)
            except Exception as e:
                print(f"Fehler beim Laden des Logos: {e}")
                self.logo_element = None
        
    def generate_invoice_pdf(self, invoice):
        """Generiert eine PDF-Rechnung"""
        buffer = BytesIO()
        
        try:
            # PDF-Canvas erstellen
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Header zeichnen (Logo, Firmenname) - einmalig
            self._setup_header(c)
            
            # Rechnungsinformationen
            self.draw_invoice_info(c, invoice)
            
            # Kundeninformationen
            self.draw_customer_info(c, invoice)
            
            # Rechnungsbeträge (vereinfacht für Anzahlungen/Schlussrechnungen)
            self.draw_invoice_amounts(c, invoice)
            
            # Footer - einmalig
            self._setup_footer(c)
            
            c.save()
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            print(f"Fehler bei PDF-Generierung: {e}")
            # Fallback: Leeres PDF mit Fehlermeldung
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 750, f"Fehler bei der PDF-Generierung: {str(e)}")
            c.save()
            buffer.seek(0)
            return buffer
    
    def _setup_header(self, c):
        """Einmaliges Setup des PDF-Headers mit Logo und Zahlungsinfos"""
        # Logo oben links ohne schwarzen Hintergrund - genau wie in pdf_export.py
        if self.logo_element:
            try:
                # Logo direkt als Image-Element zeichnen
                self.logo_element.drawOn(c, self.margin, self.height - 3*cm)
            except Exception as e:
                print(f"Fehler beim Zeichnen des Logos: {e}")
        
        # Zahlungsinfos oben rechts in Schriftgröße 9
        c.setFont("Helvetica", 9)
        y_start = self.height - 1.5*cm
        
        payment_info = [
            "IBAN: AT21 3287 8000 0109 2301",
            "BIC: RLNWATWWBAD",
            "Bank: Raiffeisenbank",
            "UID: ATU61661106"
        ]
        
        for line in payment_info:
            c.drawRightString(self.width - self.margin, y_start, line)
            y_start -= 0.4*cm
    
    def draw_invoice_info(self, c, invoice):
        """Zeichnet die Rechnungsinformationen rechts oben"""
        y_start = self.height - 7*cm  # Von 6cm auf 7cm verschoben für mehr Abstand
        
        # Rechnungstitel groß und fett in Corporate Color
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.HexColor('#CC5500'))  # Corporate Orange
        invoice_title = self._get_invoice_title(invoice.invoice_type)
        c.drawRightString(self.width - self.margin, y_start, invoice_title)
        
        # Zurück zu schwarz für Details
        c.setFillColor(colors.black)
        
        # Rechnungsdetails rechts ausgerichtet - mit mehr Zeilenabstand
        y_pos = y_start - 1*cm
        c.setFont("Helvetica", 11)
        
        details = [
            f"Rechnungsnummer: {invoice.invoice_number}",
            f"Rechnungsdatum: {invoice.created_at.strftime('%d.%m.%Y')}",
            f"Fälligkeitsdatum: {invoice.due_date.strftime('%d.%m.%Y')}",
            f"Auftragsnummer: {invoice.order.order_number}",
        ]
        
        for detail in details:
            c.drawRightString(self.width - self.margin, y_pos, detail)
            y_pos -= 0.45*cm  # Erhöhter Zeilenabstand von 0.35 auf 0.45
    
    def draw_customer_info(self, c, invoice):
        """Zeichnet die Kundeninformationen im Adressfeld"""
        y_start = self.height - 6*cm
        customer = invoice.order.quote.customer
        
        # Firmenzeile oberhalb der Kundendaten in Schriftgröße 8
        c.setFont("Helvetica", 8)
        company_line = "InnSAN Fachbetrieb Ing. Michael Holasek | Hetzendorferstrasse 138/2/1B | 1120 Wien"
        c.drawString(self.margin, y_start + 0.5*cm, company_line)
        
        # Überschrift Rechnungsadresse
        c.setFont("Helvetica", 10)
        c.drawString(self.margin, y_start, "Rechnungsadresse:")
        
        # Linie unter Überschrift
        y_start -= 0.3*cm
        c.line(self.margin, y_start, self.margin + 6*cm, y_start)
        
        # Kundenadresse
        y_pos = y_start - 0.5*cm
        c.setFont("Helvetica", 11)
        
        address_lines = [
            customer.full_name or "",
            customer.address or "",
            f"{customer.postal_code or ''} {customer.city or ''}".strip()
        ]
        
        for line in address_lines:
            if line.strip():  # Nur nicht-leere Zeilen
                c.drawString(self.margin, y_pos, line)
                y_pos -= 0.5*cm
    
    def draw_invoice_amounts(self, c, invoice):
        """Zeichnet die Rechnungsbeträge mit verbessertem Layout"""
        y_start = self.height - 12*cm
        
        # Dankestext mit Angebotsnummer
        c.setFont("Helvetica", 10)
        quote_number = invoice.order.quote.quote_number
        thanks_text = [
            "Herzlichen Dank für Ihr Vertrauen in unsere Produkte. Wir erlauben uns folgende Beträge in Rechnung zu stellen",
            "und freuen uns, wenn wir auch in Zukunft für Sie tätig werden dürfen.",  
        ]
        
        y_pos = y_start
        for line in thanks_text:
            c.drawString(self.margin, y_pos, line)
            y_pos -= 0.4*cm
        
        y_pos -= 0.5*cm
        
        # Projektbeschreibung in Corporate Color
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#CC5500'))  # Corporate Orange
        c.drawString(self.margin, y_pos, "Leistungsbeschreibung:")
        c.setFillColor(colors.black)  # Zurück zu schwarz
        
        y_pos -= 0.7*cm
        c.setFont("Helvetica", 11)
        project_desc = invoice.order.quote.project_description or "Installationsarbeiten"
        
        # Projektbeschreibung anzeigen - Text umbrechen falls zu lang
        if len(project_desc) > 70:
            words = project_desc.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= 70:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
        else:
            lines = [project_desc]
        
        # Projektbeschreibung zeichnen
        for line in lines:
            c.drawString(self.margin, y_pos, line)
            y_pos -= 0.5*cm
        
        # Angebotsnummer unter der Projektbeschreibung hinzufügen
        y_pos -= 0.3*cm
        angebots_text = f'Verrechnung gemäß Angebot: "{quote_number}"'
        c.drawString(self.margin, y_pos, angebots_text)
        y_pos -= 0.5*cm
        
        # Beträge-Tabelle
        y_pos -= 1*cm
        
        # Tabellenkopf in Corporate Color
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#CC5500'))  # Corporate Orange
        c.drawString(self.margin, y_pos, "Position")
        c.drawRightString(self.width - self.margin, y_pos, "Betrag")
        c.setFillColor(colors.black)  # Zurück zu schwarz
        
        y_pos -= 0.3*cm
        c.setStrokeColor(colors.HexColor('#CC5500'))  # Corporate Orange für Linie
        c.line(self.margin, y_pos, self.width - self.margin, y_pos)
        c.setStrokeColor(colors.black)  # Zurück zu schwarz
        y_pos -= 0.5*cm
        
        # Beträge
        c.setFont("Helvetica", 11)
        
        rows = [
            (f"Auftragssumme netto", f"{invoice.base_amount:.2f} €")
                    ]
        
        # Abzug bei Schlussrechnung
        if invoice.invoice_type == 'schluss' and invoice.previous_payments > 0:
            rows.append(("Abzüglich bereits erhaltener Anzahlungen (netto)", f"- {invoice.previous_payments:.2f} €"))
        
        for desc, amount in rows:
            c.drawString(self.margin, y_pos, desc)
            c.drawRightString(self.width - self.margin, y_pos, amount)
            y_pos -= 0.5*cm
        
        # Linie vor Zwischensumme/Restbetrag
        y_pos -= 0.2*cm
        c.line(self.margin + 8*cm, y_pos, self.width - self.margin, y_pos)
        y_pos -= 0.5*cm
        
        # Zwischensumme/Restbetrag je nach Rechnungstyp
        c.setFont("Helvetica-Bold", 11)
        if invoice.invoice_type == 'anzahlung':
            # Bei Anzahlungen: Anzahlungssumme
            c.drawString(self.margin, y_pos, f"Anzahlungssumme netto ({invoice.percentage:.0f}%):")
            c.drawRightString(self.width - self.margin, y_pos, f"{invoice.final_amount:.2f} €")
        elif invoice.invoice_type == 'schluss':
            # Bei Schlussrechnungen: Restbetrag (Auftragssumme - Anzahlungen)
            restbetrag = invoice.base_amount - invoice.previous_payments
            c.drawString(self.margin, y_pos, "Restbetrag netto:")
            c.drawRightString(self.width - self.margin, y_pos, f"{restbetrag:.2f} €")
        else:
            # Standard für andere Rechnungstypen
            c.drawString(self.margin, y_pos, "Zwischensumme netto:")
            c.drawRightString(self.width - self.margin, y_pos, f"{invoice.final_amount:.2f} €")
        y_pos -= 0.5*cm
        
        # MwSt
        c.setFont("Helvetica", 11)
        c.drawString(self.margin, y_pos, f"zzgl. {invoice.vat_rate:.0f}% MwSt.:")
        if invoice.invoice_type == 'schluss':
            # Bei Schlussrechnungen: MwSt vom Restbetrag berechnen
            restbetrag = invoice.base_amount - invoice.previous_payments
            vat_amount = restbetrag * invoice.vat_rate / 100
            c.drawRightString(self.width - self.margin, y_pos, f"{vat_amount:.2f} €")
        else:
            c.drawRightString(self.width - self.margin, y_pos, f"{invoice.vat_amount:.2f} €")
        y_pos -= 0.5*cm
        
        # Gesamtsumme
        y_pos -= 0.2*cm
        c.line(self.margin + 8*cm, y_pos, self.width - self.margin, y_pos)
        y_pos -= 0.5*cm
        
        c.setFont("Helvetica-Bold", 14)
        if invoice.invoice_type == 'anzahlung':
            c.drawString(self.margin, y_pos, "Anzahlungssumme brutto:")
            c.drawRightString(self.width - self.margin, y_pos, f"{invoice.gross_amount:.2f} €")
        elif invoice.invoice_type == 'schluss':
            # Bei Schlussrechnungen: Restbetrag + MwSt berechnen
            restbetrag = invoice.base_amount - invoice.previous_payments
            restbetrag_brutto = restbetrag + (restbetrag * invoice.vat_rate / 100)
            c.drawString(self.margin, y_pos, "Gesamtsumme brutto:")
            c.drawRightString(self.width - self.margin, y_pos, f"{restbetrag_brutto:.2f} €")
        else:
            c.drawString(self.margin, y_pos, "Gesamtsumme brutto:")
            c.drawRightString(self.width - self.margin, y_pos, f"{invoice.gross_amount:.2f} €")
        
        # Abschlusstext vor Zahlungsbedingungen
        y_pos -= 2*cm
        c.setFont("Helvetica", 10)
        closing_text = [
            "Wir hoffen, den Auftrag zu Ihrer Zufriedenheit ausgeführt zu haben und verbleiben",
            "mit freundlichen Grüßen,",
            "Ihr InnSAN Team"
        ]
        
        for line in closing_text:
            c.drawString(self.margin, y_pos, line)
            y_pos -= 0.5*cm
        
        # Neue Seite für Zahlungsbedingungen und Datenschutz
        c.showPage()
        
        # Header auf neuer Seite
        self._setup_header(c)
        
        # Zahlungsbedingungen auf neuer Seite
        y_pos = self.height - 6*cm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#CC5500'))  # Corporate Orange
        c.drawString(self.margin, y_pos, "Zahlungsbedingungen")
        c.setFillColor(colors.black)  # Zurück zu schwarz
        
        y_pos -= 0.8*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.margin, y_pos, "Zahlungskondition:")
        y_pos -= 0.4*cm
        c.setFont("Helvetica", 10)
        c.drawString(self.margin, y_pos, "Fällig bei Erhalt der Rechnung. Netto ohne Abzüge.")
        
        y_pos -= 1*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.margin, y_pos, "Hinweis Datenschutz und Datenspeicherung:")
        
        y_pos -= 0.5*cm
        c.setFont("Helvetica", 9)
        datenschutz_text = [
            "Wir weisen darauf hin, dass zum Zweck der Vertragsabwicklung folgende Daten bei uns gespeichert werden:",
            "Name, Vorname, Anschrift, Telefonnummer und ggf. Email-Adresse.",
            "",
            "Die von Ihnen bereit gestellten Daten sind zur Vertragserfüllung bzw. zur Durchführung vorvertraglicher",
            "Maßnahmen erforderlich. Ohne diese Daten können wir den Vertrag mit Ihnen nicht abschließen. Eine",
            "Datenübermittlung an Dritte erfolgt nicht, mit Ausnahme von den von uns beauftragten Lieferanten zum Zwecke",
            "der Bestellabwicklung, an das von uns beauftragte Transportunternehmen zur Zustellung der Ware sowie an unseren",
            "Steuerberater zur Erfüllung unserer steuerrechtlichen Verpflichtungen.",
            "",
            "Nach Abbruch des Auftragvorgangs, werden die bei uns gespeicherten Daten gelöscht. Im Falle eines",
            "Vertragsabschlusses werden sämtliche Daten aus dem Vertragsverhältnis bis zum Ablauf der steuerrechtlichen",
            "Aufbewahrungsfrist (7 Jahre) gespeichert.",
            "",
            "Die Daten Name, Anschrift, gekaufte Waren und Kaufdatum werden darüber hinaus gehend bis zum Ablauf der",
            "Produkthaftung (10 Jahre) gespeichert.",
            "",
            "Im Falle einer Zustimmung zur Verwendung von Fotomaterial, wird dieses bis auf Widerruf bei uns anonym",
            "abgespeichert.",
            "",
            "Die Datenverarbeitung erfolgt auf Basis der gesetzlichen Bestimmungen der DSGVO."
        ]
        
        for line in datenschutz_text:
            c.drawString(self.margin, y_pos, line)
            y_pos -= 0.35*cm
            # Prüfen ob noch Platz auf der Seite ist
            if y_pos < 3*cm:
                c.showPage()
                self._setup_header(c)
                y_pos = self.height - 6*cm
    
    def _setup_footer(self, c):
        """Dreispaltiger Footer mit Firmeninfos, Bankdaten und Rechtsinformationen"""
        footer_y = 2.5*cm
        c.setFont("Helvetica", 8)
        
        # Spalte 1: Firmeninformationen (links)
        company_info = [
            "InnSan Ing. Michael Holasek e.U.",
            "Hetzendorferstrasse 138/2/1B",
            "1120 Wien",
            "Tel: +43 699 114 88 772",
            "E-Mail: michael.holasek@innsan.at"
        ]
        
        for i, line in enumerate(company_info):
            c.drawString(self.margin, footer_y - i * 0.3*cm, line)
        
        # Spalte 2: Bankdaten (mitte)
        col2_x = self.margin + 7*cm
        bank_info = [
            "Bankverbindung:",
            "IBAN: AT21 3287 8000 0109 2301",
            "BIC: RLNWATWWBAD",
            "Raiffeisenbank Leopoldsdorf"
        ]
        
        for i, line in enumerate(bank_info):
            c.drawString(col2_x, footer_y - i * 0.3*cm, line)
        
        # Spalte 3: Rechtsinformationen (rechts)
        col3_x = self.margin + 14*cm
        legal_info = [
            "Rechtsinformationen:",
            "UID: ATU61661106",
            "Handelsgericht Leopoldsdorf",
            "Gewerbeschein: Installateur"
        ]
        
        for i, line in enumerate(legal_info):
            c.drawString(col3_x, footer_y - i * 0.3*cm, line)
    
    def _get_company_data(self):
        """Lädt Firmendaten aus den Einstellungen"""
        try:
            settings = CompanySettings.get_all_settings()
            return [
                settings.get('company_address', 'Hetzendorferstrasse 138/2/1B'),
                settings.get('company_city', '1120 Wien'),
                f"Tel: {settings.get('company_phone', '+43 699 114 88 772')}",
                f"E-Mail: {settings.get('company_email', 'michael.holasek@innsan.at')}"
            ]
        except:
            return [
                "Hetzendorferstrasse 138/2/1B",
                "1120 Wien", 
                "Tel: +43 699 114 88 772",
                "E-Mail: michael.holasek@innsan.at"
            ]
    
    def _get_invoice_title(self, invoice_type):
        """Gibt den passenden Rechnungstitel zurück"""
        titles = {
            'anzahlung': 'ANZAHLUNG',
            'zwischen': 'ZWISCHENRECHNUNG', 
            'schluss': 'SCHLUSSRECHNUNG'
        }
        return titles.get(invoice_type, 'RECHNUNG')
    
    def _get_invoice_type_desc(self, invoice_type):
        """Gibt die Beschreibung des Rechnungstyps zurück"""
        descriptions = {
            'anzahlung': 'Anzahlung',
            'zwischen': 'Zwischenrechnung',
            'schluss': 'Schlussrechnung'
        }
        return descriptions.get(invoice_type, 'Rechnung')
