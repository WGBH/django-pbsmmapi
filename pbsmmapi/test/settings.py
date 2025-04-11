import os

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

STATIC_ROOT = os.path.join(PROJECT_ROOT, "tests", "test-static")
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "tests", "test-media")
MEDIA_URL = "/media/"

TIME_ZONE = "Asia/Tokyo"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DATABASE_NAME", ":memory:"),
        "USER": os.environ.get("DATABASE_USER", ""),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", ""),
        "PORT": os.environ.get("DATABASE_PORT", ""),
        "TEST": {"NAME": os.environ.get("DATABASE_NAME", "")},
    }
}


SECRET_KEY = "not needed"

ROOT_URLCONF = "pbsmmapi.test.urls"

STATIC_URL = "/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Default storage settings
# https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-STORAGES
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

if os.environ.get("STATICFILES_STORAGE", "") == "manifest":
    STORAGES["staticfiles"][
        "BACKEND"
    ] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


USE_TZ = True

LANGUAGE_CODE = "en"

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
                "django.template.context_processors.request",
            ],
            "debug": True,  # required in order to catch template errors
        },
    },
]

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

INSTALLED_APPS = [
    "pbsmmapi",
    "pbsmmapi.asset",
    "pbsmmapi.episode",
    "pbsmmapi.season",
    "pbsmmapi.show",
    "pbsmmapi.special",
    "pbsmmapi.franchise",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
]


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache",
    }
}

PASSWORD_HASHERS = (
    "django.contrib.auth.hashers.MD5PasswordHasher",  # don't use the intentionally slow default password hasher
)

ALLOWED_HOSTS = [
    "localhost",
    "testserver",
    "other.example.com",
    "127.0.0.1",
    "0.0.0.0",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

PBSMM_API_ID = os.getenv("PBSMM_API_ID")
PBSMM_API_SECRET = os.getenv("PBSMM_API_SECRET")

HUEY = {
    "huey_class": "huey.MemoryHuey",  # Huey implementation to use.
    # 'name': settings.DATABASES['default']['NAME'],  # Use db name for huey.
    "results": True,  # Store return values of tasks.
    "store_none": False,  # If a task returns None, do not save to results.
    "immediate": True,
    "utc": True,  # Use UTC for all times internally.
    "blocking": True,  # Perform blocking pop rather than poll Redis.
    "consumer": {
        "workers": 1,
        "worker_type": "thread",
        "initial_delay": 0.1,  # Smallest polling interval, same as -d.
        "backoff": 1.15,  # Exponential backoff using this rate, -b.
        "max_delay": 10.0,  # Max possible polling interval, -m.
        "scheduler_interval": 1,  # Check schedule every second, -s.
        "periodic": True,  # Enable crontab feature.
        "check_worker_health": True,  # Enable worker health checks.
        "health_check_interval": 1,  # Check worker health every second.
    },
}
