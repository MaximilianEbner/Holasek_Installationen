#!/usr/bin/env python3
"""
Script zum Löschen aller Angebote, Rechnungen und Aufträge aus der Datenbank
Kunden und andere Stammdaten bleiben erhalten.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sqlite3

# Flask App Kontext laden
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import Quote, Order, Invoice, QuoteItem, QuoteSubItem, SupplierOrder, SupplierOrderItem, QuoteRejection

def clear_database():
    """Löscht alle Angebote, Aufträge und Rechnungen aus der Datenbank"""
    
    with app.app_context():
        try:
            print("🗑️  Starte Datenbank-Bereinigung...")
            
            # Zähle Einträge vor dem Löschen
            quote_count = Quote.query.count()
            order_count = Order.query.count() 
            invoice_count = Invoice.query.count()
            
            print(f"📊 Gefunden:")
            print(f"   - {quote_count} Angebote")
            print(f"   - {order_count} Aufträge") 
            print(f"   - {invoice_count} Rechnungen")
            
            if quote_count == 0 and order_count == 0 and invoice_count == 0:
                print("✅ Datenbank ist bereits leer!")
                return
            
            # Bestätigung einholen
            confirm = input("\n⚠️  WARNUNG: Alle Angebote, Aufträge und Rechnungen werden PERMANENT gelöscht!\n"
                          "Kunden und Stammdaten bleiben erhalten.\n"
                          "Möchten Sie fortfahren? (ja/nein): ").lower().strip()
            
            if confirm not in ['ja', 'j', 'yes', 'y']:
                print("❌ Abgebrochen.")
                return
            
            print("\n🔄 Lösche Daten...")
            
            # 1. Lösche QuoteSubItems (Unterpositionen von Angeboten)
            sub_items_deleted = db.session.query(QuoteSubItem).delete()
            print(f"   ✓ {sub_items_deleted} Angebots-Unterpositionen gelöscht")
            
            # 2. Lösche QuoteItems (Angebotspositionen)
            quote_items_deleted = db.session.query(QuoteItem).delete()
            print(f"   ✓ {quote_items_deleted} Angebotspositionen gelöscht")
            
            # 3. Lösche SupplierOrderItems (Lieferanten-Bestellpositionen)
            supplier_order_items_deleted = db.session.query(SupplierOrderItem).delete()
            print(f"   ✓ {supplier_order_items_deleted} Lieferanten-Bestellpositionen gelöscht")
            
            # 4. Lösche SupplierOrders (Lieferanten-Bestellungen)
            supplier_orders_deleted = db.session.query(SupplierOrder).delete()
            print(f"   ✓ {supplier_orders_deleted} Lieferanten-Bestellungen gelöscht")
            
            # 5. Lösche QuoteRejections (Angebots-Ablehnungen)
            rejections_deleted = db.session.query(QuoteRejection).delete()
            print(f"   ✓ {rejections_deleted} Angebots-Ablehnungen gelöscht")
            
            # 6. Lösche Rechnungen
            invoices_deleted = db.session.query(Invoice).delete()
            print(f"   ✓ {invoices_deleted} Rechnungen gelöscht")
            
            # 7. Lösche Aufträge
            orders_deleted = db.session.query(Order).delete()
            print(f"   ✓ {orders_deleted} Aufträge gelöscht")
            
            # 8. Lösche Angebote
            quotes_deleted = db.session.query(Quote).delete()
            print(f"   ✓ {quotes_deleted} Angebote gelöscht")
            
            # Änderungen speichern
            db.session.commit()
            
            print("\n✅ Datenbank erfolgreich bereinigt!")
            print("📋 Folgende Daten wurden entfernt:")
            print(f"   - {quotes_deleted} Angebote")
            print(f"   - {orders_deleted} Aufträge")
            print(f"   - {invoices_deleted} Rechnungen")
            print(f"   - {supplier_orders_deleted} Lieferanten-Bestellungen")
            print(f"   - {quote_items_deleted + supplier_order_items_deleted + sub_items_deleted} zugehörige Positionen")
            print(f"   - {rejections_deleted} Angebots-Ablehnungen")
            
            print("\n🔒 Erhalten geblieben:")
            print("   - Alle Kunden")
            print("   - Alle Produkte")
            print("   - Alle Lieferanten")
            print("   - Alle Vorlagen")
            print("   - Alle Systemeinstellungen")
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen: {e}")
            db.session.rollback()
            raise
        
def reset_auto_increment():
    """Setzt die Auto-Increment Zähler zurück (nur für SQLite)"""
    
    try:
        # Prüfe ob SQLite verwendet wird
        if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', '').lower():
            print("\n🔄 Setze Auto-Increment Zähler zurück...")
            
            # Direkte SQLite Verbindung für SQLITE_SEQUENCE Reset
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Reset der Auto-Increment Zähler
            tables_to_reset = ['quotes', 'orders', 'invoices', 'quote_items', 'quote_sub_items', 'supplier_orders', 'supplier_order_items', 'quote_rejections']
            
            for table in tables_to_reset:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            
            conn.commit()
            conn.close()
            
            print("   ✓ Auto-Increment Zähler zurückgesetzt")
            print("   → Neue Angebote/Aufträge/Rechnungen starten wieder bei 1")
        else:
            print("ℹ️  Auto-Increment Reset nur für SQLite verfügbar")
            
    except Exception as e:
        print(f"⚠️  Warnung: Auto-Increment Reset fehlgeschlagen: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🗃️  DATENBANK BEREINIGUNG")
    print("=" * 60)
    
    clear_database()
    reset_auto_increment()
    
    print("\n" + "=" * 60)
    print("✅ BEREINIGUNG ABGESCHLOSSEN")
    print("=" * 60)
