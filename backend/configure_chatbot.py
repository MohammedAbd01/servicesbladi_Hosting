#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servicesbladi.settings')

# Setup Django
django.setup()

from chatbot.models import ChatbotConfiguration

def configure_chatbot():
    print("🤖 Configuration du Chatbot MRE avec Gemini Flash 2.5")
    print("=" * 60)
    
    # Configure Gemini API key
    api_key_config, created = ChatbotConfiguration.objects.get_or_create(key='gemini_api_key')
    api_key_config.value = 'AIzaSyBnAN-9SaKCxzv25gcPRho50prMV1nANqc'
    api_key_config.save()
    print("✅ Clé API Gemini configurée")
    
    # Set model to Gemini Flash 2.5
    model_config, created = ChatbotConfiguration.objects.get_or_create(key='gemini_model')
    model_config.value = 'gemini-2.0-flash-exp'
    model_config.save()
    print("✅ Modèle configuré: Gemini Flash 2.5")
    
    # Enable chatbot
    enabled_config, created = ChatbotConfiguration.objects.get_or_create(key='chatbot_enabled')
    enabled_config.value = 'true'
    enabled_config.save()
    print("✅ Chatbot activé")
    
    # Update welcome message for MRE
    welcome_config, created = ChatbotConfiguration.objects.get_or_create(key='welcome_message')
    welcome_config.value = """Bienvenue ! Je suis votre assistant IA spécialisé pour les services aux Marocains Résidant à l'Étranger (MRE).

Je peux vous aider avec :
🏛️ **Administration** - Procédures consulaires, documents officiels
💰 **Fiscalité** - Impôts, déclarations, conventions fiscales  
🏠 **Immobilier** - Achat, vente, investissement au Maroc
📈 **Investissement** - Opportunités, réglementation
🎓 **Formation** - Programmes, certifications

Comment puis-je vous aider aujourd'hui ?"""
    welcome_config.save()
    print("✅ Message de bienvenue MRE configuré")
    
    # Set timeout and limits
    timeout_config, created = ChatbotConfiguration.objects.get_or_create(key='response_timeout_seconds')
    timeout_config.value = '30'
    timeout_config.save()
    
    max_messages_config, created = ChatbotConfiguration.objects.get_or_create(key='max_messages_per_session')
    max_messages_config.value = '50'
    max_messages_config.save()
    print("✅ Paramètres de performance configurés")
    
    # Enable feedback
    feedback_config, created = ChatbotConfiguration.objects.get_or_create(key='feedback_enabled')
    feedback_config.value = 'true'
    feedback_config.save()
    print("✅ Système de feedback activé")
    
    print("\n" + "=" * 60)
    print("🎉 CHATBOT MRE COMPLÈTEMENT ACTIVÉ!")
    print("🌐 Test disponible sur: http://127.0.0.1:8080/test-chatbot/")
    print("🚀 Widget visible sur toutes les pages du site")

if __name__ == '__main__':
    configure_chatbot()
