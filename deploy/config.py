"""
Production-ready Konfiguration für Railway Deployment
"""
import os

class Config:
    # Sicherheit
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key-change-this'
    
    # Datenbank - PostgreSQL für Railway, SQLite für lokale Entwicklung
    DATABASE_URL = os.environ.get('DATABASE_URL')
    print(f"DEBUG: DATABASE_URL = {DATABASE_URL}")  # Debug-Ausgabe
    
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        # Railway/Heroku PostgreSQL URL fix
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        print(f"DEBUG: Fixed DATABASE_URL = {DATABASE_URL}")  # Debug-Ausgabe
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///installation_business.db'
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI = {SQLALCHEMY_DATABASE_URI}")  # Debug-Ausgabe
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PDF-Konfiguration
    PDF_TEMP_DIR = 'temp_pdfs'
    
    # Standard-Werte
    DEFAULT_HOURLY_RATE = 95.0
    DEFAULT_VAT_RATE = 0.20  # 20% USt
    
    # Production Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 Stunde
    
    # Session-Konfiguration
    PERMANENT_SESSION_LIFETIME = 3600  # 1 Stunde
    SESSION_COOKIE_SECURE = True if os.environ.get('DATABASE_URL') else False  # HTTPS in Production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
