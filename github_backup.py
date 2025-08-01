"""
GitHub Backup-Integration für Railway Deployment
Ermöglicht das Laden von Datenbank-Backups von GitHub
"""

import os
import requests
import sqlite3
import shutil
from datetime import datetime
from io import BytesIO
import tempfile

class GitHubBackupManager:
    def __init__(self, github_repo=None, github_token=None):
        """
        GitHub Backup Manager initialisieren
        
        Args:
            github_repo: Repository im Format "owner/repo"
            github_token: GitHub Personal Access Token (optional für öffentliche Repos)
        """
        self.github_repo = github_repo or os.environ.get('GITHUB_BACKUP_REPO')
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        self.backup_folder = 'backups'
        
        if not self.github_repo:
            raise ValueError("GitHub Repository muss angegeben werden!")
    
    def list_available_backups(self):
        """
        Listet alle verfügbaren .db Backup-Dateien aus dem GitHub Repository auf
        
        Returns:
            list: Liste von Backup-Dateien mit Informationen
        """
        try:
            # GitHub API URL für Repository Contents
            api_url = f"https://api.github.com/repos/{self.github_repo}/contents/{self.backup_folder}"
            
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 404:
                # Backup-Ordner existiert nicht
                return []
            
            response.raise_for_status()
            files = response.json()
            
            # Nur .db Dateien filtern
            backup_files = []
            for file in files:
                if file['name'].endswith('.db') and file['type'] == 'file':
                    backup_files.append({
                        'name': file['name'],
                        'size': file['size'],
                        'download_url': file['download_url'],
                        'last_modified': file.get('last_modified', 'Unbekannt'),
                        'sha': file['sha']
                    })
            
            # Nach Namen sortieren (neueste zuerst, basierend auf Timestamp im Namen)
            backup_files.sort(key=lambda x: x['name'], reverse=True)
            
            return backup_files
            
        except requests.RequestException as e:
            print(f"Fehler beim Abrufen der GitHub-Backups: {e}")
            return []
    
    def download_backup(self, backup_name):
        """
        Lädt ein Backup von GitHub herunter
        
        Args:
            backup_name: Name der Backup-Datei
            
        Returns:
            BytesIO: Backup-Datei als BytesIO-Objekt oder None bei Fehler
        """
        try:
            # GitHub Raw URL für direkte Datei-Downloads
            download_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/{self.backup_folder}/{backup_name}"
            
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            response = requests.get(download_url, headers=headers)
            response.raise_for_status()
            
            backup_data = BytesIO(response.content)
            return backup_data
            
        except requests.RequestException as e:
            print(f"Fehler beim Herunterladen des Backups {backup_name}: {e}")
            return None
    
    def restore_backup(self, backup_name):
        """
        Stellt ein Backup als aktuelle Datenbank wieder her
        Automatische Erkennung von SQLite (lokal) vs PostgreSQL (Railway)
        
        Args:
            backup_name: Name der Backup-Datei
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            # Backup herunterladen
            backup_data = self.download_backup(backup_name)
            if not backup_data:
                return False
            
            # Prüfen ob Railway PostgreSQL oder lokale SQLite
            database_url = os.environ.get('DATABASE_URL')
            
            if database_url:
                # Railway PostgreSQL - SQLite zu PostgreSQL Migration
                print("Railway PostgreSQL erkannt - starte Migration...")
                return self._restore_to_postgresql(backup_data, database_url)
            else:
                # Lokale SQLite - direkter Restore
                print("Lokale SQLite erkannt - starte direkten Restore...")
                return self._restore_to_sqlite(backup_data)
            
        except Exception as e:
            print(f"Fehler beim Wiederherstellen des Backups: {e}")
            return False
    
    def _restore_to_sqlite(self, backup_data):
        """Restore für lokale SQLite Datenbank"""
        try:
            # Aktuelle Datenbank-Pfade bestimmen
            current_db_paths = [
                'instance/installation_business.db',
                os.path.join(os.path.dirname(__file__), 'instance', 'installation_business.db'),
                'installation_business.db'
            ]
            
            current_db = None
            for path in current_db_paths:
                if os.path.exists(os.path.dirname(path)) or path == 'installation_business.db':
                    current_db = path
                    break
            
            if not current_db:
                # Fallback: instance-Ordner erstellen
                os.makedirs('instance', exist_ok=True)
                current_db = 'instance/installation_business.db'
            
            # Backup der aktuellen Datenbank erstellen
            if os.path.exists(current_db):
                backup_current = current_db + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                shutil.copy2(current_db, backup_current)
                print(f"Aktuelle Datenbank gesichert als: {backup_current}")
            
            # Temporäre Datei erstellen und validieren
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_file.write(backup_data.getvalue())
                temp_db_path = temp_file.name
            
            # Validierung der heruntergeladenen Datenbank
            try:
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if not tables:
                    print("Heruntergeladene Datei ist keine gültige SQLite-Datenbank!")
                    os.unlink(temp_db_path)
                    return False
                    
                print(f"Backup validiert. Gefundene Tabellen: {len(tables)}")
                
            except sqlite3.Error as e:
                print(f"Fehler bei der Validierung der Datenbank: {e}")
                os.unlink(temp_db_path)
                return False
            
            # Neue Datenbank an die richtige Stelle kopieren
            shutil.move(temp_db_path, current_db)
            
            print(f"Backup erfolgreich als aktuelle SQLite-Datenbank wiederhergestellt!")
            return True
            
        except Exception as e:
            print(f"Fehler beim SQLite-Restore: {e}")
            return False
    
    def _restore_to_postgresql(self, backup_data, postgres_url):
        """Restore für Railway PostgreSQL - migriert von SQLite"""
        try:
            import sqlite3
            
            # SQLite Backup in temporäre Datei speichern
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_file.write(backup_data.getvalue())
                sqlite_path = temp_file.name
            
            try:
                # SQLite zu PostgreSQL Migration
                success = self._migrate_sqlite_to_postgresql(sqlite_path, postgres_url)
                
                if success:
                    print("SQLite-Backup erfolgreich zu PostgreSQL migriert!")
                    return True
                else:
                    print("Migration von SQLite zu PostgreSQL fehlgeschlagen!")
                    return False
                    
            finally:
                # Temporary SQLite file löschen
                if os.path.exists(sqlite_path):
                    os.unlink(sqlite_path)
            
        except Exception as e:
            print(f"Fehler beim PostgreSQL-Restore: {e}")
            return False
    
    def _migrate_sqlite_to_postgresql(self, sqlite_path, postgres_url):
        """Migriert SQLite-Daten zu PostgreSQL"""
        try:
            import sqlite3
            import psycopg2
            from urllib.parse import urlparse
            
            # SQLite Verbindung
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            # PostgreSQL URL parsen
            parsed = urlparse(postgres_url)
            
            # PostgreSQL Verbindung
            pg_conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading /
                user=parsed.username,
                password=parsed.password,
                sslmode='require'
            )
            pg_cursor = pg_conn.cursor()
            
            print("PostgreSQL Verbindung hergestellt")
            
            # Alle Tabellen aus SQLite lesen
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'")
            tables = [row[0] for row in sqlite_cursor.fetchall()]
            
            print(f"Gefundene Tabellen in SQLite: {tables}")
            
            # Existierende Daten in PostgreSQL löschen (in korrekter Reihenfolge wegen Foreign Keys)
            delete_order = [
                'invoice_reminder', 'quote_rejection', 'position_template_sub_item',
                'supplier_order_item', 'supplier_order', 'quote_sub_item', 'quote_item',
                'work_instruction', 'invoice', 'order', 'quote', 'customer',
                'supplier', 'position_template', 'company_settings', 'acquisition_channel',
                'login_admin'
            ]
            
            print("Lösche existierende PostgreSQL-Daten...")
            for table in delete_order:
                if table in tables:
                    try:
                        pg_cursor.execute(f"DELETE FROM {table}")
                        print(f"  ✓ {table} geleert")
                    except Exception as e:
                        print(f"  ⚠ Warnung beim Löschen von {table}: {e}")
            
            pg_conn.commit()
            
            # Daten von SQLite zu PostgreSQL migrieren
            for table_name in tables:
                print(f"Migriere Tabelle: {table_name}")
                
                # Alle Daten aus SQLite lesen
                sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"  → {table_name} ist leer, überspringe")
                    continue
                
                # Spalten ermitteln
                columns = [description[0] for description in sqlite_cursor.description]
                
                # Insert-Statement für PostgreSQL vorbereiten
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # Daten stapelweise einfügen
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    try:
                        pg_cursor.executemany(insert_sql, batch)
                        print(f"  → {len(batch)} Datensätze eingefügt")
                    except Exception as e:
                        print(f"  ✗ Fehler beim Einfügen in {table_name}: {e}")
                        # Versuche einzeln einzufügen für bessere Fehleranalyse
                        for row in batch:
                            try:
                                pg_cursor.execute(insert_sql, row)
                            except Exception as row_error:
                                print(f"    ✗ Einzelner Datensatz fehlgeschlagen: {row_error}")
                
                pg_conn.commit()
                print(f"  ✓ {table_name} komplett migriert ({len(rows)} Datensätze)")
            
            # PostgreSQL Sequences aktualisieren (wichtig für Auto-Increment)
            print("Aktualisiere PostgreSQL-Sequences...")
            for table_name in tables:
                try:
                    # Finde Primary Key Spalte
                    pg_cursor.execute(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_default LIKE 'nextval%'
                    """)
                    pk_columns = pg_cursor.fetchall()
                    
                    for (pk_column,) in pk_columns:
                        # Sequence auf höchsten Wert setzen
                        pg_cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name}")
                        max_val = pg_cursor.fetchone()[0]
                        if max_val:
                            sequence_name = f"{table_name}_{pk_column}_seq"
                            pg_cursor.execute(f"SELECT setval('{sequence_name}', {max_val})")
                            print(f"  ✓ Sequence {sequence_name} auf {max_val} gesetzt")
                            
                except Exception as e:
                    print(f"  ⚠ Sequence-Update für {table_name} fehlgeschlagen: {e}")
            
            pg_conn.commit()
            
            # Verbindungen schließen
            sqlite_conn.close()
            pg_cursor.close()
            pg_conn.close()
            
            print("✓ Migration von SQLite zu PostgreSQL erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"✗ Migration fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_backup_info(self, backup_name):
        """
        Holt detaillierte Informationen zu einem Backup
        
        Args:
            backup_name: Name der Backup-Datei
            
        Returns:
            dict: Backup-Informationen oder None
        """
        try:
            backup_data = self.download_backup(backup_name)
            if not backup_data:
                return None
            
            # Temporäre Datei für Analyse
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_file.write(backup_data.getvalue())
                temp_db_path = temp_file.name
            
            try:
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                
                # Tabellen-Info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Datensätze zählen
                record_counts = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        record_counts[table] = count
                    except sqlite3.Error:
                        record_counts[table] = "N/A"
                
                conn.close()
                
                # Dateigröße
                file_size = os.path.getsize(temp_db_path)
                
                return {
                    'name': backup_name,
                    'file_size': file_size,
                    'file_size_mb': round(file_size / 1024 / 1024, 2),
                    'tables': tables,
                    'table_count': len(tables),
                    'record_counts': record_counts,
                    'total_records': sum(count for count in record_counts.values() if isinstance(count, int))
                }
                
            finally:
                os.unlink(temp_db_path)
                
        except Exception as e:
            print(f"Fehler beim Abrufen der Backup-Informationen: {e}")
            return None

# Beispiel für Environment-Variablen in Railway:
# GITHUB_BACKUP_REPO=MaximilianEbner/Fabian-Project
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx (optional, nur bei privaten Repos)
