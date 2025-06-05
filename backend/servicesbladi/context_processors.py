import time
import random

def language_context(request):
    """
    Context processor that adds the current language code to the template context.
    This allows JavaScript to access the current language.
    """
    return {
        'LANGUAGE_CODE': getattr(request, 'LANGUAGE_CODE', 'fr')
    }

def notifications_context(request):
    """
    Context processor that adds unread notifications count and recent notifications
    to the template context for authenticated users.
    """
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'notifications': []
        }
    
    # Import here to avoid circular imports
    from custom_requests.models import Notification
    
    # Get unread notifications count
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Get recent notifications (limit to 5)
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    return {
        'unread_notifications_count': unread_count,
        'notifications': notifications
    }

def cache_version_context(request):
    """
    Add cache version information to the template context
    to prevent cached pages from different versions.
    """
    # Timestamp actuel si pas encore défini
    if not hasattr(request, 'request_time'):
        request.request_time = int(time.time())
    
    # Version de cache si pas dans la session
    if 'cache_version' not in request.session:
        cache_version = f"{request.request_time}.{random.randint(1000, 9999)}"
        request.session['cache_version'] = cache_version
        request.session.modified = True
    
    return {
        'cache_version': request.session.get('cache_version', ''),
        'request_time': request.request_time,
        'timestamp': int(time.time()),
    }