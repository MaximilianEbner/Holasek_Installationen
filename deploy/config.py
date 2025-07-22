"""
Production-ready Konfiguration für Railway Deployment
"""
import os

class Config:
    # Sicherheit
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key-change-this'
    
    # Datenbank - Immer SQLite verwenden (wie früher)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///installation_business.db'
    print(f"DEBUG: Using SQLite: {SQLALCHEMY_DATABASE_URI}")  # Debug-Ausgabe
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
