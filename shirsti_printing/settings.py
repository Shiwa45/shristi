# shirsti_printing/settings.py
import importlib
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel environment detection
IS_VERCEL = os.environ.get('VERCEL') == '1'

# Security settings
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')
DEBUG = config('DEBUG', default=True, cast=bool) and not IS_VERCEL

allowed_hosts = config('ALLOWED_HOSTS', default='')
ALLOWED_HOSTS = ['*'] if DEBUG else [host.strip() for host in allowed_hosts.split(',') if host.strip()]
if not ALLOWED_HOSTS and not DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',
    'crispy_forms',
    'crispy_tailwind',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.services',
    'apps.design_tool',
    'apps.orders',
    'apps.templates_mgmt',
    'apps.pricing',
    'apps.notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if importlib.util.find_spec('whitenoise') is not None:
    MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'shirsti_printing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.services.context_processors.services_menu_context',
                'apps.core.context_processors.site_settings_context',
                'apps.orders.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'shirsti_printing.wsgi.application'

# Database
if IS_VERCEL and os.environ.get('DB_HOST'):
    # Use PostgreSQL on Vercel if credentials are provided
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'verceldb'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
elif IS_VERCEL:
    # Use temporary SQLite on Vercel (in writable /tmp directory)
    # Note: Data won't persist across deployments
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',
        }
    }
elif config('DB_ENGINE', default='') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    # Use SQLite for local dev or simple EC2 deployments
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = Path(config('STATIC_ROOT', default=BASE_DIR / 'staticfiles'))

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(config('MEDIA_ROOT', default=BASE_DIR / 'media'))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Django Allauth
SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@shirsti.com')

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379')

# CORS settings
cors_allowed_origins = config('CORS_ALLOWED_ORIGINS', default='')
CORS_ALLOWED_ORIGINS = (
    [origin.strip() for origin in cors_allowed_origins.split(',') if origin.strip()]
    or [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'] if IS_VERCEL else ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Add file logging for local development only
if not IS_VERCEL:
    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': log_dir / 'django.log',
    }
    LOGGING['loggers']['django']['handlers'] = ['file', 'console']

# Third-party API Keys
PIXABAY_API_KEY = config('PIXABAY_API_KEY', default='27347-23fd1708b1c4f768195a5093b')
UNSPLASH_ACCESS_KEY = config('UNSPLASH_ACCESS_KEY', default='5746b12f75e91c251bddf6f83bd2ad0d658122676e9bd2444e110951f9a04af8')
PEXELS_API_KEY = config('PEXELS_API_KEY', default='563492ad6f9170000100000147b95f140fe441b858072ac5940c9ba0')
