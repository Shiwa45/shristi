#!/bin/bash
# Quick fix for static files on AWS

echo "Fixing static files configuration..."

# 1. Collect static files
cd /home/ubuntu/shristi
source venv/bin/activate
python manage.py collectstatic --noinput

# 2. Set proper permissions
sudo chown -R ubuntu:www-data /home/ubuntu/shristi/staticfiles
sudo chown -R ubuntu:www-data /home/ubuntu/shristi/static
sudo chmod -R 755 /home/ubuntu/shristi/staticfiles
sudo chmod -R 755 /home/ubuntu/shristi/static

# 3. Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# 4. Check Nginx error log
echo "Checking Nginx error log..."
sudo tail -20 /var/log/nginx/shristi_error.log

echo "Done! Check http://13.61.189.208/static/admin/css/base.css to verify"
