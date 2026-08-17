#!/usr/bin/env bash
# Render.com build script

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
