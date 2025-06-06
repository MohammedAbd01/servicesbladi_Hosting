# servicesbladi Azure Deployment Configuration

This file contains the deployment settings and commands for Azure Web App.

## Azure Web App Configuration

**App Name:** servicesbladi
**Resource Group:** Adval
**Location:** Spain Central
**Runtime:** Python 3.10
**App Service Plan:** P1v2

## Environment Variables (Set these in Azure Portal)

```bash
DJANGO_SETTINGS_MODULE=servicesbladi.settings
PYTHONPATH=/home/site/wwwroot
WEBSITE_HTTPLOGGING_RETENTION_DAYS=3
```

## Database Configuration

- **Type:** Azure Database for MySQL
- **Server:** servicesbladi.mysql.database.azure.com
- **Database:** servicesbladi
- **SSL:** Required with BaltimoreCyberTrustRoot.crt.pem

## Static Files

- Static files are served using WhiteNoise
- Media files are handled through Django
- All files are collected during deployment

## Startup Command

The startup.txt file contains the commands that Azure runs when starting the app:
```bash
python manage.py migrate --noinput
python manage.py createcachetable --noinput  
python manage.py collectstatic --noinput
gunicorn servicesbladi.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
```

## Deployment Process

1. GitHub Actions builds the app
2. Runs migrations and collects static files
3. Packages everything for deployment
4. Deploys to Azure Web App using OIDC authentication

## Security Features

- SSL redirect disabled (Azure handles SSL termination)
- Secure cookies enabled
- XSS protection enabled
- Content type sniffing disabled

## Monitoring

- Logs are written to `/home/site/wwwroot/logs/django.log`
- Console logs are available in Azure Portal
- Application insights can be added for advanced monitoring
