#!/bin/bash
# MediCare Deployment Script

set -e

PROJECT_DIR="/home/ubuntu/Hostpital_management"
VENV="$PROJECT_DIR/venv"

echo "=== MediCare Deployment Script ==="

# Activate virtual environment
source "$VENV/bin/activate"

cd "$PROJECT_DIR"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Create required directories
mkdir -p /var/log/gunicorn /var/run/gunicorn
chown -R ubuntu:ubuntu /var/log/gunicorn /var/run/gunicorn

# Link systemd service
echo "Linking systemd service..."
sudo ln -sf "$PROJECT_DIR/systemd/medicare.service" /etc/systemd/system/medicare.service
sudo systemctl daemon-reload

# Enable and start service
echo "Starting Gunicorn..."
sudo systemctl enable medicare
sudo systemctl restart medicare

# Link nginx config
echo "Configuring Nginx..."
sudo ln -sf "$PROJECT_DIR/nginx/medicare" /etc/nginx/sites-enabled/medicare
sudo nginx -t && sudo systemctl reload nginx

echo "=== Deployment Complete ==="
echo "Access your app at: http://3.237.67.226"
