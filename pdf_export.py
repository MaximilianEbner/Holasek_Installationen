"""
PDF-Export-Funktionen für Angebote
"""
from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from io import BytesIO
from models import Quote
import os
import json
from pypdf import PdfWriter, PdfReader
from utils import format_currency_de

class PDFExporter:
    """Klasse für PDF-Export von Angeboten"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Erstellt benutzerdefinierte Styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle', 
            parent=self.styles['Heading1'], 
            fontSize=24, 
            textColor=colors.HexColor('#CC5500')
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading', 
            parent=self.styles['Heading2'], 
            fontSize=14, 
            textColor=colors.HexColor('#CC5500')
        )
        
        self.small_style = ParagraphStyle(
            'Small', 
            parent=self.styles['Normal'], 
            fontSize=8
        )
        
        self.right_style = ParagraphStyle(
            'Right', 
            parent=self.styles['Normal'], 
            alignment=TA_RIGHT
        )
    
    def _wrap_text_for_table(self, text, max_width=None):
        """Umbruch von langem Text für Tabellenzellen mit Paragraph-Objekten"""
        if not text:
            return "-"
        
        # Teile Text an Zeilenumbrüchen auf
        lines = str(text).split('\n')
        paragraphs = []
        
        for line in lines:
            if line.strip():
                # Lange Zeilen automatisch umbrechen
                if len(line) > 40:  # Threshold für automatischen Umbruch
                    # Einfacher Umbruch bei Leerzeichen
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + word) > 40:
                            if current_line:
                                paragraphs.append(Paragraph(current_line.strip(), self.styles['Normal']))
                            current_line = word + " "
                        else:
                            current_line += word + " "
                    if current_line:
                        paragraphs.append(Paragraph(current_line.strip(), self.styles['Normal']))
                else:
                    paragraphs.append(Paragraph(line, self.styles['Normal']))
            else:
                paragraphs.append(Paragraph(" ", self.styles['Normal']))  # Leere Zeile
        
        return paragraphs if len(paragraphs) > 1 else (paragraphs[0] if paragraphs else Paragraph("-", self.styles['Normal']))
    
    def export_quote(self, quote_id):
        """Exportiert ein Angebot als PDF"""
        quote = Quote.query.get_or_404(quote_id)
        
        # PDF in Memory erstellen
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=2*cm, 
            leftMargin=2*cm, 
            topMargin=2*cm, 
            bottomMargin=2*cm
        )
        
        # Story (Inhalt) aufbauen
        story = []
        
        # Header
        story.extend(self._build_header())
        
        # Angebot Title
        story.append(Paragraph("ANGEBOT", self.title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Angebotsdaten
        story.extend(self._build_quote_info(quote))
        
        # Kunde
        story.extend(self._build_customer_info(quote))
        
        # Projektbeschreibung
        story.extend(self._build_project_description(quote))
        
        # Positionen
        story.extend(self._build_positions(quote))
        
        # Preissummen
        story.extend(self._build_price_summary(quote))
        
        # Zusätzliche Informationen
        if quote.include_additional_info:
            story.extend(self._build_additional_info(quote))
        
        # Zahlungsbedingungen und AGB
        story.extend(self._build_terms_and_conditions())
        
        # Unterschriftsfeld
        story.extend(self._build_signature_field(quote))
        
        # PDF generieren
        doc.build(story)
        buffer.seek(0)
        
        filename = f"Angebot_{quote.quote_number}.pdf"
        
        return send_file(
            BytesIO(buffer.read()),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    def _build_header(self):
        """Erstellt den Header mit Logo und Firmeninformationen"""
        header_elements = []
        
        # Logo laden
        logo_path = os.path.join(os.path.dirname(__file__), 'innSAN_Logo.png')
        logo_element = None
        
        if os.path.exists(logo_path):
            try:
                # Logo mit korrektem Seitenverhältnis (624x222 Pixel = 2.81:1)
                logo_width = 6*cm
                logo_height = logo_width / 2.81  # Berechne Höhe basierend auf Original-Seitenverhältnis
                logo_element = Image(logo_path, width=logo_width, height=logo_height)
            except Exception as e:
                print(f"Fehler beim Laden des Logos: {e}")
                logo_element = None
        
        # Header-Tabelle mit Logo und Firmendaten
        if logo_element:
            header_data = [
                [logo_element, 'Ing. Michael Holasek'],
                ['', 'Hetzendorferstrasse 138/2/1B'],
                ['', '1120 Wien'],
                ['', ''],
                ['', 'Ihr Ansprechpartner:'],
                ['', 'Michael Holasek'],
                ['', 'Tel1: +43 (0)664 - 4793530'],
                ['', 'Tel2: (+43) 03134 35900 - Zentrale'],
                ['', 'Mail: michael.holasek@innsan.at']
            ]
            
            header_table = Table(header_data, colWidths=[6*cm, 11*cm])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Logo links
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Text rechts
                ('VALIGN', (0, 0), (0, 0), 'TOP'),   # Logo oben
                ('VALIGN', (1, 0), (1, -1), 'TOP'),  # Text oben
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, -1), 10),
                ('BOTTOMPADDING', (1, 0), (1, -1), 2),
                ('TOPPADDING', (1, 0), (1, -1), 2),
                ('SPAN', (0, 0), (0, 3)),  # Logo über mehrere Zeilen
            ]))
        else:
            # Fallback ohne Logo
            header_data = [
                ['innSAN', 'Ing. Michael Holasek'],
                ['', 'Hetzendorferstrasse 138/2/1B'],
                ['', '1120 Wien'],
                ['', ''],
                ['', 'Ihr Ansprechpartner:'],
                ['', 'Michael Holasek'],
                ['', 'Tel1: +43 (0)664 - 4793530'],
                ['', 'Tel2: (+43) 03134 35900 - Zentrale'],
                ['', 'Mail: michael.holasek@innsan.at']
            ]
            
            header_table = Table(header_data, colWidths=[6*cm, 11*cm])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
        
        return [header_table, Spacer(1, 1*cm)]
    
    def _build_quote_info(self, quote):
        """Erstellt die Angebotsinformationen"""
        angebot_data = [
            ['Angebotsnummer:', quote.quote_number],
            ['Datum:', quote.created_at.strftime('%d.%m.%Y')],
            ['Gültig bis:', quote.valid_until.strftime('%d.%m.%Y')]
        ]
        
        angebot_table = Table(angebot_data, colWidths=[4*cm, 6*cm])
        angebot_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return [angebot_table, Spacer(1, 1*cm)]
    
    def _build_customer_info(self, quote):
        """Erstellt die Kundeninformationen"""
        customer_text = f"{quote.customer.full_name}<br/>{quote.customer.email}"
        if quote.customer.phone:
            customer_text += f"<br/>{quote.customer.phone}"
        if quote.customer.address:
            customer_text += f"<br/>{quote.customer.address}<br/>{quote.customer.postal_code} {quote.customer.city}"
        
        return [
            Paragraph("Kunde:", self.heading_style),
            Paragraph(customer_text, self.styles['Normal']),
            Spacer(1, 0.5*cm)
        ]
    
    def _build_project_description(self, quote):
        """Erstellt die Projektbeschreibung"""
        return [
            Paragraph("Projektbeschreibung:", self.heading_style),
            Paragraph(quote.project_description, self.styles['Normal']),
            Spacer(1, 0.5*cm)
        ]
    
    def _build_positions(self, quote):
        """Erstellt die Positionen des Angebots"""
        elements = [
            Paragraph("Leistungen:", self.heading_style),
            Spacer(1, 0.3*cm)
        ]
        
        # Styles für Positionen
        main_pos_style = ParagraphStyle(
            'MainPosition',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceBefore=6,
            spaceAfter=3
        )
        
        price_style = ParagraphStyle(
            'Price',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            alignment=TA_RIGHT
        )
        
        for i, item in enumerate(quote.quote_items, 1):
            pos_number = item.position_number or i
            
            # Bestimme Preisanzeigemodus
            display_mode = getattr(quote, 'price_display_mode', 'standard')
            if display_mode == 'standard' and getattr(quote, 'show_subitem_prices', False):
                # Kompatibilität: Wenn alte Checkbox aktiviert war, verwende 'detailed' Modus
                display_mode = 'detailed'
            
            # Hauptposition
            pos_title = f"Position {pos_number}: {item.description}"
            
            if display_mode == 'total_only':
                # Nur Gesamtbetrag Modus: Keine einzelnen Positionspreise anzeigen
                main_pos_data = [[Paragraph(pos_title, main_pos_style), ""]]
            else:
                # Standard/Detailed Modus: Positionspreise mit Aufschlag anzeigen
                pos_price = format_currency_de(item.calculate_price_with_markup())
                main_pos_data = [[Paragraph(pos_title, main_pos_style), Paragraph(pos_price, price_style)]]
            main_pos_table = Table(main_pos_data, colWidths=[13*cm, 4*cm])
            main_pos_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#CC5500')),
            ]))
            elements.append(main_pos_table)
            
            # Unterpositionen - immer anzeigen (außer wenn keine vorhanden)
            if item.sub_items:
                sub_style = ParagraphStyle(
                    'SubItem',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    leftIndent=20,
                    spaceBefore=2,
                    spaceAfter=2
                )
                
                sub_price_style = ParagraphStyle(
                    'SubPrice',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    alignment=TA_RIGHT
                )
                
                for sub_item in item.sub_items:
                    # Bestimme Preisanzeigemodus (Rückwärtskompatibilität mit show_subitem_prices)
                    display_mode = getattr(quote, 'price_display_mode', 'standard')
                    if display_mode == 'standard' and getattr(quote, 'show_subitem_prices', False):
                        # Kompatibilität: Wenn alte Checkbox aktiviert war, verwende 'detailed' Modus
                        display_mode = 'detailed'
                    
                    if display_mode == 'detailed' and sub_item.price > 0:
                        # Detailliert: Zeige Unterpositionspreise mit Aufschlag - rechtsbündig
                        sub_price_with_markup = sub_item.calculate_price_with_markup()
                        sub_text = f"{sub_item.sub_number} {sub_item.description}"
                        sub_price_text = format_currency_de(sub_price_with_markup)
                        
                        # Tabelle für rechtsbündige Preisanzeige
                        sub_data = [[Paragraph(sub_text, sub_style), Paragraph(sub_price_text, sub_price_style)]]
                        sub_table = Table(sub_data, colWidths=[13*cm, 4*cm])
                        sub_table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ]))
                        elements.append(sub_table)
                    else:
                        # Standard und Total_only: Keine Preise für Unterpositionen
                        sub_text = f"{sub_item.sub_number} {sub_item.description}"
                        elements.append(Paragraph(sub_text, sub_style))
            
            elements.append(Spacer(1, 0.4*cm))
        
        return elements
    
    def _build_price_summary(self, quote):
        """Erstellt die Preiszusammenfassung"""
        netto_summe = quote.total_amount or 0
        ust_betrag = netto_summe * 0.20  # 20% USt
        brutto_summe = netto_summe + ust_betrag
        
        # Hinweis zu Netto-Preisen
        netto_note_style = ParagraphStyle(
            'NettoNote',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            alignment=TA_RIGHT,
            spaceBefore=10,
            spaceAfter=10
        )
        
        elements = [
            Paragraph("Alle angegebenen Preise verstehen sich als Nettopreise.", netto_note_style)
        ]
        
        # Preisaufschlüsselung
        price_data = [
            ['', 'Summe Netto:', format_currency_de(netto_summe)],
            ['', 'USt 20%:', format_currency_de(ust_betrag)],
            ['', 'Gesamtsumme (Brutto):', format_currency_de(brutto_summe)]
        ]
        
        price_table = Table(price_data, colWidths=[6*cm, 7*cm, 4*cm])
        price_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTSIZE', (1, 0), (2, 1), 12),
            ('FONTNAME', (1, 0), (2, 1), 'Helvetica'),
            ('FONTSIZE', (1, 2), (2, 2), 12),
            ('FONTNAME', (1, 2), (2, 2), 'Helvetica-Bold'),
            ('LINEABOVE', (1, 2), (2, 2), 1, colors.black),
            ('BACKGROUND', (1, 2), (2, 2), colors.HexColor('#fff3e6')),
            ('BOTTOMPADDING', (1, 0), (-1, -1), 6),
            ('TOPPADDING', (1, 0), (-1, -1), 6),
            ('TOPPADDING', (1, 2), (2, 2), 10),
            ('BOTTOMPADDING', (1, 2), (2, 2), 10),
        ]))
        
        elements.extend([price_table, Spacer(1, 0.5*cm)])
        
        return elements
    
    def _build_additional_info(self, quote):
        """Erstellt zusätzliche Informationen basierend auf Quote-Daten"""
        elements = [
            Paragraph("Wir bedanken uns für Ihr Vertrauen und bieten Ihnen folgenden Leistungsumfang:", self.small_style)
        ]
        
        # Leistungsumfang
        if quote.leistungsumfang and quote.leistungsumfang != '<keine>':
            leistungsumfang_html = quote.leistungsumfang.replace('\n', '<br/>')
            elements.extend([
                Paragraph(leistungsumfang_html, self.small_style),
                Spacer(1, 0.3*cm)
            ])
        else:
            # Fallback auf Default-Text oder leer lassen wenn "<keine>"
            if not quote.leistungsumfang or quote.leistungsumfang == '<keine>':
                # Feld ist leer - nichts anzeigen oder Platzhalter
                pass
            else:
                default_leistung = """
• Demontage der bestehenden Produkte inklusive Entsorgung<br/>
• Montage der im Angebot angeführten Produkte<br/>
• Anschluss an bestehendes Gebäudeleitungssystem im unmittelbaren Umbaubereich ab Badezimmer oder in der Dusche<br/>
• Diverse Ausgleichs- und Abdichtungsarbeiten<br/>
                """
                elements.extend([
                    Paragraph(default_leistung, self.small_style),
                    Spacer(1, 0.3*cm)
                ])
        
        # Informationen zum Objekt
        if quote.objektinformationen and quote.objektinformationen != '<keine>':
            elements.append(Paragraph("<b>Informationen zum Objekt:</b><br/>", self.small_style))
            objektinfo_html = quote.objektinformationen.replace('\n', '<br/>')
            elements.extend([
                Paragraph(objektinfo_html, self.small_style),
                Spacer(1, 0.3*cm)
            ])
        elif quote.objektinformationen != '<keine>':
            # Nur Default-Text anzeigen wenn nicht explizit als "<keine>" markiert
            default_objekt = """
<b>Informationen zum Objekt:</b><br/>
• Einfamilienhaus<br/>
• Zuschnitt vor dem Gebäude möglich<br/>
• Parken vor dem Gebäude möglich<br/>
            """
            elements.extend([
                Paragraph(default_objekt, self.small_style),
                Spacer(1, 0.3*cm)
            ])
        
        # Installationsleistungen
        if quote.installationsleistungen and quote.installationsleistungen != '<keine>':
            elements.append(Paragraph("<b>Installationsleistungen:</b><br/>", self.small_style))
            installations_html = quote.installationsleistungen.replace('\n', '<br/>')
            elements.extend([
                Paragraph(installations_html, self.small_style),
                Spacer(1, 0.5*cm)
            ])
        elif quote.installationsleistungen != '<keine>':
            # Nur Default-Text anzeigen wenn nicht explizit als "<keine>" markiert
            default_installation = """
<b>Installationsleistungen:</b><br/>
• Abfluss Dusche herrichten<br/>
• Armatur Dusche versetzen<br/><br/>

<b>Nebenabsprache mit dem Kunden:</b><br/>
• Demontage, Vorbereitung und Entsorgung erfolgt durch Innsan<br/>
            """
            elements.extend([
                Paragraph(default_installation, self.small_style),
                Spacer(1, 0.5*cm)
            ])
        
        return elements
    
    def _build_terms_and_conditions(self):
        """Erstellt Zahlungsbedingungen und AGB"""
        elements = [
            Paragraph("Das Angebot hat eine Preisgültigkeit von 90 Tagen ab Ausstellungsdatum", self.styles['Normal']),
            Paragraph("30 % Anzahlung vom Gesamtbetrag nach Auftragserteilung, Restzahlung fällig bei Erhalt der Rechnung, ohne Skonto", self.styles['Normal']),
            Spacer(1, 0.5*cm),
            Paragraph("Allgemeine Geschäftsbedingungen:", self.heading_style)
        ]
        
        # Vollständige AGBs
        agb_text = """
<b>1.) Hinweis Niveauunterschied:</b> Je nach Bad kann eine unterschiedlich geringe Schwelle zwischen Boden und der Duschtasse (Eintrittshöhe) verbleiben, welche das bestehende Abflussniveau vorgibt und unter Einhaltung eines normgerechten Gefälles. Wir versuchen die Duschtassen so tief wie möglich (barrierefrei) zu montieren. Ein fachgerechtes/funktionierendes Bestandssystem, wo darauf angeschlossen wird, wird vorausgesetzt (zB.: Abflußstrangentlüftung, Abflußgefälle, freie Abwasserrohre etc.).<br/><br/>

<b>2.) Hinweis zusätzliche Kosten</b><br/>
a) bei versteckten Mängeln / unvorhersehbaren Gegebenheiten im Zuge des Umbaus: Ein funktionstüchtiges Bestandssystem sowie passender, tragfähiger Untergrund wird vorausgesetzt. Sollten im Zuge der Umbau-/Demontagearbeiten Unwägbarkeiten oder versteckte Mängel (zB. Feuchtigkeitsprobleme, hohle Verfliesung u.ä.) zum Vorschein kommen, werden nötige Zusatzarbeiten (Arbeitszeit und Materialien) auf Regie verrechnet. Der Regiestundensatz beträgt pro Person und Stunde 95 EUR exkl. MwSt., zuzüglich Kosten für das benötigte Material.<br/>
b) zusätzliche Leistungen (Arbeiten und Materialien), die in diesem Pauschalpreis bzw. nicht im Auftragstext enthalten/angeführt sind, jedoch im Zuge des Umbaus vom Kunden gewünscht werden, werden bei Schlussrechnung zusätzlich zur Auftragssumme abgerechnet, da diese im ursprünglichen Auftrag keine Deckung finden.<br/><br/>

<b>3.) Beigestellte Waren</b><br/>
Für vom Kunden bereitgestellte Geräte/Produkte/sonstige Materialien oder daraus entstehende Schäden, wird keine Gewährleistung/Garantie oder sonstige Haftung übernommen. Die Qualität und Betriebsbereitschaft von Beistellungen liegt in der Verantwortung des Kunden. Natürlich haften wir für die ordnungsgemäße Durchführung der Installationsarbeiten, mit welchen wir durch den Kunden betraut wurden. Davon ausgenommen ist allerding, wenn unser Werk aufgrund der von Kunden beigestellten Ware misslingt. Wir warnen auch, wenn im konkreten Fall die von Ihnen beigestellten Produkte offenbar untauglich sind, sodass dies die vertragsgemäße Herstellung der beauftragten Installation hindert. Wünschen Sie diese Installation dennoch und misslingt sie aus den Gründen, vor welchen wir gewarnt haben, bleibt unser Entgeltanspruch unberührt. Ebenso sind Schadenersatz- und Gewährleistungsansprüche beschränkt, soweit Mängel und Schäden auf Ihre Wünsche oder Vorgaben zurückzuführen sind.<br/><br/>

<b>4.) Bestand- und Altbestand, De- und Neumontage</b><br/>
Für bestehende/vorhandene Geräte/Produkte (zB. Waschbecken, Duschabtrennungen, Ablagen uvm.), welche wieder montiert werden sollen, wird im Zuge der Demontage keine Haftung in Bezug auf Bruch oder Beschädigungen übernommen. Demontierte Gegenstände, die keine Wiederverwendung finden, werden entsorgt, sofern bei Umbaubeginn seitens des Kunden keine ausdrückliche Weisung erfolgt. Weiters können im Rahmen von Montage- und Instandsetzungsarbeiten Schäden an bereits vorhandenen Leitungen, Rohrleitungen, Armaturen, sanitären Einrichtungsgegenständen und Geräten als Folge nicht erkennbarer Gegebenheiten oder Materialfehler, sowie Schäden bei Stemmarbeiten in bindungslosem Mauerwerk, entstehen. Solche Schäden sind von uns nur zu verantworten, wenn wir diese mutwillig verursacht haben. Bei behelfsmäßigen Instandsetzungen besteht lediglich eine sehr beschränkte und den Umständen entsprechende Haltbarkeit und beschränkt sich die Gewährleistungspflicht auf die unsererseits verbauten Materialien.<br/><br/>

<b>5.) Lieferverzögerung, Nach- oder Ausbesserungsarbeiten</b><br/>
Sollten wider Erwarten Lieferverzögerungen, Nach- oder Ausbesserungsarbeiten notwendig sein, steht dem Kunden das Recht zu, einstweilen 50% vom Betrag der betreffenden Auftragsposition einzubehalten. Dieser wird jedoch umgehend nach Nachlieferung oder Ausbesserung zur Zahlung fällig. Es wird die Möglichkeit der uneingeschränkten Nachbesserung bis zur Abnahme des Kunden vereinbart. Preisnachlässe sind aufgrund von Lieferverzögerungen, Nach- oder Ausbesserungsarbeiten nicht gestattet.<br/><br/>

<b>6.) Zahlung</b><br/>
Eine Anzahlung wird nach Vertragsabschluss und nach Erhalt der Anzahlungsrechnung fällig. Je nach Leistungsfertigstellung können Teilrechnungen zur Zahlung fällig werden. Die Berechtigung auf einen Skontoabzug wird nicht gestattet. Im Falle eines Zahlungsverzugs werden 4% Verzugszinsen berechnet.<br/><br/>

<b>7.) Mitwirkungspflichten des Kunden</b><br/>
Der Kunde hat vor Beginn der Leistungsausführung die nötigen Angaben über die Lage verdeckt geführter Strom, Gas- und Wasserleitungen oder ähnlicher Vorrichtungen den Monteuren mitzuteilen. Die für die Leistungsausführung erforderliche Energie- und Wassermengen sind vom Kunden auf dessen Kosten beizustellen und den Monteuren zu unterweisen. Eine funktionstüchtige Absperrung der Druckwasserleitung wird vorausgesetzt; im Falle einer Erneuerung des Absperrhahns, sind die Kosten durch den Kunden zu tragen. Der Kunde hat uns für die Zeit der Leistungsausführung kostenlos Räumlichkeiten für die Lagerung von Werkzeugen und Materialien zur Verfügung zu stellen.<br/><br/>

<b>8.) Leistungsfristen und Termine</b><br/>
Die für die Leistungsausführung genannten Umbautage sind eine Einschätzung und können variieren bzw. sind somit freibleibend. Im Falle von Abweichungen der angegeben Baustellentage bzw. auch notwendige Folgetermine, aus welchen Gründen auch immer, besteht kein Nachlassanspruch auf den vereinbarten Auftragspreis. Fristen und Termine verschieben sich bei höherer Gewalt, nicht vorhersehbare und von uns nicht verschuldete Verzögerung unserer Zulieferer, Ausfällen von Dienstnehmern oder sonstigen vergleichbaren Ereignissen, die nicht in unserem Einflussbereich liegen. Preisnachlässe sind aufgrund dessen nicht gestattet<br/><br/>

<b>9.) Widerrufsrecht gemäß § 4 Abs 1 FAGG</b><br/>
Sie können von einem außerhalb von Geschäftsräumen geschlossenen Vertrag (§ 3 Z 1 FAGG) oder von einem Fernabsatzvertrag (§ 3 Z 2 FAGG) gemäß § 11 FAGG zurücktreten. Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses. Die Angabe von Gründen ist nicht erforderlich. Vom Rücktritt ausgenommen sind Sondermaß- und speziell für den Kunden angefertigte Produkte sowie auch Sonderbestellungen.<br/><br/>

<b>10.) Rücktritt</b><br/>
Im Falle eines berechtigten Rücktritts vom Vertrag, dürfen wir einen pauschalierten Schadenersatz von 20% des Auftragswertes zuzüglich Ust. ohne Nachweis des tatsächlichen Schadens vom Kunden verlangen. Für Sondermaßbestellungen bzw. speziell für den Kunden angefertigte Produkte beträgt der Schadenersatz 70% des Auftragswertes.<br/><br/>

<b>11.) Hinweis Datenschutz und Datenspeicherung:</b><br/>
Wir weisen darauf hin, dass zum Zweck der Vertragsabwicklung folgende Daten bei uns gespeichert werden: Name, Vorname, Anschrift, Telefonnummer und ggf. Email-Adresse. Die von Ihnen bereit gestellten Daten sind zur Vertragserfüllung bzw. zur Durchführung vorvertraglicher Maßnahmen erforderlich. Ohne diese Daten können wir den Vertrag mit Ihnen nicht abschließen. Eine Datenübermittlung an Dritte erfolgt nicht, mit Ausnahme von den von uns beauftragten Lieferanten zum Zwecke der Bestellabwicklung, an das von uns beauftragte Transportunternehmen zur Zustellung der Ware sowie an unseren Steuerberater zur Erfüllung unserer steuerrechtlichen Verpflichtungen. Im Falle eines Vertragsabschlusses werden sämtliche Daten aus dem Vertragsverhältnis bis zum Ablauf der steuerrechtlichen Aufbewahrungsfrist (7 Jahre) gespeichert. Die Daten Name, Anschrift, gekaufte Waren und Kaufdatum werden darüber hinaus gehend bis zum Ablauf der Produkthaftung (10 Jahre) gespeichert. Im Falle einer Zustimmung zur Verwendung von Fotomaterial, wird dieses bis auf Widerruf bei uns anonym abgespeichert. Die Datenverarbeitung erfolgt auf Basis der gesetzlichen Bestimmungen der DSGVO.<br/>
☑ Ich habe die Datenschutzhinweise gelesen und bin ausdrücklich damit einverstanden.<br/>
☑ Ich stimme zu, Fotomaterial vom Umbauobjekt zur Verfügung zu stellen und bin mit einer Veröffentlichung der Vorher-Nachher Bilder im Rahmen der InnSAN Werbelinie ohne Namensnennung einverstanden.<br/><br/>

<b>12.) Eigentumsvorbehalt</b><br/>
Die von uns gelieferte, montierte oder sonst übergebene Ware bleibt bis zur vollständigen Bezahlung unser Eigentum.
        """
        
        elements.append(Paragraph(agb_text, self.small_style))
        
        return elements
    
    def _build_signature_field(self, quote):
        """Erstellt das Unterschriftsfeld"""
        customer_name = quote.customer.full_name
        signature_data = [
            ['Ort, Datum: _________________________', '', '', ''],
            [f'Unterschrift {customer_name}: _________________________', '', '', '']
        ]
        
        signature_table = Table(signature_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
        signature_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 1), (0, 1), 8),
        ]))
        
        return [Spacer(1, 1*cm), signature_table]
    
    def export_work_instruction(self, order_id):
        """Exportiert eine Arbeitsanweisung als PDF"""
        from models import Order, SupplierOrderItem, QuoteSubItem
        
        order = Order.query.get_or_404(order_id)
        work_instruction = order.work_instruction
        quote = order.quote
        customer = quote.customer
        
        if not work_instruction:
            raise ValueError("Keine Arbeitsanweisung für diesen Auftrag vorhanden")
        
        # PDF-Buffer erstellen
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        
        # Header mit Arbeitsanweisungs-Nummer
        story.append(Paragraph("ARBEITSANWEISUNG", self.title_style))
        story.append(Paragraph(f"Nr. {work_instruction.instruction_number}", self.heading_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Firmeninfo und Auftragsnummer
        company_info = [
            ["Installationsbetrieb Holasek", f"Auftragsnummer: {order.order_number}"],
            ["Ihr kompetenter Partner für Installationen", f"Auftragsdatum: {order.created_at.strftime('%d.%m.%Y') if order.created_at else '-'}"],
            ["", f"Status: {work_instruction.status}"],
            ["", f"Priorität: {work_instruction.priority}"]
        ]
        
        company_table = Table(company_info, colWidths=[10*cm, 7*cm])
        company_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ]))
        story.append(company_table)
        story.append(Spacer(1, 0.8*cm))
        
        # 1. Kundendaten
        story.append(Paragraph("1. KUNDENDATEN", self.heading_style))
        story.append(Spacer(1, 0.3*cm))
        
        customer_data = [
            ["Name:", f"{customer.first_name} {customer.last_name}"],
            ["E-Mail:", customer.email],
            ["Telefon:", customer.phone or "-"],
            ["Adresse:", customer.address or "-"],
            ["PLZ/Ort:", f"{customer.postal_code or ''} {customer.city or ''}".strip() or "-"]
        ]
        
        customer_table = Table(customer_data, colWidths=[3*cm, 14*cm])
        customer_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 0.8*cm))
        
        # 2. Projektinformationen und Montagedetails
        story.append(Paragraph("2. PROJEKTINFORMATIONEN", self.heading_style))
        story.append(Spacer(1, 0.3*cm))
        
        project_data = [
            ["Projekt:", quote.project_description or "-"],
            ["Geplanter Start:", order.start_date.strftime('%d.%m.%Y') if order.start_date else "-"],
            ["Geplantes Ende:", order.end_date.strftime('%d.%m.%Y') if order.end_date else "-"],
            ["Projektleiter:", order.project_manager or "-"],
            ["Status:", order.status],
            ["Montageort:", work_instruction.installation_location or "-"],
            ["Geschätzte Dauer:", f"{work_instruction.estimated_duration} Stunden" if work_instruction.estimated_duration else "-"]
        ]
        
        project_table = Table(project_data, colWidths=[3*cm, 14*cm])
        project_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(project_table)
        story.append(Spacer(1, 0.8*cm))
        
        # 2a. Arbeitsanweisungen und Hinweise
        if work_instruction.sonstiges or work_instruction.tools_required or work_instruction.access_requirements:
            story.append(Paragraph("2a. ARBEITSANWEISUNGEN UND HINWEISE", self.heading_style))
            story.append(Spacer(1, 0.3*cm))
            
            if work_instruction.sonstiges:
                story.append(Paragraph("<b>📄 Sonstiges:</b>", self.styles['Normal']))
                # Add line breaks properly
                sonstiges_lines = work_instruction.sonstiges.split('\n')
                for line in sonstiges_lines:
                    if line.strip():
                        story.append(Paragraph(line, self.styles['Normal']))
                story.append(Spacer(1, 0.3*cm))
            
            if work_instruction.tools_required:
                story.append(Paragraph("<b>Benötigte Werkzeuge:</b>", self.styles['Normal']))
                tools_lines = work_instruction.tools_required.split('\n')
                for line in tools_lines:
                    if line.strip():
                        story.append(Paragraph(line, self.styles['Normal']))
                story.append(Spacer(1, 0.3*cm))
            
            if work_instruction.access_requirements:
                story.append(Paragraph("<b>Zugangserfordernisse:</b>", self.styles['Normal']))
                access_lines = work_instruction.access_requirements.split('\n')
                for line in access_lines:
                    if line.strip():
                        story.append(Paragraph(line, self.styles['Normal']))
                story.append(Spacer(1, 0.3*cm))
            
            story.append(Spacer(1, 0.5*cm))
        
        # 2b. Arbeitsschritte - gespeicherte Daten haben Vorrang vor Quote-Daten
        work_steps = []
        if work_instruction.work_steps_data:
            # Verwende gespeicherte Arbeitsschritte
            try:
                work_steps = json.loads(work_instruction.work_steps_data)
            except:
                work_steps = []
        
        # Falls keine gespeicherten Arbeitsschritte vorhanden, lade aus Quote
        if not work_steps and quote:
            step_number = 1
            for item in quote.quote_items:
                for sub_item in item.sub_items:
                    if sub_item.item_type == 'arbeitsvorgang':
                        work_steps.append({
                            'step_number': step_number,
                            'description': sub_item.description,
                            'notes': '',  # Keine automatischen Notizen mehr
                            'estimated_time': int(sub_item.hours * 60) if sub_item.hours else 0  # Convert hours to minutes
                        })
                        step_number += 1
        
        if work_steps:
            story.append(Paragraph("2b. ARBEITSSCHRITTE", self.heading_style))
            story.append(Spacer(1, 0.3*cm))
            
            work_steps_data = [["Nr.", "Beschreibung", "Notizen", "Zeit (Min)"]]
            for step in work_steps:
                work_steps_data.append([
                    str(step['step_number']),
                    self._wrap_text_for_table(step['description']),
                    self._wrap_text_for_table(step['notes'] or "-"),
                    str(step['estimated_time']) if step['estimated_time'] else "-"
                ])
            
            work_steps_table = Table(work_steps_data, colWidths=[1.5*cm, 10*cm, 4*cm, 1.5*cm])
            work_steps_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(work_steps_table)
            story.append(Spacer(1, 0.8*cm))
        
        # 2c. Teile/Materialien: gespeicherte Daten haben Vorrang vor Quote-Daten
        work_parts = []
        if work_instruction.work_parts_data:
            try:
                work_parts = json.loads(work_instruction.work_parts_data)
            except:
                work_parts = []
        # Falls keine gespeicherten Teile vorhanden, lade aus Quote
        if not work_parts and quote:
            for item in quote.quote_items:
                for sub_item in item.sub_items:
                    if sub_item.item_type == 'bestellteil':
                        work_parts.append({
                            'part_name': sub_item.description,
                            'part_number': sub_item.part_number or '',
                            'quantity': sub_item.part_quantity or '1',
                            'supplier': sub_item.supplier or '',
                            'storage_location': ''
                        })
        if work_parts:
            story.append(Paragraph("2c. BESTELLTEILE", self.heading_style))
            story.append(Spacer(1, 0.3*cm))
            work_parts_data = [["Lieferant", "Artikelnr.", "Teilename", "Anzahl", "Lagerort"]]
            for part in work_parts:
                work_parts_data.append([
                    self._wrap_text_for_table(part.get('supplier', '-') or "-"),
                    self._wrap_text_for_table(part.get('part_number', '-') or "-"),
                    self._wrap_text_for_table(part.get('part_name', '-') or "-"),
                    str(part.get('quantity', 1)),
                    self._wrap_text_for_table(part.get('storage_location', '-') or "-")
                ])
            work_parts_table = Table(work_parts_data, colWidths=[4*cm, 3*cm, 5*cm, 1.5*cm, 3.5*cm])
            work_parts_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(work_parts_table)
            story.append(Spacer(1, 0.8*cm))
        
        # 3b. Sonstige Materialien
        story.append(Paragraph("3. SONSTIGE MATERIALIEN", self.heading_style))
        story.append(Spacer(1, 0.3*cm))
        sonstige = []
        for item in quote.quote_items:
            for sub_item in item.sub_items:
                if sub_item.item_type == 'sonstiges':
                    sonstige.append([
                        f"Pos. {item.position_number}",
                        sub_item.description,
                        sub_item.quantity or "1"
                    ])
        if sonstige:
            sonstige_header = [["Position", "Bezeichnung", "Anzahl"]]
            sonstige_table = Table(sonstige_header + sonstige, 
                                 colWidths=[2*cm, 12*cm, 3*cm])
            sonstige_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(sonstige_table)
        else:
            story.append(Paragraph("Keine sonstigen Materialien vorhanden.", self.styles['Normal']))
        story.append(Spacer(1, 0.8*cm))
        # 4. Fotos und Medien
        story.append(Paragraph("4. FOTOS UND MEDIEN", self.heading_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Tatsächliche Fotos anzeigen falls vorhanden
        if work_instruction.photo_paths:
            try:
                photo_paths = json.loads(work_instruction.photo_paths) if isinstance(work_instruction.photo_paths, str) else work_instruction.photo_paths
                if photo_paths:
                    # Upload-Ordner bestimmen
                    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
                    
                    for i, photo_filename in enumerate(photo_paths, 1):
                        # Vollständigen Pfad zur Datei erstellen
                        photo_path = os.path.join(upload_folder, photo_filename)
                        
                        if os.path.exists(photo_path):
                            try:
                                # Foto hinzufügen
                                story.append(Paragraph(f"<b>Foto {i}:</b>", self.styles['Normal']))
                                story.append(Spacer(1, 0.2*cm))
                                
                                # Prüfe Dateiendung - nur Bilder als Bilder darstellen
                                file_extension = os.path.splitext(photo_filename)[1].lower()
                                if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
                                    # Bild hinzufügen - einfache proportionale Skalierung
                                    # A4 ist 21cm breit, mit 2cm Rand links und rechts = 17cm verfügbar
                                    max_width = 16*cm  # Etwas kleiner für mehr Sicherheit
                                    max_height = 12*cm  # Maximale Höhe für Fotos
                                    
                                    # Lade das Bild ohne Größenangabe zunächst
                                    img = Image(photo_path)
                                    
                                    # Berechne das Seitenverhältnis
                                    img_ratio = img.imageWidth / img.imageHeight
                                    
                                    # Bestimme finale Größe basierend auf verfügbarem Platz
                                    if img_ratio > (max_width / max_height):
                                        # Bild ist breiter -> Breite begrenzt
                                        final_width = max_width
                                        final_height = max_width / img_ratio
                                    else:
                                        # Bild ist höher -> Höhe begrenzt
                                        final_height = max_height
                                        final_width = max_height * img_ratio
                                    
                                    # Erstelle finales Bild mit berechneten Dimensionen
                                    final_img = Image(photo_path, width=final_width, height=final_height)
                                    story.append(final_img)
                                    
                                else:
                                    # Für andere Dateitypen (z.B. PDF) nur Dateiname anzeigen
                                    story.append(Paragraph(f"Datei: {photo_filename} (Typ: {file_extension})", self.styles['Normal']))
                                    story.append(Paragraph("Hinweis: Nicht-Bilddateien werden nicht als Vorschau dargestellt.", self.styles['Normal']))
                                
                                story.append(Spacer(1, 0.5*cm))
                            except Exception as e:
                                story.append(Paragraph(f"Foto {i}: Fehler beim Laden ({photo_filename}) - {str(e)}", self.styles['Normal']))
                                story.append(Spacer(1, 0.3*cm))
                        else:
                            story.append(Paragraph(f"Foto {i}: Datei nicht gefunden ({photo_filename})", self.styles['Normal']))
                            story.append(Spacer(1, 0.3*cm))
                else:
                    story.append(Paragraph("Keine Fotos hochgeladen.", self.styles['Normal']))
            except (json.JSONDecodeError, TypeError):
                story.append(Paragraph("Fehler beim Laden der Fotodaten.", self.styles['Normal']))
        else:
            # Platzhalter-Boxen für Fotos falls keine vorhanden
            story.append(Paragraph("Keine Fotos hochgeladen - Platz für manuelle Ergänzungen:", self.styles['Normal']))
            story.append(Spacer(1, 0.3*cm))
            
            photo_placeholder = [
                ["", "", ""],
                ["Foto 1:", "", ""],
                ["", "", ""],
                ["", "", ""],
                ["Foto 2:", "", ""],
                ["", "", ""],
                ["", "", ""],
                ["Foto 3:", "", ""],
                ["", "", ""]
            ]
            
            photo_table = Table(photo_placeholder, colWidths=[2*cm, 7.5*cm, 7.5*cm])
            photo_table.setStyle(TableStyle([
                ('GRID', (1, 0), (2, -1), 1, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
                ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
                ('FONTNAME', (0, 7), (0, 7), 'Helvetica-Bold'),
            ]))
            story.append(photo_table)
        story.append(Spacer(1, 1*cm))
        
        # 5. Pläne und technische Zeichnungen
        story.append(Paragraph("5. PLÄNE UND TECHNISCHE ZEICHNUNGEN", self.heading_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Tatsächliche Pläne anzeigen falls vorhanden
        if work_instruction.plan_path:
            # Vollständigen Pfad zur Datei erstellen
            upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
            plan_path = os.path.join(upload_folder, work_instruction.plan_path)
            
            if os.path.exists(plan_path):
                try:
                    story.append(Paragraph("<b>Hochgeladener Plan:</b>", self.styles['Normal']))
                    story.append(Spacer(1, 0.2*cm))
                    
                    # Prüfe Dateiendung - nur Bilder als Bilder darstellen
                    file_extension = os.path.splitext(work_instruction.plan_path)[1].lower()
                    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
                        # Plan-Bild hinzufügen - intelligente Größenbestimmung
                        max_width = 17*cm
                        max_height = 20*cm  # Größere Höhe für Pläne
                        
                        # Erstelle zwei Versionen und wähle die passendere
                        # Version 1: Breite maximieren
                        img_width = Image(plan_path, width=max_width, height=None)
                        
                        # Version 2: Höhe maximieren  
                        img_height = Image(plan_path, width=None, height=max_height)
                        
                        # Wähle die Version die besser in den verfügbaren Raum passt
                        if img_width.drawHeight <= max_height:
                            # Breite-optimierte Version passt in die Höhe
                            story.append(img_width)
                        else:
                            # Höhe-optimierte Version verwenden
                            story.append(img_height)
                        
                    else:
                        # Für andere Dateitypen (z.B. PDF) nur Dateiname anzeigen
                        story.append(Paragraph(f"Plan-Datei: {work_instruction.plan_path} (Typ: {file_extension})", self.styles['Normal']))
                        story.append(Paragraph("Hinweis: Nicht-Bilddateien werden nicht als Vorschau dargestellt.", self.styles['Normal']))
                except Exception as e:
                    story.append(Paragraph(f"Plan: Fehler beim Laden ({work_instruction.plan_path}) - {str(e)}", self.styles['Normal']))
            else:
                story.append(Paragraph(f"Plan: Datei nicht gefunden ({work_instruction.plan_path})", self.styles['Normal']))
        else:
            # Platzhalter für Plan falls keiner vorhanden
            story.append(Paragraph("Kein Plan hochgeladen - Platz für manuelle Ergänzungen:", self.styles['Normal']))
            story.append(Spacer(1, 0.3*cm))
            
            plan_placeholder = [
                ["", ""],
                ["", ""],
                ["", ""],
                ["", ""],
                ["", ""],
                ["", ""]
            ]
            
            plan_table = Table(plan_placeholder, colWidths=[8.5*cm, 8.5*cm])
            plan_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(plan_table)
        
        # Footer
        story.append(Spacer(1, 1*cm))
        footer_text = f"Arbeitsanweisung erstellt am: {order.created_at.strftime('%d.%m.%Y %H:%M') if order.created_at else '-'}"
        story.append(Paragraph(footer_text, self.small_style))
        
        # PDF generieren
        doc.build(story)
        buffer.seek(0)
        
        # Wenn ein PDF-Plan hochgeladen wurde, hänge diesen an
        if work_instruction.plan_path and work_instruction.plan_path.lower().endswith('.pdf'):
            upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
            plan_pdf_path = os.path.join(upload_folder, work_instruction.plan_path)
            
            if os.path.exists(plan_pdf_path):
                try:
                    # Kombiniere beide PDFs
                    final_buffer = self._merge_pdfs(buffer, plan_pdf_path)
                    return final_buffer
                except Exception as e:
                    print(f"Fehler beim Anhängen des Plans: {e}")
                    # Fallback: Nur die Arbeitsanweisung zurückgeben
                    buffer.seek(0)
                    return buffer
        
        return buffer
    
    def _merge_pdfs(self, work_instruction_buffer, plan_pdf_path):
        """Fügt das Plan-PDF an die Arbeitsanweisung an"""
        try:
            # PDF Writer für das finale PDF erstellen
            writer = PdfWriter()
            
            # Arbeitsanweisung hinzufügen
            work_instruction_buffer.seek(0)
            work_instruction_reader = PdfReader(work_instruction_buffer)
            for page in work_instruction_reader.pages:
                writer.add_page(page)
            
            # Plan-PDF hinzufügen
            plan_reader = PdfReader(plan_pdf_path)
            for page in plan_reader.pages:
                writer.add_page(page)
            
            # Finales PDF in Buffer schreiben
            final_buffer = BytesIO()
            writer.write(final_buffer)
            final_buffer.seek(0)
            
            return final_buffer
            
        except Exception as e:
            print(f"Fehler beim Zusammenfügen der PDFs: {e}")
            # Fallback: Nur die Arbeitsanweisung zurückgeben
            work_instruction_buffer.seek(0)
            return work_instruction_buffer

    def export_invoice(self, invoice_id):
        """Exportiert eine Rechnung als PDF"""
        from models import Invoice
        from invoice_pdf import InvoicePDFGenerator
        
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # PDF-Generator verwenden
        pdf_generator = InvoicePDFGenerator()
        pdf_buffer = pdf_generator.generate_invoice_pdf(invoice)
        
        return pdf_buffer
