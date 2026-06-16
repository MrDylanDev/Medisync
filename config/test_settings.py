"""
Test settings for Medisync.

Overrides the database to use SQLite in-memory for testing.
This avoids requiring a running MySQL server during test execution.
"""
from .settings import *  # noqa: F403

# Use SQLite for tests (avoids requiring MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashers to speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use console email for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
