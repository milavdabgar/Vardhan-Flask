#!/bin/bash
set -e

echo "Starting initialization..."

# Create instance directory if it doesn't exist
mkdir -p /app/instance
chmod 777 /app/instance

echo "Running database migrations..."
# Initialize/upgrade the database
flask db upgrade || (flask db init && flask db migrate -m "initial migration" && flask db upgrade)

echo "Initializing database with default data..."
# Initialize database with default data
python init_database.py

echo "Starting application..."
# Start the application
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
