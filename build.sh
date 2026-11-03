#!/usr/bin/env bash
# Render build command: install packages, collect static files and apply migrations
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
