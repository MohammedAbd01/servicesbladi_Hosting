from django.contrib import messages
import time
import random
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

class MessageMiddleware(MiddlewareMixin):
    """Middleware for processing message-related tasks"""

    def process_request(self, request):
        if request.user.is_authenticated:
            # Set last active timestamp
            if hasattr(request.user, 'last_active'):
                request.user.last_active = timezone.now()
                request.user.save(update_fields=['last_active'])

        return None

class CacheControlMiddleware(MiddlewareMixin):
    """Middleware to control browser caching of static files"""
    
    def process_request(self, request):
        # Générer un timestamp unique pour cette requête
        request.request_time = int(time.time())
        
        # Toujours générer une nouvelle version pour le cache à chaque requête
        cache_version = f"{int(time.time())}.{random.randint(1000, 9999)}"
        request.session['cache_version'] = cache_version
        request.session['request_time'] = request.request_time
        request.session.modified = True
        
        # Ajouter un indicateur si c'est une requête WebSocket
        if request.path.startswith('/ws/'):
            request.is_websocket = True
            
        return None
    
    def process_response(self, request, response):
        # Ajouter des en-têtes no-cache pour toutes les réponses HTML
        if response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['X-Accel-Expires'] = '0'  # Pour Nginx
            
            # Ajouter un ETag aléatoire pour forcer le rechargement
            response['ETag'] = f'W/"{time.time()}-{random.randint(1000, 9999)}"'
            
        # Aussi pour JS, CSS, JSON et autres ressources importantes
        elif response.get('Content-Type', '').startswith(('text/css', 'application/javascript', 'application/json')):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        # Pour les WebSockets, s'assurer qu'ils ne sont pas mis en cache non plus
        if getattr(request, 'is_websocket', False):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
        
        return response
