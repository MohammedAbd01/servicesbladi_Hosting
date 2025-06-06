# Django app configuration for Azure App Service
import os

# SSL certificate path for Azure App Service
SSL_CERT_PATH = '/home/site/wwwroot/BaltimoreCyberTrustRoot.crt.pem'

# Database configuration with proper SSL handling
if os.path.exists(SSL_CERT_PATH):
    DATABASES_SSL_OPTIONS = {
        'ssl': {'ca': SSL_CERT_PATH}
    }
else:
    # Fallback if cert file is not found
    DATABASES_SSL_OPTIONS = {
        'ssl': {'ssl_disabled': False}
    }

# Static files configuration for Azure
AZURE_STATIC_ROOT = '/home/site/wwwroot/staticfiles'
AZURE_MEDIA_ROOT = '/home/site/wwwroot/media'

# Logging for Azure App Service
AZURE_LOGS_DIR = '/home/site/wwwroot/logs'
if not os.path.exists(AZURE_LOGS_DIR):
    try:
        os.makedirs(AZURE_LOGS_DIR, exist_ok=True)
    except:
        pass  # Ignore permission errors in Azure
