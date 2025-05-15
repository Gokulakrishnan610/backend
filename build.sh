#!/usr/bin/env bash

# Exit on error
set -o errexit

# Set environment variables
export ENVIRONMENT="production"
export DJANGO_SETTINGS_MODULE="UniversityApp.settings"
export SECRET_KEY="your-secret-key-here"
export COOKIE_DOMAIN="render.com"
export JWT_KEY="your-jwt-key-here"

# For initial deployment, use SQLite to simplify testing
export USE_SQLITE="True"

# Install dependencies
pip install -r requirements.txt

# Install gunicorn explicitly
pip install gunicorn

# Add gunicorn to PATH
export PATH="$PATH:$HOME/.local/bin"

# Create static directory if it doesn't exist
mkdir -p static

# Create log directory if it doesn't exist
mkdir -p log

# Collect static files
python manage.py collectstatic --noinput

# Create a fresh database instead of using the included one
# This will avoid foreign key issues
echo "Creating a fresh database..."
rm -f dump-1.sqlite3
touch dump-1.sqlite3

# Run migrations to set up the schema
echo "Running migrations on fresh database..."
python manage.py migrate --run-syncdb

# Create admin user and seed basic data
echo "Creating admin user..."
python manage.py create_admin

# Optionally seed some basic data for testing
echo "Seeding basic data..."
python manage.py seed_departments
python manage.py seed_rooms
# Add other seed commands as needed 