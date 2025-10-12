""""
CSV/Excel Backup and Restore System für die Installation Business App
Erstellt vollständige Backups aller Datentabellen und ermöglicht Wiederherstellung
"""
import os
import csv
import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO, StringIO
import pandas as pd
from flask import flash
from sqlalchemy import text
from sqlalchemy.inspection import inspect
from models import (
    db, Customer, Quote, QuoteItem, QuoteSubItem, Order, Invoice, 
    Supplier, SupplierOrder, SupplierOrderItem, PositionTemplate, 
    AcquisitionChannel, CompanySettings, WorkInstruction, 
    InvoiceReminder, QuoteRejection, PositionTemplateSubItem,
    Article, InvoicePosition, LoginAdmin
)

BACKUP_MODELS = [
    CompanySettings, AcquisitionChannel, Supplier, Article,
    PositionTemplate, PositionTemplateSubItem, Customer,
    Quote, QuoteItem, QuoteSubItem, QuoteRejection,
    Order, WorkInstruction, SupplierOrder, SupplierOrderItem,
    Invoice, InvoicePosition, InvoiceReminder,
]

class CSVBackupSystem:
    """Vollständiges CSV/Excel Backup und Restore System"""
    def __init__(self):
        self.backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.models = BACKUP_MODELS

    def get_model_data(self, model_class):
        """Extrahiert alle Daten aus einem Model als Liste von Dictionaries"""
        try:
            print(f"📊 Extrahiere Daten aus {model_class.__name__}...")
            records = model_class.query.all()
            columns = [column.name for column in inspect(model_class).columns]
            data = []
            for record in records:
                row_data = {}
                for column in columns:
                    value = getattr(record, column)
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif value is None:
                        value = ''
                    row_data[column] = value
                data.append(row_data)
            print(f"   ✓ {len(data)} Datensätze gefunden")
            return data, columns
        except Exception as e:
            print(f"   ❌ Fehler beim Laden der Daten für {model_class.__name__}: {str(e)}")
            return [], []

    def create_csv_backup(self):
        """Erstellt CSV-Backup aller Tabellen in einem ZIP-Archiv"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'InnSAN_CSV_Backup_{timestamp}.zip'
        backup_path = os.path.join(self.backup_dir, backup_filename)
        print(f"🚀 Erstelle CSV-Backup: {backup_filename}")
        print("=" * 60)
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                metadata = {
                    'backup_timestamp': timestamp,
                    'backup_type': 'CSV_COMPLETE',
                    'total_tables': len(self.models),
                    'app_version': 'InnSAN v2.0',
                    'tables': []
                }
                for model_class in self.models:
                    table_name = model_class.__tablename__
                    try:
                        data, columns = self.get_model_data(model_class)
                        csv_output = StringIO()
                        if data and columns:
                            writer = csv.DictWriter(csv_output, fieldnames=columns)
                            writer.writeheader()
                            writer.writerows(data)
                        csv_filename = f"{table_name}.csv"
                        zipf.writestr(csv_filename, csv_output.getvalue())
                        metadata['tables'].append({
                            'name': table_name,
                            'records': len(data),
                            'columns': len(columns)
                        })
                    except Exception as e:
                        print(f"   ❌ Fehler bei Tabelle {table_name}: {str(e)}")
                        metadata['tables'].append({
                            'name': table_name,
                            'records': 0,
                            'columns': 0,
                            'error': str(e)
                        })
                metadata_json = json.dumps(metadata, indent=2)
                zipf.writestr('backup_metadata.json', metadata_json)
            print("=" * 60)
            print(f"✅ CSV-Backup erfolgreich erstellt: {backup_filename}")
            return backup_path
        except Exception as e:
            print(f"❌ Fehler beim CSV-Backup: {str(e)}")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise e

    def create_excel_backup(self):
        """Erstellt Excel-Backup mit allen Tabellen in separaten Sheets"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'InnSAN_Excel_Backup_{timestamp}.xlsx'
        backup_path = os.path.join(self.backup_dir, backup_filename)
        print(f"📊 Erstelle Excel-Backup: {backup_filename}")
        print("=" * 60)
        try:
            all_data = {}
            for model_class in self.models:
                table_name = model_class.__tablename__
                data, columns = self.get_model_data(model_class)
                if data:
                    df = pd.DataFrame(data)
                    all_data[table_name] = df
                else:
                    print(f"   ⚪ {table_name}: Keine Daten")
            with pd.ExcelWriter(backup_path, engine='openpyxl') as writer:
                for table_name, df in all_data.items():
                    df.to_excel(writer, sheet_name=table_name, index=False)
                info_data = {
                    'Backup Info': [
                        'InnSAN Installation Business App',
                        f'Backup erstellt am: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}',
                        f'Anzahl Tabellen: {len(all_data)}',
                        f'Format: Excel (.xlsx)',
                        '',
                        'Enthaltene Tabellen:'
                    ]
                }
                for table_name, df in all_data.items():
                    info_data['Backup Info'].append(f'- {table_name}: {len(df)} Datensätze')
                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name='Backup_Info', index=False)
            print("=" * 60)
            print(f"✅ Excel-Backup erfolgreich erstellt: {backup_filename}")
            return backup_path
        except Exception as e:
            print(f"❌ Fehler beim Excel-Backup: {str(e)}")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise e

    def restore_from_csv(self, zip_file_path):
        """Stellt Daten aus CSV-Backup wieder her"""
        print(f"🔄 Beginne CSV-Wiederherstellung aus: {os.path.basename(zip_file_path)}")
        print("=" * 70)
        try:
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(zip_file_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            metadata_path = os.path.join(temp_dir, 'backup_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    timestamp = metadata.get('backup_timestamp', 'Unbekannt')
                    table_count = metadata.get('total_tables', 0)
                    print(f"📋 Backup-Info: {timestamp} ({table_count} Tabellen)")
            print("🗑️  Lösche bestehende Daten...")
            for model_class in reversed(self.models):
                try:
                    count = model_class.query.count()
                    if count > 0:
                        model_class.query.delete()
                        print(f"   🗑️  {model_class.__tablename__}: {count} Datensätze gelöscht")
                except Exception as e:
                    print(f"   ⚠️ Fehler beim Löschen {model_class.__tablename__}: {str(e)}")
            db.session.commit()
            print("📥 Stelle Daten wieder her...")
            restored_count = 0
            for model_class in self.models:
                table_name = model_class.__tablename__
                csv_file_path = os.path.join(temp_dir, f"{table_name}.csv")
                if os.path.exists(csv_file_path):
                    try:
                        df = pd.read_csv(csv_file_path)
                        if len(df) > 0:
                            count = self._restore_model_data(model_class, df)
                            restored_count += count
                            print(f"   ✓ {table_name}: {count} Datensätze wiederhergestellt")
                        else:
                            print(f"   ⚪ {table_name}: Keine Daten")
                    except Exception as e:
                        print(f"   ✗ Fehler bei {table_name}: {str(e)}")
                else:
                    print(f"   ⚠️ {table_name}: CSV-Datei nicht gefunden")
            db.session.commit()
            shutil.rmtree(temp_dir)
            print("=" * 70)
            print(f"✅ Wiederherstellung abgeschlossen: {restored_count} Datensätze insgesamt")
            return True
        except Exception as e:
            print(f"❌ Kritischer Fehler bei der CSV-Wiederherstellung: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

    def restore_from_excel(self, excel_file_path):
        """Stellt Daten aus Excel-Backup wieder her"""
        print(f"🔄 Beginne Excel-Wiederherstellung aus: {os.path.basename(excel_file_path)}")
        print("=" * 70)
        try:
            xl_file = pd.ExcelFile(excel_file_path)
            print("🗑️  Lösche bestehende Daten...")
            for model_class in reversed(self.models):
                try:
                    count = model_class.query.count()
                    if count > 0:
                        model_class.query.delete()
                        print(f"   🗑️  {model_class.__tablename__}: {count} Datensätze gelöscht")
                except Exception as e:
                    print(f"   ⚠️ Fehler beim Löschen {model_class.__tablename__}: {str(e)}")
            db.session.commit()
            print("📥 Stelle Daten wieder her...")
            restored_count = 0
            for model_class in self.models:
                table_name = model_class.__tablename__
                if table_name in xl_file.sheet_names:
                    try:
                        df = pd.read_excel(excel_file_path, sheet_name=table_name)
                        if len(df) > 0:
                            count = self._restore_model_data(model_class, df)
                            restored_count += count
                            print(f"   ✓ {table_name}: {count} Datensätze wiederhergestellt")
                        else:
                            print(f"   ⚪ {table_name}: Keine Daten")
                    except Exception as e:
                        print(f"   ✗ Fehler bei {table_name}: {str(e)}")
                else:
                    print(f"   ⚠️ {table_name}: Excel-Sheet nicht gefunden")
            db.session.commit()
            print("=" * 70)
            print(f"✅ Excel-Wiederherstellung abgeschlossen: {restored_count} Datensätze insgesamt")
            return True
        except Exception as e:
            print(f"❌ Kritischer Fehler bei der Excel-Wiederherstellung: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

    def _restore_model_data(self, model_class, df):
        """Stellt Daten für ein spezifisches Model wieder her"""
        try:
            count = 0
            for _, row in df.iterrows():
                instance = model_class()
                for column in row.index:
                    if hasattr(instance, column):
                        value = row[column]
                        if pd.isna(value) or value == '':
                            value = None
                        elif isinstance(value, str) and 'T' in value and ':' in value:
                            try:
                                from datetime import datetime as dt
                                value = dt.fromisoformat(value.replace('Z', '+00:00'))
                            except:
                                pass
                        
                        # Typ-Konvertierung basierend auf SQLAlchemy Spalten-Typ
                        if value is not None and hasattr(model_class, column):
                            column_obj = getattr(model_class, column)
                            if hasattr(column_obj, 'type'):
                                column_type = str(column_obj.type)
                                if 'INTEGER' in column_type or 'BIGINT' in column_type:
                                    try:
                                        value = int(value)
                                    except (ValueError, TypeError):
                                        value = None
                                elif 'FLOAT' in column_type or 'DECIMAL' in column_type or 'NUMERIC' in column_type:
                                    try:
                                        value = float(value)
                                    except (ValueError, TypeError):
                                        value = None
                                elif 'BOOLEAN' in column_type:
                                    if isinstance(value, str):
                                        value = value.lower() in ('true', '1', 'yes', 'on')
                                    else:
                                        value = bool(value)
                                elif 'DATE' in column_type or 'TIME' in column_type:
                                    if isinstance(value, str) and value.strip():
                                        try:
                                            from datetime import datetime as dt
                                            # Versuche verschiedene Datumsformate
                                            if 'T' in value:
                                                # ISO Format mit Zeit
                                                value = dt.fromisoformat(value.replace('Z', '+00:00'))
                                            elif len(value) == 10 and '-' in value:
                                                # Nur Datum YYYY-MM-DD
                                                value = dt.strptime(value, '%Y-%m-%d').date()
                                            else:
                                                # Versuche Standard-Parsing
                                                value = dt.fromisoformat(value)
                                        except (ValueError, TypeError):
                                            value = None
                        
                        setattr(instance, column, value)
                db.session.add(instance)
                count += 1
            return count
        except Exception as e:
            print(f"❌ Fehler beim Wiederherstellen von {model_class.__name__}: {str(e)}")
            raise e

    def list_backups(self):
        """Listet alle verfügbaren Backup-Dateien auf"""
        try:
            backups = []
            if not os.path.exists(self.backup_dir):
                return backups
            for filename in os.listdir(self.backup_dir):
                if filename.endswith(('.zip', '.xlsx')):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(file_path)
                    backup_info = {
                        'filename': filename,
                        'path': file_path,
                        'size': file_stat.st_size,
                        'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                        'created': datetime.fromtimestamp(file_stat.st_ctime),
                        'type': 'ZIP' if filename.endswith('.zip') else 'Excel'
                    }
                    backups.append(backup_info)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
        except Exception as e:
            print(f"Fehler beim Auflisten der Backups: {str(e)}")
            return []

    def delete_backup(self, filename):
        """Löscht eine Backup-Datei"""
        try:
            file_path = os.path.join(self.backup_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Backup gelöscht: {filename}")
                return True
            else:
                print(f"❌ Backup-Datei nicht gefunden: {filename}")
                return False
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Backups: {str(e)}")
            return False

    def get_backup_info(self, filename):
        """Gibt detaillierte Informationen über ein Backup zurück"""
        try:
            file_path = os.path.join(self.backup_dir, filename)
            if not os.path.exists(file_path):
                return None
            file_stat = os.stat(file_path)
            info = {
                'filename': filename,
                'size': file_stat.st_size,
                'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(file_stat.st_ctime),
                'type': 'ZIP' if filename.endswith('.zip') else 'Excel',
                'tables': []
            }
            if filename.endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as zipf:
                        file_list = zipf.namelist()
                        csv_files = [f for f in file_list if f.endswith('.csv')]
                        for csv_file in csv_files:
                            table_name = csv_file.replace('.csv', '')
                            info['tables'].append({'name': table_name, 'type': 'CSV'})
                        if 'backup_metadata.json' in file_list:
                            metadata_content = zipf.read('backup_metadata.json')
                            metadata = json.loads(metadata_content.decode('utf-8'))
                            info['metadata'] = metadata
                except Exception as e:
                    print(f"Fehler beim Analysieren der ZIP-Datei: {str(e)}")
            elif filename.endswith('.xlsx'):
                try:
                    xl_file = pd.ExcelFile(file_path)
                    for sheet_name in xl_file.sheet_names:
                        if sheet_name != 'Backup_Info':
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                            info['tables'].append({
                                'name': sheet_name,
                                'type': 'Excel Sheet',
                                'records': len(df)
                            })
                except Exception as e:
                    print(f"Fehler beim Analysieren der Excel-Datei: {str(e)}")
            return info
        except Exception as e:
            print(f"Fehler beim Abrufen der Backup-Informationen: {str(e)}")
            return None

    def get_database_stats(self):
        """Gibt Statistiken über die aktuelle Datenbank zurück"""
        try:
            stats = {
                'total_records': 0,
                'tables': [],
                'timestamp': datetime.now().isoformat()
            }
            for model_class in self.models:
                try:
                    count = model_class.query.count()
                    table_info = {
                        'name': model_class.__tablename__,
                        'model': model_class.__name__,
                        'records': count
                    }
                    stats['tables'].append(table_info)
                    stats['total_records'] += count
                except Exception as e:
                    print(f"Fehler beim Zählen von {model_class.__name__}: {str(e)}")
                    stats['tables'].append({
                        'name': model_class.__tablename__,
                        'model': model_class.__name__,
                        'records': 0,
                        'error': str(e)
                    })
            return stats
        except Exception as e:
            print(f"Fehler beim Erstellen der Datenbankstatistiken: {str(e)}")
            return {'total_records': 0, 'tables': [], 'error': str(e)}

backup_system = CSVBackupSystem()
