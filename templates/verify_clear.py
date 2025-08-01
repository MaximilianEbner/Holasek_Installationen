#!/usr/bin/env python3
from app import app, db
from models import Quote, Order, Invoice

with app.app_context():
    print(f"Angebote: {Quote.query.count()}")
    print(f"Aufträge: {Order.query.count()}")
    print(f"Rechnungen: {Invoice.query.count()}")
