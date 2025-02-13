#!/bin/sh
set -e

echo "Starting deployment..."

# Navigate to the project directory
cd /home/milav/docker-projects/vardhan-flask

# Pull latest changes
echo "Pulling latest changes..."
git fetch origin
git reset --hard origin/master

# Stop and remove containers and volumes
echo "Cleaning up old containers and volumes..."
docker compose down -v

# Rebuild and start containers
echo "Rebuilding and starting containers..."
docker compose up -d --build

# Wait for the application to start
echo "Waiting for application to start..."
sleep 10

# Check container status
echo "Checking container status..."
docker compose ps

# Show recent logs
echo "Recent logs:"
docker compose logs --tail 50

echo "Deployment completed!"
