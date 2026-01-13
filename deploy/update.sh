#!/bin/bash
# Script to update the application on AWS server

echo "========================================="
echo "Updating Shristi Printing Application"
echo "========================================="

# 1. Pull latest changes
echo "Pulling latest changes from GitHub..."
git pull origin main

# 2. Update dependencies (just in case)
echo "Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements/production.txt

# 3. Run migrations
echo "Running database migrations..."
python manage.py migrate

# 4. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 5. Fix permissions (Critical for Nginx)
echo "Fixing permissions..."
sudo chown -R ubuntu:www-data staticfiles media static
sudo chmod -R 755 staticfiles media static

# 6. Restart services
echo "Restarting application services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "========================================="
echo "Update Completed Successfully!"
echo "========================================="
