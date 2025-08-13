"""
Test settings for the blog app
"""

# Test database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Disable migrations during tests for faster execution
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
DEBUG = False
SECRET_KEY = "test-secret-key-for-blog-tests"

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}

# Test middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Test templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Test apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.blog",
    "apps.users",
    "apps.notifications",
]

# Test user model
AUTH_USER_MODEL = "users.CustomUser"

# Test static files
STATIC_URL = "/static/"
STATIC_ROOT = "/tmp/static/"

# Test media files
MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/media/"

# Test cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Test email backend
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Test file uploads
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

# Test session
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Test timezone
USE_TZ = True
TIME_ZONE = "UTC"
