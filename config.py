"""
Konfigurationsdatei für die InstallationApp
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Railway PostgreSQL URL Fix
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///installation_business.db'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload-Konfiguration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # PDF-Konfiguration
    PDF_TEMP_DIR = 'temp_pdfs'
    
    # Standard-Werte
    DEFAULT_HOURLY_RATE = 95.0
    DEFAULT_VAT_RATE = 0.20  # 20% USt
