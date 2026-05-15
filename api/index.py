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

# Export the app for Vercel
app = application