# Gunicorn configuration for Azure App Service
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 60
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/home/site/wwwroot/logs/gunicorn_access.log"
errorlog = "/home/site/wwwroot/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "servicesbladi_gunicorn"

# Server mechanics
daemon = False
pidfile = "/home/site/wwwroot/logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
