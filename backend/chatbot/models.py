from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ChatSession(models.Model):
    """Session de chat pour tracking des conversations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.user or 'Anonyme'}"


class ChatMessage(models.Model):
    """Messages du chat MRE"""
    MESSAGE_TYPES = [
        ('user', 'Utilisateur'),
        ('bot', 'Assistant MRE'),
        ('system', 'Système'),
    ]

    DOMAIN_CATEGORIES = [
        ('fiscalite', 'Fiscalité'),
        ('immobilier', 'Immobilier'),
        ('investissement', 'Investissement'),
        ('administration', 'Administration'),
        ('formation', 'Formation professionnelle'),
        ('other', 'Autre'),
        ('off_topic', 'Hors sujet'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    domain_category = models.CharField(max_length=20, choices=DOMAIN_CATEGORIES, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Métadonnées pour analytics
    response_time_ms = models.IntegerField(null=True, blank=True)  # Temps de réponse API
    api_model_used = models.CharField(max_length=50, default='gemini-2.0-flash-exp')

    class Meta:
        ordering = ['-timestamp']
        db_table = 'chatbot_chatmessage'
        # Force UTF8MB4 charset for emoji support
        options = {
            'charset': 'utf8mb4',
            'collate': 'utf8mb4_unicode_ci'
        }
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Flags pour le support
    is_escalated = models.BooleanField(default=False)
    needs_human_review = models.BooleanField(default=False)
    satisfaction_rating = models.IntegerField(null=True, blank=True)  # 1-5

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.get_message_type_display()} - {self.content[:50]}..."


class ChatFeedback(models.Model):
    """Feedback utilisateur sur les réponses du chatbot"""
    FEEDBACK_TYPES = [
        ('helpful', 'Utile'),
        ('not_helpful', 'Pas utile'),
        ('incorrect', 'Incorrect'),
        ('incomplete', 'Incomplet'),
    ]

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Feedback: {self.get_feedback_type_display()} - {self.message.id}"


class ChatAnalytics(models.Model):
    """Analytics et métriques du chatbot"""
    date = models.DateField()
    total_sessions = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    
    # Métriques par domaine
    fiscalite_questions = models.IntegerField(default=0)
    immobilier_questions = models.IntegerField(default=0)
    investissement_questions = models.IntegerField(default=0)
    administration_questions = models.IntegerField(default=0)
    formation_questions = models.IntegerField(default=0)
    off_topic_questions = models.IntegerField(default=0)
    
    # Métriques de performance
    avg_response_time_ms = models.FloatField(null=True, blank=True)
    escalation_rate = models.FloatField(null=True, blank=True)
    satisfaction_avg = models.FloatField(null=True, blank=True)
    
    # Conversions
    signups_from_chat = models.IntegerField(default=0)
    service_requests_from_chat = models.IntegerField(default=0)

    class Meta:
        unique_together = ['date']
        ordering = ['-date']

    def __str__(self):
        return f"Analytics {self.date} - {self.total_sessions} sessions"


class ChatbotConfiguration(models.Model):
    """Configuration du chatbot"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"Config: {self.key}"

    @classmethod
    def get_value(cls, key, default=None):
        """Récupérer une valeur de configuration"""
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description="", user=None):
        """Définir une valeur de configuration"""
        config, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'updated_by': user
            }
        )
        if not created:
            config.value = value
            config.description = description
            config.updated_by = user
            config.save()
        return config
