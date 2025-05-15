#!/usr/bin/env bash
# Exit on error
set -o errexit

# Set environment variables
export ENVIRONMENT="production"
export DJANGO_SETTINGS_MODULE="UniversityApp.settings"
export SECRET_KEY="your-secret-key-here"
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

# Create superuser
echo "Creating admin user..."
python -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(email='admin@university.com', password='admin123', first_name='Admin', last_name='User') if not User.objects.filter(email='admin@university.com').exists() else print('Admin user already exists')" || echo "Failed to create superuser, but continuing build"

# Optionally seed some basic data for testing
echo "Seeding basic data..."
