import os
import sys
from pathlib import Path

# Add the project root directory to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_root)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')

# Configure Django
import django
django.setup()

# Import WSGI application
from shirsti_printing.wsgi import application

# Run migrations on Vercel startup
if os.environ.get('VERCEL') == '1':
    from django.core.management import execute_from_command_line
    from django.db import connection
    
    # Check if migrations have been run by checking if tables exist
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        except:
            # Tables don't exist, run migrations
            try:
                execute_from_command_line(['manage.py', 'migrate', '--noinput'])
                execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
            except Exception as e:
                print(f"Migration/collectstatic error: {e}")

# Export the app for Vercel
app = application