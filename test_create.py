#!/usr/bin/env python3
"""
Teste das Erstellen einer neuen PositionTemplate
"""
from app import app
from models import db, PositionTemplate

with app.app_context():
    print('Testing PositionTemplate creation...')
    
    # Simuliere das Erstellen einer neuen Vorlage wie in create_template
    new_template = PositionTemplate(
        name="Test Template",
        description="Test Description",
        enable_length=True,
        enable_width=True,
        enable_height=False,
        enable_area=True,
        enable_volume=False
    )
    
    db.session.add(new_template)
    db.session.commit()
    
    print(f'Template created with ID: {new_template.id}')
    print(f'enable_length: {new_template.enable_length}')
    print(f'enable_width: {new_template.enable_width}')
    print(f'enable_height: {new_template.enable_height}')
    print(f'enable_area: {new_template.enable_area}')
    print(f'enable_volume: {new_template.enable_volume}')
    
    # Lade die Vorlage erneut aus der DB
    reloaded_template = PositionTemplate.query.get(new_template.id)
    print('\nReloaded from DB:')
    print(f'enable_length: {reloaded_template.enable_length}')
    print(f'enable_width: {reloaded_template.enable_width}')
    print(f'enable_height: {reloaded_template.enable_height}')
    print(f'enable_area: {reloaded_template.enable_area}')
    print(f'enable_volume: {reloaded_template.enable_volume}')
    
    # Lösche die Test-Vorlage wieder
    db.session.delete(new_template)
    db.session.commit()
    print(f'\nTest template deleted')
