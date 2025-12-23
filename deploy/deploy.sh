#!/bin/bash

# Deployment script for Shristi Printing on AWS EC2
# Run this script on the AWS server after cloning the repository

set -e  # Exit on error

echo "========================================="
echo "Shristi Printing Deployment Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ubuntu/shristi"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"

# Step 1: Update system packages
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Step 2: Install system dependencies
echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
sudo apt install -y python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib libpq-dev git

# Step 3: Create project directories
echo -e "${YELLOW}Step 3: Creating project directories...${NC}"
mkdir -p $LOG_DIR
mkdir -p $PROJECT_DIR/staticfiles
mkdir -p $PROJECT_DIR/media

# Step 4: Set up Python virtual environment
echo -e "${YELLOW}Step 4: Setting up Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate

# Step 5: Install Python dependencies
echo -e "${YELLOW}Step 5: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements/production.txt
pip install gunicorn psycopg2-binary python-dotenv

# Step 6: Set up environment variables
echo -e "${YELLOW}Step 6: Setting up environment variables...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env
    echo -e "${RED}IMPORTANT: Edit .env file with your actual credentials!${NC}"
    echo "Run: nano $PROJECT_DIR/.env"
fi

# Step 7: Set up database (SQLite for simplicity)
echo -e "${YELLOW}Step 7: Setting up database...${NC}"
python manage.py migrate

# Step 8: Collect static files
echo -e "${YELLOW}Step 8: Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Step 9: Create superuser (optional, interactive)
echo -e "${YELLOW}Step 9: Create superuser (optional)...${NC}"
echo "Do you want to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python manage.py createsuperuser
fi

# Step 10: Set up Gunicorn service
echo -e "${YELLOW}Step 10: Setting up Gunicorn service...${NC}"
sudo cp $PROJECT_DIR/deploy/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn --no-pager

# Step 11: Set up Nginx
echo -e "${YELLOW}Step 11: Setting up Nginx...${NC}"
sudo cp $PROJECT_DIR/deploy/nginx.conf /etc/nginx/sites-available/shristi
sudo ln -sf /etc/nginx/sites-available/shristi /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager

# Step 12: Set up firewall
echo -e "${YELLOW}Step 12: Configuring firewall...${NC}"
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# Step 13: Set proper permissions
echo -e "${YELLOW}Step 13: Setting proper permissions...${NC}"
sudo chown -R ubuntu:ubuntu $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Your application should now be running at: http://13.61.189.208"
echo ""
echo "Useful commands:"
echo "  - View Gunicorn logs: sudo journalctl -u gunicorn -f"
echo "  - View Nginx logs: sudo tail -f /var/log/nginx/shristi_error.log"
echo "  - Restart Gunicorn: sudo systemctl restart gunicorn"
echo "  - Restart Nginx: sudo systemctl restart nginx"
echo ""
echo -e "${YELLOW}Don't forget to edit .env file with your actual credentials!${NC}"
