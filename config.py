"""
Konfigurationsdatei für die InstallationApp
"""
import os

def get_database_url():
    """Ermittelt die korrekte Datenbank-URL für lokale und Railway-Umgebung"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Railway PostgreSQL
        # Fix für SQLAlchemy 1.4+ (postgres:// -> postgresql://)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        print(f"✓ Using Railway PostgreSQL Database")
        return database_url
    else:
        # Lokale SQLite Entwicklung
        print(f"✓ Using Local SQLite Database")
        return 'sqlite:///instance/installation_business.db'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Automatische Datenbank-Erkennung
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Railway PostgreSQL spezifische Einstellungen
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 20,
            'max_overflow': 0,
        }
    
    # Upload-Konfiguration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # PDF-Konfiguration
    PDF_TEMP_DIR = 'temp_pdfs'
    
    # Standard-Werte
    DEFAULT_HOURLY_RATE = 95.0
    DEFAULT_VAT_RATE = 0.20  # 20% USt
