"""
Context processors pour le chatbot MRE
"""

def chatbot_context(request):
    """
    Ajouter les variables nécessaires pour le chatbot dans tous les templates
    """
    return {
        'chatbot_enabled': True,
        'user_is_client': request.user.is_authenticated,
        'chatbot_config': {
            'show_on_all_pages': True,
            'auto_open_for_new_users': False,
        }
    }
