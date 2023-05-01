"""
Django settings for myportal project.

Generated by 'django-admin startproject' using Django 3.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import logging
from pathlib import Path
from django.template import context_processors
from myportal import fields

log = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep all secret keys used in production secret!
# You can generate a secure secret key with `openssl rand -hex 32`
SECRET_KEY = 'django-insecure-47f(ub2qs-n!b@&&)tis&l$&qf1%^@&jy-95jx!bahqrm^19m2'
# Your portal credentials for enabling user login via Globus Auth
SOCIAL_AUTH_GLOBUS_KEY = ''
SOCIAL_AUTH_GLOBUS_SECRET = ''

# ALLAUTH
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {
    "cilogon": {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        "APP": {
            "client_id": "cilogon:/client_id/34d8b8c1560547fa1023ceacc000dd96",
            "secret": "CeAUGYES8B0mWiU9cD-OP0nUD_Ajkv51dhQVqezltgigcim_SliiFzpiAHibNQnrkIP7wPP-MOm9XDxVd1mnaQ",
            "key": ""
        },
        # These are provider-specific settings that can only be
        # listed here:
        "SCOPE": [
            "openid", "email", "profile", "org.cilogon.userinfo"
        ],
        "AUTH_PARAMS": {
            "access_type": "offline",
        },
        "VERIFIED_EMAIL": True,
    }
}
ACCOUNT_EMAIL_REQUIRED = True

# This is a general Django setting if views need to redirect to login
# https://docs.djangoproject.com/en/3.2/ref/settings/#login-url
LOGIN_URL = '/login/cilogon'
# LOGIN_URL = '/login/globus'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/profile/'

# This dictates which scopes will be requested on each user login
SOCIAL_AUTH_GLOBUS_SCOPE = [
    'urn:globus:auth:scope:search.api.globus.org:all',
]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ["https://geoedf-portal.anvilcloud.rcac.purdue.edu"]

PROJECT_TITLE = 'GeoEDF'
SEARCH_INDEXES = {
    'schema-org-index': {
        'uuid': '15a6acc8-3a23-42ed-98cf-a32833acaae3',
        'name': 'Schema.org Json Index',
        'template_override_dir': 'schema-org-index',
        'fields': [
            ('extension', fields.extension),
            ('size_bytes', fields.size_bytes),
            ('name', fields.name),
            # ('creator', fields.creator_name),
            # ('creative_work_status', fields.creative_work_status),
            ('id', fields.identifier),
        ],
        'facets': [  # limit of 3 facets
            {
                'name': 'Creator',
                'field_name': 'schemaorgJson.creator.@list.name',
                'size': 10,
                'type': 'terms'
            },
            {
                'name': 'Tags',
                'field_name': 'tags',
                'size': 10,
                'type': 'terms'
            },
            {
                'name': 'Extension',
                'field_name': 'extension',
                'size': 10,
                'type': 'terms'
            },
            # {
            #     'name': 'File Size (Bytes)',
            #     'type': 'numeric_histogram',
            #     'field_name': 'size_bytes',
            #     'size': 10,
            #     'histogram_range': {'low': 5000, 'high': 10000},
            # },
            # {
            #     "name": "Dates",
            #     "field_name": "dateModified",
            #     "type": "date_histogram",
            #     "date_interval": "hour",
            # },

        ],
    }
}

SITE_ID = 1
# SITE_NAME = 'geoedf.sample.com'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'globus_portal_framework',
    'social_django',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'drf_yasg',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.cilogon',

    'myportal',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'globus_portal_framework.middleware.ExpiredTokenMiddleware',
    'globus_portal_framework.middleware.GlobusAuthExceptionMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

# Authentication backends setup OAuth2 handling and where user data should be
# stored
AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    # 'allauth.socialaccount.providers.cilogon',
    'globus_portal_framework.auth.GlobusOpenIdConnect',
    'django.contrib.auth.backends.ModelBackend',
]

ACCOUNT_EMAIL_VERIFICATION = 'none'

SWAGGER_SETTINGS = {
   'SECURITY_DEFINITIONS': {
      'Basic': {
            'type': 'basic'
      },
      'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
      }
   }
}

ROOT_URLCONF = 'myportal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myportal' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'globus_portal_framework.context_processors.globals',
            ],
        },
    },
]

WSGI_APPLICATION = 'myportal.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LOGGING = {
    'version': 1,
    'handlers': {
        'stream': {'level': 'DEBUG', 'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {'handlers': ['stream'], 'level': 'INFO'},
        'globus_portal_framework': {'handlers': ['stream'], 'level': 'INFO'},
        'myportal': {'handlers': ['stream'], 'level': 'INFO'},
    },
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "myportal" / "static",
    BASE_DIR / "myportal" / "templates",
    'static/',
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

try:
    from .local_settings import *
except ImportError:
    expected_path = Path(__file__).resolve().parent / 'local_settings.py'
    log.warning(f'You should create a file for your secrets at {expected_path}')
