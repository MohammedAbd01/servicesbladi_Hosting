from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def safe_content(content):
    """Safely process message content to prevent crashes and XSS"""
    if not content:
        return ""
    
    # Limit content length to prevent memory issues
    content = str(content)[:5000]  # 5k char limit
    
    # Escape HTML to prevent XSS
    content = escape(content)
    
    # Handle line breaks
    content = content.replace('\n', '<br>')
    
    return mark_safe(content)

@register.filter
def truncate_messages(messages, limit=50):
    """Limit number of messages to prevent performance issues"""
    if not messages:
        return messages
    
    # Convert to list if QuerySet and limit
    return list(messages)[-limit:] if hasattr(messages, '__iter__') else messages
