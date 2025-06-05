"""
Commande de gestion Django pour initialiser les configurations du chatbot
"""

from django.core.management.base import BaseCommand
from chatbot.models import ChatbotConfiguration


class Command(BaseCommand):
    help = 'Initialise les configurations par défaut du chatbot MRE'

    def handle(self, *args, **options):
        configs = [
            {
                'key': 'gemini_api_key',
                'value': 'AIzaSyBnAN-9SaKCxzv25gcPRho50prMV1nANqc',
                'description': 'Clé API Gemini Flash 2.5 pour le chatbot'
            },            {
                'key': 'chatbot_enabled',
                'value': 'true',
                'description': 'Activer/désactiver le chatbot sur le site'
            },
            {
                'key': 'gemini_model',
                'value': 'gemini-2.0-flash-exp',
                'description': 'Modèle Gemini à utiliser (Flash 2.5)'
            },{
                'key': 'welcome_message',
                'value': 'Bienvenue ! Je suis votre assistant spécialisé pour les services aux Marocains Résidant à l\'Étranger.',
                'description': 'Message de bienvenue du chatbot'
            },
            {
                'key': 'max_messages_per_session',
                'value': '50',
                'description': 'Nombre maximum de messages par session'
            },
            {
                'key': 'response_timeout_seconds',
                'value': '30',
                'description': 'Délai d\'attente pour les réponses API en secondes'
            },
            {
                'key': 'auto_escalation_keywords',
                'value': 'problème,urgent,réclamation,plainte,erreur,bug',
                'description': 'Mots-clés déclenchant une escalade automatique'
            },
            {
                'key': 'feedback_enabled',
                'value': 'true',
                'description': 'Activer le système de feedback sur les réponses'
            }
        ]

        created_count = 0
        updated_count = 0

        for config_data in configs:
            config, created = ChatbotConfiguration.objects.get_or_create(
                key=config_data['key'],
                defaults={
                    'value': config_data['value'],
                    'description': config_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Configuration créée: {config.key}')
                )
            else:
                # Mettre à jour la description si elle a changé
                if config.description != config_data['description']:
                    config.description = config_data['description']
                    config.save()
                    updated_count += 1
                
                self.stdout.write(
                    self.style.WARNING(f'ⓘ Configuration existante: {config.key}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Initialisation terminée: {created_count} créées, {updated_count} mises à jour'
            )
        )
