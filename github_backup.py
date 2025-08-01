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
            
            print(f"Backup {backup_name} erfolgreich als aktuelle Datenbank wiederhergestellt!")
            return True
            
        except Exception as e:
            print(f"Fehler beim Wiederherstellen des Backups: {e}")
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
