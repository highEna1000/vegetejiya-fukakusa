#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running database migration..."
python migrate_db.py

echo "Build completed successfully!"