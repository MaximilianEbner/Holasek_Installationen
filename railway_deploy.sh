#!/bin/bash
# Railway Deployment Script
# Dieses Skript wird automatisch von Railway ausgeführt

echo "🚀 Starting Railway Deployment..."

# Datenbank initialisieren (falls noch nicht geschehen)
echo "📊 Initializing database..."
python init_railway_db.py

echo "✅ Deployment complete!"
