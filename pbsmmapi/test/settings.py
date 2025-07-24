import multiprocessing
import os
from pathlib import Path

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
PROJECT_ROOT = Path(__file__).resolve(strict=True).parent.parent
WEBROOT = PROJECT_ROOT.parent.joinpath(".ephemeral", "webroot")

USE_TZ = True
TIME_ZONE = "America/New_York"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["PGDATABASE"],
        "USER": os.environ["PGUSER"],
        "PASSWORD": os.environ["PGPASSWORD"],
        "HOST": os.environ["PGHOST"],
        "PORT": os.environ["PGPORT"],
        "OPTIONS": {
            "pool": True,
        },
    },
}

SECRET_KEY = "not needed"

ROOT_URLCONF = "pbsmmapi.test.urls"

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

STATIC_ROOT = WEBROOT / "static"
STATIC_URL = "/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

MEDIA_ROOT = WEBROOT / "media"
MEDIA_URL = "/media/"

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
            "debug": True,
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
    "pbsmmapi.changelog",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "huey.contrib.djhuey",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    }
}

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

ALLOWED_HOSTS = [
    "localhost",
    "testserver",
    "127.0.0.1",
    "0.0.0.0",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

PBSMM_API_ID = os.getenv("PBSMM_API_ID")
PBSMM_API_SECRET = os.getenv("PBSMM_API_SECRET")

PBSMM_SHOW_SLUGS = []

HUEY = {
    "huey_class": "huey.RedisHuey",
    "name": "mmhuey",
    "results": True,
    "store_none": False,
    "immediate": False,
    "utc": True,
    "blocking": True,
    "connection": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "connection_pool": None,
        "read_timeout": 1,
        "url": None,
    },
    "consumer": {
        "workers": int(multiprocessing.cpu_count() / 2),
        "worker_type": "thread",
        "initial_delay": 0.1,
        "backoff": 1.15,
        "max_delay": 10.0,
        "scheduler_interval": 1,
        "periodic": True,
        "check_worker_health": True,
        "health_check_interval": 1,
    },
}
