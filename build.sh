#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

# 本番環境用の設定
export SKIP_DB_INIT=false

echo "Running database migration..."
python migrate_db.py

echo "Build completed successfully!"