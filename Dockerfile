FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Fix line endings and make the entrypoint script executable
RUN dos2unix docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Create instance directory and set permissions
RUN mkdir -p instance && chmod 777 instance

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=wsgi.py

# Use our entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
