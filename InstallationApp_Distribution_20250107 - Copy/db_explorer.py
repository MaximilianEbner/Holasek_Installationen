#!/usr/bin/env python3
"""
Automatisches Backup-System für die Installation Business App
"""
import sqlite3
import os
import csv
import shutil
import sys
from datetime import datetime

def create_automatic_backup():
    """Erstellt automatisch ein komplettes Backup (CSV + DB-Datei)"""
    
    db_path = "instance/installation_business.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank nicht gefunden!")
        print(f"Gesucht in: {os.path.abspath(db_path)}")
        return False
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"backup_{timestamp}"
        
        # Backup-Hauptordner erstellen
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)
        
        print("🎯 KOMPLETTES AUTOMATISCHES BACKUP")
        print("=" * 50)
        print(f"Backup-Ordner: {backup_folder}")
        print(f"Zeitstempel: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}")
        print("-" * 50)
        
        # 1. SQLite DB-Datei kopieren
        print("📀 Kopiere SQLite-Datenbank...")
        db_backup_path = os.path.join(backup_folder, "installation_business.db")
        shutil.copy2(db_path, db_backup_path)
        db_size = os.path.getsize(db_backup_path) / 1024  # KB
        print(f"✅ SQLite-Datenbank kopiert ({db_size:.1f} KB)")
        
        # 2. CSV-Export erstellen
        print("\n📊 Erstelle CSV-Export...")
        csv_folder = os.path.join(backup_folder, "csv_export")
        os.makedirs(csv_folder, exist_ok=True)
        
        # Verbindung zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Alle Tabellen ermitteln
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        exported_count = 0
        total_rows = 0
        
        for (table_name,) in tables:
            try:
                csv_filename = os.path.join(csv_folder, f"{table_name}.csv")
                
                # Spalten abrufen
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Daten abrufen
                cursor.execute(f"SELECT * FROM '{table_name}';")
                rows = cursor.fetchall()
                
                # CSV schreiben
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    writer.writerow(column_names)
                    
                    for row in rows:
                        clean_row = ['' if cell is None else str(cell) for cell in row]
                        writer.writerow(clean_row)
                
                print(f"✅ {table_name:<20} -> {len(rows):>5} Zeilen")
                exported_count += 1
                total_rows += len(rows)
                
            except Exception as e:
                print(f"❌ {table_name:<20} -> Fehler: {e}")
        
        conn.close()
        
        # 3. Backup-Info Datei erstellen
        print("\n📋 Erstelle Backup-Information...")
        create_backup_info_file(backup_folder, csv_folder, exported_count, total_rows, db_size)
        
        # 4. Erfolgsmeldung
        print("\n🎉 BACKUP ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 50)
        print(f"📁 Backup-Ordner: {os.path.abspath(backup_folder)}")
        print(f"📀 SQLite-Datenbank: installation_business.db")
        print(f"📊 CSV-Export: {exported_count} Tabellen mit {total_rows} Datensätzen")
        print(f"📋 Backup-Info: BACKUP_INFO.txt")
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Backup: {e}")
        return False

def create_backup_info_file(backup_folder, csv_folder, exported_count, total_rows, db_size):
    """Erstellt eine detaillierte Backup-Info Datei"""
    
    info_file = os.path.join(backup_folder, "BACKUP_INFO.txt")
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("INSTALLATIONS BUSINESS APP - KOMPLETTES BACKUP\n")
        f.write("=" * 60 + "\n")
        f.write(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}\n")
        f.write(f"Backup-Version: v2.0\n")
        f.write("\nINHALT DES BACKUPS:\n")
        f.write("-" * 30 + "\n")
        f.write(f"📀 SQLite-Datenbank: installation_business.db ({db_size:.1f} KB)\n")
        f.write(f"📊 CSV-Export: {exported_count} Tabellen mit {total_rows} Datensätzen\n")
        f.write(f"📁 CSV-Ordner: csv_export/\n")
        
        # CSV-Details
        if os.path.exists(csv_folder):
            f.write("\nCSV-EXPORT DETAILS:\n")
            f.write("-" * 20 + "\n")
            
            csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
            for csv_file in sorted(csv_files):
                table_name = csv_file.replace('.csv', '')
                csv_path = os.path.join(csv_folder, csv_file)
                
                # Zeilen zählen (ohne Header)
                try:
                    with open(csv_path, 'r', encoding='utf-8') as csvf:
                        row_count = sum(1 for line in csvf) - 1  # -1 für Header
                    f.write(f"{table_name:<20} -> {row_count:>5} Zeilen\n")
                except:
                    f.write(f"{table_name:<20} -> ? Zeilen\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("WIEDERHERSTELLUNG:\n")
        f.write("=" * 60 + "\n")
        f.write("1. SQLite-Datenbank:\n")
        f.write("   - Kopieren Sie 'installation_business.db' in den 'instance/' Ordner\n")
        f.write("   - Überschreibt die aktuelle Datenbank komplett\n")
        f.write("\n2. CSV-Dateien:\n")
        f.write("   - Jede CSV-Datei entspricht einer Datenbanktabelle\n")
        f.write("   - Trennzeichen: Semikolon (;)\n")
        f.write("   - Kodierung: UTF-8\n")
        f.write("   - Erste Zeile enthält Spaltennamen\n")
        f.write("   - Kann in Excel/LibreOffice geöffnet werden\n")
        f.write("\n3. Notfall-Wiederherstellung:\n")
        f.write("   - Bei Datenbankproblemen: SQLite-Datei zurückkopieren\n")
        f.write("   - Bei Datenverlusten: CSV-Dateien als Referenz nutzen\n")
        f.write("\n" + "=" * 60 + "\n")

def explore_database():
    """Erkundet die Installation Business Database"""
    
    db_path = "instance/installation_business.db"
    
    if not os.path.exists(db_path):
        print("❌ Datenbank nicht gefunden!")
        print(f"Gesucht in: {os.path.abspath(db_path)}")
        return
    
    try:
        # Verbindung zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🎯 INSTALLATIONS BUSINESS DATABASE EXPLORER")
        print("=" * 50)
        
        # Alle Tabellen anzeigen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Gefundene Tabellen ({len(tables)}):")
        for i, (table_name,) in enumerate(tables, 1):
            print(f"  {i}. {table_name}")
        
        # Für jede Tabelle: Anzahl Einträge
        print("\n📊 Datenbank-Übersicht:")
        print("-" * 30)
        
        for (table_name,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                count = cursor.fetchone()[0]
                print(f"  {table_name:<20} {count:>5} Einträge")
            except Exception as e:
                print(f"  {table_name:<20} Fehler: {e}")
        
        # Hauptmenü
        print("\n" + "=" * 50)
        print("🔍 HAUPTMENÜ")
        print("1. Tabelle anzeigen")
        print("2. Einzelne Tabelle als CSV exportieren")
        print("3. VOLLSTÄNDIGES CSV-BACKUP erstellen")
        print("q. Beenden")
        
        while True:
            try:
                user_input = input("\nWahl (1-3) oder 'q': ").strip()
                
                if user_input.lower() == 'q':
                    break
                elif user_input == '1':
                    interactive_table_view(cursor, tables)
                elif user_input == '2':
                    export_single_table_csv(cursor, tables)
                elif user_input == '3':
                    export_full_backup_csv(cursor, tables)
                else:
                    print("❌ Ungültige Auswahl!")
                    
            except KeyboardInterrupt:
                break
        
        conn.close()
        print("\n✅ Datenbankverbindung geschlossen.")
        
    except Exception as e:
        print(f"❌ Fehler beim Öffnen der Datenbank: {e}")

def interactive_table_view(cursor, tables):
    """Interaktive Tabellenansicht"""
    print("\n📋 TABELLEN ANZEIGEN")
    for i, (table_name,) in enumerate(tables, 1):
        print(f"  {i}. {table_name}")
    
    try:
        user_input = input(f"\nTabelle auswählen (1-{len(tables)}): ").strip()
        table_index = int(user_input) - 1
        
        if 0 <= table_index < len(tables):
            table_name = tables[table_index][0]
            show_table_data(cursor, table_name)
        else:
            print("❌ Ungültige Auswahl!")
            
    except ValueError:
        print("❌ Bitte eine Zahl eingeben!")

def export_single_table_csv(cursor, tables):
    """Exportiert eine einzelne Tabelle als CSV"""
    print("\n📊 EINZELNE TABELLE EXPORTIEREN")
    for i, (table_name,) in enumerate(tables, 1):
        print(f"  {i}. {table_name}")
    
    try:
        user_input = input(f"\nTabelle auswählen (1-{len(tables)}): ").strip()
        table_index = int(user_input) - 1
        
        if 0 <= table_index < len(tables):
            table_name = tables[table_index][0]
            export_table_to_csv(cursor, table_name)
        else:
            print("❌ Ungültige Auswahl!")
            
    except ValueError:
        print("❌ Bitte eine Zahl eingeben!")

def export_full_backup_csv(cursor, tables):
    """Erstellt ein vollständiges CSV-Backup aller Tabellen"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"csv_backup_{timestamp}"
    
    # Backup-Ordner erstellen
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    print(f"\n🎯 VOLLSTÄNDIGES CSV-BACKUP")
    print(f"Backup-Ordner: {backup_folder}")
    print("-" * 40)
    
    exported_count = 0
    total_rows = 0
    
    for (table_name,) in tables:
        try:
            # Dateiname für diese Tabelle
            csv_filename = os.path.join(backup_folder, f"{table_name}.csv")
            
            # Spalten abrufen
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Daten abrufen
            cursor.execute(f"SELECT * FROM '{table_name}';")
            rows = cursor.fetchall()
            
            # CSV schreiben
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')  # Deutsch-freundlich mit Semikolon
                
                # Header schreiben
                writer.writerow(column_names)
                
                # Daten schreiben
                for row in rows:
                    # Konvertiere None zu leerem String
                    clean_row = ['' if cell is None else str(cell) for cell in row]
                    writer.writerow(clean_row)
            
            print(f"✅ {table_name:<20} -> {len(rows):>5} Zeilen")
            exported_count += 1
            total_rows += len(rows)
            
        except Exception as e:
            print(f"❌ {table_name:<20} -> Fehler: {e}")
    
    # Zusammenfassung erstellen
    summary_file = os.path.join(backup_folder, "BACKUP_INFO.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 50 + "\n")
        f.write("INSTALLATIONS BUSINESS APP - CSV BACKUP\n")
        f.write("=" * 50 + "\n")
        f.write(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}\n")
        f.write(f"Tabellen exportiert: {exported_count}\n")
        f.write(f"Gesamt Datensätze: {total_rows}\n")
        f.write("\nExportierte Tabellen:\n")
        f.write("-" * 20 + "\n")
        
        for (table_name,) in tables:
            csv_file = f"{table_name}.csv"
            if os.path.exists(os.path.join(backup_folder, csv_file)):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                    count = cursor.fetchone()[0]
                    f.write(f"{table_name:<20} -> {count:>5} Zeilen\n")
                except:
                    f.write(f"{table_name:<20} -> ? Zeilen\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("WIEDERHERSTELLUNG:\n")
        f.write("- Jede CSV-Datei entspricht einer Datenbanktabelle\n")
        f.write("- Trennzeichen: Semikolon (;)\n")
        f.write("- Kodierung: UTF-8\n")
        f.write("- Erste Zeile enthält Spaltennamen\n")
    
    print(f"\n🎉 CSV-BACKUP ABGESCHLOSSEN!")
    print(f"📁 Ordner: {os.path.abspath(backup_folder)}")
    print(f"📊 {exported_count} Tabellen mit {total_rows} Datensätzen exportiert")
    print(f"📋 Backup-Info: {summary_file}")

def export_table_to_csv(cursor, table_name):
    """Exportiert eine einzelne Tabelle als CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{table_name}_{timestamp}.csv"
    
    try:
        # Spalten abrufen
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Daten abrufen
        cursor.execute(f"SELECT * FROM '{table_name}';")
        rows = cursor.fetchall()
        
        # CSV schreiben
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            
            # Header schreiben
            writer.writerow(column_names)
            
            # Daten schreiben
            for row in rows:
                clean_row = ['' if cell is None else str(cell) for cell in row]
                writer.writerow(clean_row)
        
        print(f"\n✅ Tabelle '{table_name}' erfolgreich exportiert!")
        print(f"📁 Datei: {os.path.abspath(csv_filename)}")
        print(f"📊 {len(rows)} Datensätze exportiert")
        
    except Exception as e:
        print(f"❌ Fehler beim Exportieren: {e}")

def show_table_data(cursor, table_name):
    """Zeigt Daten einer Tabelle an"""
    
    print(f"\n📋 Tabelle: {table_name}")
    print("-" * 40)
    
    try:
        # Spalten-Info
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()
        
        print("Spalten:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = " (PRIMARY KEY)" if col[5] else ""
            print(f"  - {col_name} ({col_type}){is_pk}")
        
        # Erste 5 Einträge anzeigen
        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5;")
        rows = cursor.fetchall()
        
        if rows:
            print(f"\nErste {len(rows)} Einträge:")
            col_names = [col[1] for col in columns]
            
            # Header
            header = " | ".join(f"{name:<15}" for name in col_names)
            print(header)
            print("-" * len(header))
            
            # Daten
            for row in rows:
                row_str = " | ".join(f"{str(val):<15}" for val in row)
                print(row_str)
        else:
            print("Keine Daten gefunden.")
            
    except Exception as e:
        print(f"❌ Fehler beim Anzeigen der Tabelle: {e}")

if __name__ == "__main__":
    # Prüfe ob automatisches Backup gewünscht ist
    if len(sys.argv) > 1 and sys.argv[1] == "--auto-backup":
        success = create_automatic_backup()
        if success:
            print("\n✅ Drücken Sie eine Taste zum Beenden...")
        else:
            print("\n❌ Backup fehlgeschlagen! Drücken Sie eine Taste zum Beenden...")
        try:
            input()
        except:
            pass
    else:
        # Interaktiver Modus
        explore_database()
