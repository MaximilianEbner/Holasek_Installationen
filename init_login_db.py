from app import app, db

# Initialisiere die Datenbank mit allen Tabellen
with app.app_context():
    db.create_all()
    print("Datenbank mit LoginAdmin-Tabelle initialisiert!")
