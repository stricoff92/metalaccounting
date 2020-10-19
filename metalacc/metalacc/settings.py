
import os

from .applocals import (
    SECRET_KEY as _SECRET_KEY,
    OBJECT_SERIALIZATION_KEY as _OBJECT_SERIALIZATION_KEY,
    OBJECT_SIGNING_KEY as _OBJECT_SIGNING_KEY,
    ADDITIONAL_ALLOWED_HOSTS,
    ENV,
    DB_NAME,
    DB_HOSTNAME,
    DB_USERNAME,
    DB_PASSWORD,
)
from metalacc import applocals

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


TMP_DIR_PATH = "/tmp/"


SECRET_KEY = _SECRET_KEY

# data for exporting objects
OBJECT_SERIALIZATION_KEY = _OBJECT_SERIALIZATION_KEY
OBJECT_SIGNING_KEY = _OBJECT_SIGNING_KEY
OBJECT_SERIALIZATION_VERSION = 1
OBJECT_SERIALIZATION_SUPPORTED_VERSIONS = (1, )
JWT_ALGORITHM = "HS256"

DEBUG = ENV == 'DEV' or ENV == 'TESTING'


SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

if DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost'] + ADDITIONAL_ALLOWED_HOSTS
else:
    ALLOWED_HOSTS = ADDITIONAL_ALLOWED_HOSTS


protocol = "http://" if DEBUG else "https://"
BASE_ABSOLUTE_URL = protocol + ALLOWED_HOSTS[0]
if DEBUG:
    BASE_ABSOLUTE_URL += ":8000"


# Application definition

INSTALLED_APPS = [
    'api.apps.ApiConfig',
    'website.apps.WebsiteConfig',
    'docs.apps.DocsConfig',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django_extensions',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Allow django to serve static files in staging environment
if ENV == "STAGING":
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")


ROOT_URLCONF = 'metalacc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'metalacc.wsgi.application'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamp': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "logs", "django_info.log"),
            'formatter': 'timestamp',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "logs", "django_error.log"),
            'formatter': 'timestamp',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_info', 'file_error'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'HOST': DB_HOSTNAME,
        'USER': DB_USERNAME,
        'PASSWORD': DB_PASSWORD,
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/django_cache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': 'localhost:6379',
            'KEY_PREFIX':f'metalacc-{ENV}',
        },
    }


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
] if not DEBUG else []

LOGIN_URL = '/'



AUTHENTICATION_BACKENDS = [
    'metalacc.email_backend.EmailBackend'
]


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# EMAIL SETTINGS
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
elif ENV == 'PROD':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = applocals.EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = applocals.EMAIL_HOST_PASSWORD
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = 'noreply@metalaccounting.com'



LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "website/templates/static"),
]


if ENV == "STAGING":
    # Directory for whitenoise to serve static files from.
    STATIC_ROOT = os.path.join(BASE_DIR, "staging_static_root")
elif ENV == "PROD":
    # Directory for webserver to serve static files from.
    STATIC_ROOT = "/var/www/metalacc/static/"


# Number of characters in each slug
SLUG_LENGTH = 10


SHOW_DOCS = getattr(applocals, "SHOW_DOCS", True)
