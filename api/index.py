import os
import sys

# Add the project root directory to the sys.path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shirsti_printing.settings')

# Import the handler from django-vercel
from django_vercel import handler