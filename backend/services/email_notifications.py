"""
Email notification service for ServicesBladi
Handles all email notifications with beautiful templates
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service to handle email notifications with templates"""
    
    @staticmethod
    def send_templated_email(template_name, context, subject, recipient_email, sender_email=None):
        """
        Send a templated email
        """
        try:
            # Use default sender if not provided
            if not sender_email:
                sender_email = settings.DEFAULT_FROM_EMAIL
            
            # Render email templates
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = render_to_string(f'emails/{template_name}.txt', context)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=f"{settings.EMAIL_SUBJECT_PREFIX}{subject}",
                body=text_content,
                from_email=sender_email,
                to=[recipient_email]
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully to {recipient_email} with template {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_new_message_notification(sender, recipient, message_content, request_title=None):
        """Send notification for new message"""
        context = {
            'recipient_name': f"{recipient.name} {recipient.first_name}",
            'sender_name': f"{sender.name} {sender.first_name}",
            'message_content': message_content,
            'request_title': request_title,
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com'
        }
        
        subject = _("Nouveau message reçu")
        return EmailNotificationService.send_templated_email(
            'new_message',
            context,
            subject,
            recipient.email
        )
    
    @staticmethod
    def send_request_status_update(client, expert, request_obj, new_status):
        """Send notification when request status changes"""
        context = {
            'client_name': f"{client.name} {client.first_name}",
            'expert_name': f"{expert.name} {expert.first_name}" if expert else "L'équipe",
            'request_title': request_obj.title,
            'request_description': request_obj.description,
            'new_status': request_obj.get_status_display(),
            'status_class': new_status.lower(),
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com'
        }
        
        subject = _("Mise à jour de votre demande")
        return EmailNotificationService.send_templated_email(
            'request_status_update',
            context,
            subject,
            client.email
        )
    
    @staticmethod
    def send_expert_assignment_notification(expert, request_obj):
        """Send notification when expert is assigned to a request"""
        context = {
            'expert_name': f"{expert.name} {expert.first_name}",
            'client_name': f"{request_obj.client.user.name} {request_obj.client.user.first_name}",
            'request_title': request_obj.title,
            'request_description': request_obj.description,
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com'
        }
        
        subject = _("Nouvelle demande assignée")
        return EmailNotificationService.send_templated_email(
            'expert_assignment',
            context,
            subject,
            expert.email
        )
    
    @staticmethod
    def send_appointment_notification(client, expert, appointment, notification_type='created'):
        """Send notification for appointment events"""
        context = {
            'client_name': f"{client.name} {client.first_name}",
            'expert_name': f"{expert.name} {expert.first_name}",
            'appointment_date': appointment.date_time.strftime("%d/%m/%Y"),
            'appointment_time': appointment.date_time.strftime("%H:%M"),
            'appointment_type': appointment.get_meeting_type_display(),
            'notification_type': notification_type,
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com'
        }
        
        if notification_type == 'created':
            subject = _("Nouveau rendez-vous confirmé")
            template = 'appointment_created'
            recipient_email = client.email
        elif notification_type == 'reminder':
            subject = _("Rappel: Rendez-vous demain")
            template = 'appointment_reminder'
            recipient_email = client.email
        elif notification_type == 'expert_assigned':
            subject = _("Nouveau rendez-vous assigné")
            template = 'appointment_expert_assigned'
            recipient_email = expert.email
        else:
            return False
        
        return EmailNotificationService.send_templated_email(
            template,
            context,
            subject,
            recipient_email
        )
    
    @staticmethod
    def send_document_uploaded_notification(uploader, recipient, document, request_obj=None):
        """Send notification when a document is uploaded"""
        context = {
            'recipient_name': f"{recipient.name} {recipient.first_name}",
            'uploader_name': f"{uploader.name} {uploader.first_name}",
            'document_name': document.name,
            'document_type': document.get_type_display(),
            'request_title': request_obj.title if request_obj else None,
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com'
        }
        
        subject = _("Nouveau document ajouté")
        return EmailNotificationService.send_templated_email(
            'document_uploaded',
            context,
            subject,
            recipient.email
        )    @staticmethod
    def send_welcome_email(user, password=None):
        """Send welcome email to new users"""
        context = {
            'user_name': f"{user.name} {user.first_name}",
            'user_type': user.get_account_type_display(),
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com',
            'password': password,  # Include password if provided (for admin-created users)
            'is_admin_created': password is not None
        }
        
        subject = _("Bienvenue sur Services Bladi")
        return EmailNotificationService.send_templated_email(
            'welcome',
            context,
            subject,
            user.email
        )
    
    @staticmethod
    def send_verification_email(user, verification_url):
        """Send email verification email to new users"""
        context = {
            'user_name': f"{user.name} {user.first_name}",
            'verification_url': verification_url,
            'site_name': 'Services Bladi',
            'site_url': 'https://servicesbladi.com'
        }
        
        subject = _("Vérifiez votre adresse email - Services Bladi")
        return EmailNotificationService.send_templated_email(
            'verification',
            context,
            subject,
            user.email
        )
