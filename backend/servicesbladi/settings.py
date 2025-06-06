import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import Azure-specific configuration
try:
    from azure_config import DATABASES_SSL_OPTIONS, SSL_CERT_PATH
    IS_AZURE = True
except ImportError:
    IS_AZURE = False
    SSL_CERT_PATH = os.path.join(BASE_DIR, 'BaltimoreCyberTrustRoot.crt.pem')
    DATABASES_SSL_OPTIONS = {'ssl': {'ca': SSL_CERT_PATH}}

SECRET_KEY = 'django-insecure-dj217004uhfoid4ut98h9843h98fn-dkn2f808jf9jkef'

DEBUG = False

# ALLOWED_HOSTS for Azure
ALLOWED_HOSTS = ['servicesbladi-dqf3hchmcqeudmfm.spaincentral-01.azurewebsites.net', 'servicesbladi.azurewebsites.net', '127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'channels',

    'accounts',
    'services',
    'custom_requests',
    'resources',
    'messaging',
    'chatbot',
]

AUTH_USER_MODEL = 'accounts.Utilisateur'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'servicesbladi.middleware.CacheControlMiddleware',
]

ROOT_URLCONF = 'servicesbladi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, '../frontend/template'),
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'servicesbladi.context_processors.language_context',
                'servicesbladi.context_processors.notifications_context',
                'servicesbladi.context_processors.cache_version_context',
                'chatbot.context_processors.chatbot_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'servicesbladi.wsgi.application'
ASGI_APPLICATION = 'servicesbladi.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'servicesbladi',
        'USER': 'servicesbladiadmin@servicesbladi',
        'PASSWORD': 'Aa123456a',
        'HOST': 'servicesbladi.mysql.database.azure.com',
        'PORT': '3306',
        'OPTIONS': DATABASES_SSL_OPTIONS,
    }
}

# Channels config using InMemoryChannelLayer (no Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'fr'

LANGUAGES = [
    ('fr', _('French')),
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, '../frontend/static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Use WhiteNoise for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings for production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Azure handles SSL termination
USE_TZ = True

# CSRF and session settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Cache configuration for Azure
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}

# Logging configuration for Azure
LOG_DIR = '/home/site/wwwroot/logs' if IS_AZURE else os.path.join(BASE_DIR, 'logs')

# Ensure logs directory exists
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except:
    pass  # Ignore permission errors

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'servicesbladi': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'home'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Remove this old cache config - it's been moved above
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'adval.devteam@gmail.com'
EMAIL_HOST_PASSWORD = 'oeth fank mhsn lcjr'  # Your Gmail app password
DEFAULT_FROM_EMAIL = 'Adval Services Marketplace <adval.devteam@gmail.com>'
EMAIL_SUBJECT_PREFIX = '[Adval Services] '

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
}

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

GEMINI_API_KEY = ''

COUNTRIES = [
    ('FR', _('France')),
    ('US', _('États-Unis')),
    # Add more as needed
]
