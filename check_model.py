#!/usr/bin/env python3
"""
Überprüfe die PositionTemplate Datenbankstruktur
"""
from app import app
from models import db, PositionTemplate

with app.app_context():
    print('Checking PositionTemplate model...')
    template = PositionTemplate.query.first()
    print(f'Template exists: {template is not None}')

    if template:
        print(f'Template ID: {template.id}')
        print(f'Template name: {template.name}')
        print(f'Has enable_length: {hasattr(template, "enable_length")}')
        print(f'enable_length value: {getattr(template, "enable_length", "NOT_FOUND")}')
        print(f'enable_width value: {getattr(template, "enable_width", "NOT_FOUND")}')
        print(f'enable_height value: {getattr(template, "enable_height", "NOT_FOUND")}')
        print(f'enable_area value: {getattr(template, "enable_area", "NOT_FOUND")}')
        print(f'enable_volume value: {getattr(template, "enable_volume", "NOT_FOUND")}')
        
        # Alle enable_* Attribute anzeigen
        enable_attrs = [attr for attr in dir(template) if not attr.startswith('_') and 'enable' in attr]
        print('Enable attributes:', enable_attrs)
    else:
        print('No templates found in database')

    # Check available columns in the table
    print('\nChecking table schema...')
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = inspector.get_columns('position_templates')
    column_names = [col['name'] for col in columns]
    print('Available columns:', column_names)
