import os
import sys
from pathlib import Path

# Add the project root directory to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_root)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')

# Configure Django FIRST
import django
django.setup()

# Now run migrations on Vercel before anything else
if os.environ.get('VERCEL') == '1':
    try:
        from django.core.management import call_command
        from django.db import connection
        from django.db.utils import OperationalError
        
        # Try to run migrations silently
        try:
            call_command('migrate', '--noinput', verbosity=0)
        except Exception as e:
            print(f"Migration attempted (may already be complete): {e}")
    except Exception as e:
        print(f"Migration check error: {e}")

# Import WSGI application
from shirsti_printing.wsgi import application

# Export the app for Vercel
app = application