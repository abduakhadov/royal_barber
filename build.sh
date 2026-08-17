#!/usr/bin/env bash
# Render.com build script

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Initialize zones, services and barbers
python setup_zones.py
python seed_db.py
