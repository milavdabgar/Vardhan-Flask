#!/bin/bash
set -e

# Create instance directory if it doesn't exist
mkdir -p /app/instance
chmod 777 /app/instance

# Initialize/upgrade the database
flask db upgrade || flask db init && flask db migrate -m "initial migration" && flask db upgrade

# Initialize database with default data
python init_database.py

# Start the application
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
