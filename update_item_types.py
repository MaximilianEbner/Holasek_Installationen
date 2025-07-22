from app import app, db
from models import PositionTemplateSubItem

# Aktualisiere alle item_type Werte auf die korrekte Schreibweise
with app.app_context():
    subitems = PositionTemplateSubItem.query.all()
    updates = 0
    
    for item in subitems:
        if item.item_type == 'bestellteil':
            item.item_type = 'Bestellteil'
            updates += 1
        elif item.item_type == 'arbeitsvorgang':
            item.item_type = 'Arbeitsvorgang'
            updates += 1
        elif item.item_type == 'sonstiges':
            item.item_type = 'Sonstiges'
            updates += 1
    
    db.session.commit()
    print(f'Aktualisiert: {updates} Einträge')
    
    # Zeige die aktualisierten Werte
    import sqlalchemy as sa
    result = PositionTemplateSubItem.query.with_entities(
        PositionTemplateSubItem.item_type, 
        sa.func.count(PositionTemplateSubItem.id)
    ).group_by(PositionTemplateSubItem.item_type).all()
    
    print('Neue Typen in der Datenbank:')
    for typ, count in result:
        print(f'  {typ}: {count}x')
