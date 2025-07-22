"""
Konfigurationsdatei für die InstallationApp
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a7f8d9e2b1c4567890abcdef12345678901234567890abcdef1234567890abc'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///installation_business.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload-Konfiguration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # PDF-Konfiguration
    PDF_TEMP_DIR = 'temp_pdfs'
    
    # Standard-Werte
    DEFAULT_HOURLY_RATE = 95.0
    DEFAULT_VAT_RATE = 0.20  # 20% USt
