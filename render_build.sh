#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Gather all static assets
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate
