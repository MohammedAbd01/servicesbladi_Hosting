from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from accounts.models import Utilisateur, Expert, Client
from custom_requests.models import ServiceRequest, Document, RendezVous, Message, Notification
from services.email_notifications import EmailNotificationService

@login_required
def expert_documents_view(request):
    """View function for expert document management."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get documents associated with this expert
        documents = Document.objects.filter(
            Q(service_request__expert=expert.user) |
            Q(rendez_vous__expert=expert.user) |
            Q(uploaded_by=request.user)
        ).distinct().order_by('-upload_date')
        
        context = {
            'documents': documents,
            'expert': expert
        }
        
        return render(request, 'expert/documents_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointments_view(request):
    """View function for expert appointments."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
        
    try:
        expert = Expert.objects.get(user=request.user)
        # Get appointments for this expert
        appointments = RendezVous.objects.filter(
            expert=expert.user
        ).order_by('date_time')
        
        # Get all clients for the form dropdown
        clients = Client.objects.all()
        
        context = {
            'appointments': appointments,
            'expert': expert,
            'clients': clients        }
        
        return render(request, 'expert/rendezvous.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_messages_view(request):
    """View function for expert messages."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get all clients who have had appointments or service requests with this expert
        clients = Client.objects.filter(
            Q(servicerequest__expert=expert.user) |
            Q(rendezvous__expert=expert.user)
        ).distinct()
        
        # Get active client if any
        active_client_id = request.GET.get('client')
        active_client = None
        messages = []
        
        if active_client_id:
            active_client = get_object_or_404(Client, id=active_client_id)
            
            # Get messages between expert and client
            messages = Message.objects.filter(
                (Q(sender=request.user) & Q(recipient=active_client.user)) |
                (Q(sender=active_client.user) & Q(recipient=request.user))
            ).order_by('sent_at')
            
            # Mark messages as read
            unread_messages = messages.filter(recipient=request.user, is_read=False)
            for message in unread_messages:
                message.is_read = True
                message.save()
        
        context = {
            'clients': clients,
            'active_client': active_client,
            'messages': messages,
            'expert': expert
        }
        
        return render(request, 'expert/messages.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointment_detail(request, appointment_id):
    """View function for expert appointment detail."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointment details
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=expert.user)
        
        # Get documents related to this appointment
        documents = Document.objects.filter(rendez_vous=appointment).order_by('-upload_date')
        
        context = {
            'appointment': appointment,
            'documents': documents,
            'expert': expert
        }
        
        return render(request, 'expert/appointment_detail.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_appointment_detail(request, appointment_id):
    """View function for expert appointment detail."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointment details
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=expert.user)
        
        # Get documents related to this appointment
        documents = Document.objects.filter(rendez_vous=appointment).order_by('-upload_date')
        
        context = {
            'appointment': appointment,
            'documents': documents,
            'expert': expert
        }
        
        return render(request, 'expert/appointment_detail.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')
        
        return render(request, 'expert/messages_new.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_requests_view(request):
    """View function for expert requests."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get service requests assigned to this expert
        assigned_requests = ServiceRequest.objects.filter(
            expert=expert.user
        ).order_by('-created_at')
        
        # Get unassigned service requests that experts can take
        unassigned_requests = ServiceRequest.objects.filter(
            expert__isnull=True,
            status='new'  # Only show new requests that need experts
        ).order_by('-created_at')
        
        context = {
            'assigned_requests': assigned_requests,
            'unassigned_requests': unassigned_requests,
            'expert': expert
        }
        
        return render(request, 'expert/demandes.html', context)
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_resources_view(request):
    """View function for expert resources."""
    print(f"=== EXPERT RESOURCES VIEW DEBUG ===")
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"Account type: {getattr(request.user, 'account_type', 'No account_type')}")
    
    if request.user.account_type.lower() not in ['expert', 'admin']:
        print(f"Access denied - redirecting to home")
        return redirect('home')

    try:
        if request.user.account_type.lower() == 'expert':
            expert = Expert.objects.get(user=request.user)
            print(f"Expert found: {expert}")
        else:
            expert = None
            print(f"Admin user - no expert profile needed")
        
        # Import here to avoid circular import
        from resources.models import Resource, ResourceFile, ResourceLink
        
        # Get filter parameters
        category = request.GET.get('category', '')
        search_query = request.GET.get('search', '')
        sort_by = request.GET.get('sort', 'recent')
        
        # Base queryset
        resources = Resource.objects.all()
        
        # Apply filters
        if category:
            resources = resources.filter(category=category)
            
        if search_query:
            resources = resources.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Apply sorting
        if sort_by == 'name':
            resources = resources.order_by('title')
        elif sort_by == 'popular':
            resources = resources.order_by('-view_count')
        else:  # default to recent
            resources = resources.order_by('-created_at')
        
        # Get resource categories for filtering
        resource_categories = Resource.CATEGORIES
        
        context = {
            'resources': resources,
            'expert': expert,
            'resource_categories': resource_categories,
            'formats': Resource.FORMAT_TYPES,
            'current_category': category,
            'current_search': search_query,
            'current_sort': sort_by
        }
        
        return render(request, 'expert/ressources.html', context)
    
    except Expert.DoesNotExist:
        messages.error(request, _('Expert profile not found.'))
        return redirect('home')
    except Exception as e:
        messages.error(request, _(f'An error occurred: {str(e)}'))
        return redirect('home')

@login_required
def expert_request_detail(request, request_id):
    """View to display detailed information about a specific service request for expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    try:        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Get client information including phone number
        client = get_object_or_404(Utilisateur, id=service_request.client.id)
        
        # Get service type information
        service = service_request.service
        service_type = service.service_type if hasattr(service, 'service_type') else None
        
        # Get documents for this service request
        documents = Document.objects.filter(service_request=service_request).order_by('-upload_date')
        
        # Get messages related to this service request
        messages_list = Message.objects.filter(service_request=service_request).order_by('sent_at')
        
        # Get appointments related to this service request
        appointments = RendezVous.objects.filter(service_request=service_request).order_by('date_time')
        
        context = {
            'service_request': service_request,
            'documents': documents,
            'messages_list': messages_list,
            'appointments': appointments,
            'client': client,
            'service_type': service_type        }
        
        return render(request, 'expert/request_detail.html', context)
    
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('expert_demandes')

@login_required
def expert_send_message(request):
    """Handle sending a message from expert to client or admin"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        service_request_id = request.POST.get('service_request_id')
        
        if not recipient_id or not content:
            messages.error(request, "Le destinataire et le contenu sont obligatoires.")
            if service_request_id:
                return redirect('expert_request_detail', request_id=service_request_id)
            return redirect('expert_demandes')
        
        # Get the recipient
        recipient = get_object_or_404(Utilisateur, id=recipient_id)
        
        # Get the service request if available
        service_request = None
        if service_request_id:
            service_request = get_object_or_404(ServiceRequest, id=service_request_id)
            
            # Check if this expert is assigned to this request
            if service_request.expert != request.user:
                messages.error(request, "Vous n'êtes pas autorisé à envoyer des messages pour cette demande.")
                return redirect('expert_demandes')
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content,
            service_request=service_request
        )
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('Nouveau message'),
            content=_(f'Vous avez reçu un nouveau message de {request.user.first_name} {request.user.name}.'),
            related_message=message,
            related_service_request=service_request
        )
        
        messages.success(request, _('Message envoyé avec succès.'))
        
        # Redirect back to appropriate page
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi du message: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_upload_document(request):
    """Handle document upload from expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        name = request.POST.get('name')
        document_type = request.POST.get('type')
        service_request_id = request.POST.get('service_request_id')
        
        if not name or not document_type or not service_request_id or 'file' not in request.FILES:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('expert_request_detail', request_id=service_request_id)
        
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=service_request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à télécharger des documents pour cette demande.")
            return redirect('expert_demandes')
        
        # Get the file
        file = request.FILES['file']
        
        # Create the document
        document = Document.objects.create(
            name=name,
            type=document_type,
            service_request=service_request,
            uploaded_by=request.user,
            file=file
        )
          # Create notification for client
        Notification.objects.create(
            user=service_request.client,
            type='document',
            title=_('Nouveau document'),
            content=_(f'Un nouveau document "{name}" a été téléchargé pour votre demande "{service_request.title}".'),
            related_service_request=service_request
        )
        
        # Send email notification to client
        EmailNotificationService.send_document_uploaded_notification(
            request.user, service_request.client, document, service_request
        )
        
        messages.success(request, _('Document téléchargé avec succès.'))
        
        return redirect('expert_request_detail', request_id=service_request_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement du document: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_update_request_status(request, request_id):
    """Update the status of a service request by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_request_detail', request_id=request_id)
    
    try:
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à mettre à jour cette demande.")
            return redirect('expert_demandes')
        
        # Get the new status
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        # Verify that the status is valid for experts
        valid_statuses = ['in_progress', 'pending_info', 'completed']
        if new_status not in valid_statuses:
            messages.error(request, "Statut invalide.")
            return redirect('expert_request_detail', request_id=request_id)
        
        # Update the request status
        service_request.status = new_status
        service_request.save()
        
        # Add comment as message if provided
        if comment:
            Message.objects.create(
                sender=request.user,
                recipient=service_request.client,
                content=_('Statut mis à jour: ') + comment,
                service_request=service_request
            )
          # Create notification for client
        status_display = dict(ServiceRequest.STATUS_CHOICES).get(new_status, new_status)
        Notification.objects.create(
            user=service_request.client,
            type='request_update',
            title=_('Statut de demande mis à jour'),
            content=_(f'Le statut de votre demande "{service_request.title}" a été mis à jour à "{status_display}".'),
            related_service_request=service_request
        )
        
        # Send email notification to client
        EmailNotificationService.send_request_status_update(
            service_request.client, request.user, service_request, new_status
        )
        
        messages.success(request, _('Statut mis à jour avec succès.'))
        
        return redirect('expert_request_detail', request_id=request_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la mise à jour du statut: {str(e)}")
        return redirect('expert_request_detail', request_id=request_id)

@login_required
def expert_schedule_appointment(request):
    """Handle scheduling of appointment by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        service_request_id = request.POST.get('service_request_id')
        date_time_str = request.POST.get('date_time')
        duration = request.POST.get('duration')
        appointment_type = request.POST.get('type')
        notes = request.POST.get('notes', '')
        
        if not service_request_id or not date_time_str or not duration or not appointment_type:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('expert_request_detail', request_id=service_request_id)
        
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=service_request_id)
        
        # Check if this expert is assigned to this request
        if service_request.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à planifier des rendez-vous pour cette demande.")
            return redirect('expert_demandes')
        
        # Convert date_time from string to datetime
        from datetime import datetime
        date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        
        # Create the appointment
        appointment = RendezVous.objects.create(
            client=service_request.client,
            expert=request.user,
            service_request=service_request,
            date_time=date_time,
            duration=duration,
            type=appointment_type,
            notes=notes,
            status='scheduled'
        )
          # Create notification for client
        Notification.objects.create(
            user=service_request.client,
            type='appointment',
            title=_('Nouveau rendez-vous'),
            content=_(f'Un rendez-vous a été planifié pour votre demande "{service_request.title}" le {date_time.strftime("%d/%m/%Y à %H:%M")}.'),
            related_service_request=service_request
        )
        
        # Send email notification to client about new appointment
        EmailNotificationService.send_appointment_notification(
            client=service_request.client,
            expert=request.user,
            appointment=appointment,
            notification_type='created'
        )
        
        messages.success(request, _('Rendez-vous planifié avec succès.'))
        
        return redirect('expert_request_detail', request_id=service_request_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la planification du rendez-vous: {str(e)}")
        if service_request_id:
            return redirect('expert_request_detail', request_id=service_request_id)
        return redirect('expert_demandes')

@login_required
def expert_update_appointment(request):
    """Handle updating of appointment status by expert"""
    
    # Check if user is expert
    if request.user.account_type.lower() != 'expert':
        return redirect('home')
    
    if request.method != 'POST':
        return redirect('expert_demandes')
    
    try:
        # Get form data
        appointment_id = request.POST.get('appointment_id')
        status = request.POST.get('status')
        
        if not appointment_id or not status:
            messages.error(request, "L'identifiant du rendez-vous et le statut sont obligatoires.")
            return redirect('expert_demandes')
        
        # Get the appointment
        appointment = get_object_or_404(RendezVous, id=appointment_id)
        
        # Check if this expert is assigned to this appointment
        if appointment.expert != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à mettre à jour ce rendez-vous.")
            return redirect('expert_demandes')
        
        # Check if status is valid
        if status not in ['completed', 'cancelled']:
            messages.error(request, "Statut invalide.")
            return redirect('expert_request_detail', request_id=appointment.service_request.id)
        
        # Update the appointment status
        appointment.status = status
        appointment.save()
          # Create notification for client
        status_display = 'terminé' if status == 'completed' else 'annulé'
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Statut de rendez-vous mis à jour'),
            content=_(f'Votre rendez-vous du {appointment.date_time.strftime("%d/%m/%Y à %H:%M")} a été marqué comme {status_display}.'),
            related_service_request=appointment.service_request
        )
        
        # Send email notification to client about appointment status update
        if status == 'completed':
            # Use document upload template for completed appointments since we don't have a specific completion template
            EmailNotificationService.send_request_status_update(
                client=appointment.client,
                request_obj=appointment.service_request if appointment.service_request else None,
                new_status='completed',
                updated_by=request.user
            )
        elif status == 'cancelled':
            # For cancelled appointments, we'll use the appointment notification with a custom message
            context = {
                'client_name': f"{appointment.client.name} {appointment.client.first_name}",
                'expert_name': f"{request.user.name} {request.user.first_name}",
                'appointment_date': appointment.date_time.strftime("%d/%m/%Y"),
                'appointment_time': appointment.date_time.strftime("%H:%M"),
                'cancellation_reason': 'Annulé par l\'expert',
                'site_name': 'Services Bladi',
                'site_url': 'https://servicesbladi.com'
            }
            
            EmailNotificationService.send_templated_email(
                'appointment_cancelled',
                context,
                _("Rendez-vous annulé"),
                appointment.client.email
            )
        
        messages.success(request, _(f'Rendez-vous marqué comme {status_display} avec succès.'))
        
        return redirect('expert_request_detail', request_id=appointment.service_request.id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la mise à jour du rendez-vous: {str(e)}")
        return redirect('expert_demandes')

@login_required
def expert_take_request(request, request_id):
    """Allow an expert to take an unassigned service request"""
    if request.user.account_type.lower() != 'expert':
        messages.error(request, _("Vous n'avez pas les permissions nécessaires."))
        return redirect('home')
    
    try:
        # Get the expert profile
        expert = Expert.objects.get(user=request.user)
        
        # Get the service request
        service_request = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check if the request is already assigned
        if service_request.expert:
            messages.error(request, _("Cette demande est déjà assignée à un expert."))
            return redirect('expert_demandes')
        
        # Assign the request to this expert
        service_request.expert = request.user
        service_request.status = 'in_progress'  # Automatically change status to in progress
        service_request.save()
        
        # Create a notification for the client
        Notification.objects.create(
            user=service_request.client,
            type='request_update',
            title=_('Expert assigné'),
            content=_(f'Un expert ({request.user.first_name} {request.user.name}) a pris en charge votre demande "{service_request.title}".'),
            related_service_request=service_request
        )
        
        # Send a message to the client
        Message.objects.create(
            sender=request.user,
            recipient=service_request.client,
            content=_(f"Bonjour, je suis {request.user.first_name} {request.user.name}, l'expert qui va prendre en charge votre demande. Je vais l'examiner et vous contacter prochainement."),
            service_request=service_request
        )
        
        messages.success(request, _(f"Vous avez pris en charge la demande '{service_request.title}' avec succès."))
          # Redirect to the request detail page
        return redirect('expert_request_detail', request_id=request_id)
        
    except Expert.DoesNotExist:
        messages.error(request, _("Profil d'expert introuvable."))
        return redirect('home')
    except Exception as e:
        messages.error(request, _(f"Une erreur s'est produite: {str(e)}"))
        return redirect('expert_demandes')
