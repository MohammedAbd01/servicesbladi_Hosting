# Django app configuration for Azure App Service
import os

# SSL certificate path for Azure App Service
SSL_CERT_PATH = '/home/site/wwwroot/BaltimoreCyberTrustRoot.crt.pem'

# Database configuration with disabled SSL to allow non-secure connections
# This is only recommended for development/testing purposes
DATABASES_SSL_OPTIONS = {
    'ssl': False,  # Disable SSL entirely
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
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
