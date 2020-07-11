

from .settings import *


DEBUG = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
AUTH_PASSWORD_VALIDATORS = []


# Faster, less secure hashing for testing only
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

