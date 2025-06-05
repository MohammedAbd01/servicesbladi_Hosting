from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import ChatSession, ChatMessage, ChatFeedback, ChatAnalytics, ChatbotConfiguration


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at', 'message_count', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['session_id', 'user__username', 'user__email']
    readonly_fields = ['session_id', 'created_at', 'ip_address', 'user_agent']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            message_count=Count('messages')
        )
    
    def message_count(self, obj):
        return obj.message_count
    message_count.short_description = 'Messages'
    message_count.admin_order_field = 'message_count'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'message_type', 'domain_category', 'content_preview', 'timestamp', 'response_time_ms']
    list_filter = ['message_type', 'domain_category', 'timestamp', 'is_escalated', 'needs_human_review']
    search_fields = ['content', 'session__session_id']
    readonly_fields = ['timestamp', 'response_time_ms']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Contenu'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'feedback_type', 'created_at', 'has_comment']
    list_filter = ['feedback_type', 'created_at']
    search_fields = ['comment', 'message__content']
    readonly_fields = ['created_at', 'ip_address']
    
    def has_comment(self, obj):
        return bool(obj.comment)
    has_comment.boolean = True
    has_comment.short_description = 'Commentaire'


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_sessions', 'total_messages', 'unique_users',
        'top_domain', 'avg_response_time_ms', 'satisfaction_avg'
    ]
    list_filter = ['date']
    readonly_fields = ['date']
    
    def top_domain(self, obj):
        domains = {
            'Fiscalité': obj.fiscalite_questions,
            'Immobilier': obj.immobilier_questions,
            'Investissement': obj.investissement_questions,
            'Administration': obj.administration_questions,
            'Formation': obj.formation_questions,
            'Hors sujet': obj.off_topic_questions,
        }
        top = max(domains.items(), key=lambda x: x[1])
        return f"{top[0]} ({top[1]})"
    top_domain.short_description = 'Domaine principal'


@admin.register(ChatbotConfiguration)
class ChatbotConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_active', 'updated_at', 'updated_by']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['updated_at']
    
    def value_preview(self, obj):
        if len(obj.value) > 50:
            return obj.value[:50] + "..."
        return obj.value
    value_preview.short_description = 'Valeur'
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Actions personnalisées
@admin.action(description='Marquer comme nécessitant une révision humaine')
def mark_for_human_review(modeladmin, request, queryset):
    queryset.update(needs_human_review=True)


@admin.action(description='Marquer comme escaladé')
def mark_as_escalated(modeladmin, request, queryset):
    queryset.update(is_escalated=True)


# Ajouter les actions aux modèles appropriés
ChatMessageAdmin.actions = [mark_for_human_review, mark_as_escalated]
