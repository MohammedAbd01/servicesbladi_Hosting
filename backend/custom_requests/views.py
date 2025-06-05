from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import os
import mimetypes
import logging

from accounts.models import Utilisateur, Client, Expert
from services.models import Service, ServiceCategory
from .models import ServiceRequest, RendezVous, Document, Message, Notification
from services.email_notifications import EmailNotificationService

# Client request management views
@login_required
def client_requests_view(request):
    """Display client's service requests with filtering"""
    try:
        # Vérifier si l'utilisateur est un client
        client = Client.objects.get(user=request.user)
        
        # Récupérer les paramètres de filtre
        status_filter = request.GET.get('status', '')
        priority_filter = request.GET.get('priority', '')
        search_query = request.GET.get('search', '')
        
        # Filtrer les demandes du client
        requests = ServiceRequest.objects.filter(client=request.user)
        
        # Appliquer les filtres
        if status_filter:
            requests = requests.filter(status=status_filter)
            
        if priority_filter:
            requests = requests.filter(priority=priority_filter)
            
        if search_query:
            requests = requests.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(service__title__icontains=search_query)
            )
        
        # Trier par date de création (les plus récentes en premier)
        requests = requests.order_by('-created_at')
        
        # Obtenir les services disponibles pour le menu déroulant
        available_services = Service.objects.filter(is_active=True)
        
        context = {
            'requests': requests,
            'available_services': available_services,
            'current_status': status_filter,
            'current_priority': priority_filter,
            'current_search': search_query,
        }
        
        return render(request, 'client/demandes.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def create_request_view(request, service_id):
    """Create a new service request"""
    try:
        client = Client.objects.get(user=request.user)
        service = get_object_or_404(Service, id=service_id, is_active=True)
        
        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            priority = request.POST.get('priority', 'medium')
            
            # Create the request
            demande = ServiceRequest.objects.create(
                client=request.user,
                service=service,
                title=title,
                description=description,
                priority=priority,
                status='new'
            )
            
            # Upload documents if provided
            for file_key in request.FILES:
                # Skip if file_key is 'files[]' as it's already processed from request.FILES.getlist('files[]')
                if file_key == 'files[]' or '[' in file_key:
                    continue
                
                file = request.FILES[file_key]
                document = Document.objects.create(
                    service_request=demande,
                    uploaded_by=request.user,
                    type='other',
                    name=file.name,
                    file=file,
                    mime_type=file.content_type,
                    file_size=file.size // 1024  # Convert to KB
                )
            
            # Process files[] as list instead of individually
            files_list = request.FILES.getlist('files[]')
            for file in files_list:
                document = Document.objects.create(
                    service_request=demande,
                    uploaded_by=request.user,
                    type='other',
                    name=file.name,
                    file=file,
                    mime_type=file.content_type,
                    file_size=file.size // 1024  # Convert to KB
                )
            
            # Create a notification for admins
            for admin_user in Utilisateur.objects.filter(account_type='admin', is_active=True):
                Notification.objects.create(
                    user=admin_user,
                    type='request_update',
                    title=_('New Service Request'),
                    content=_(f'A new service request "{title}" has been created by {client.user.name} {client.user.first_name}.'),
                    related_demande=demande
                )
            
            # Redirect to client requests view using the consistent URL naming
            return redirect('custom_requests:client_demandes')
            
        context = {
            'service': service,
        }
        
        return render(request, 'client/create_request.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def create_request_by_type_view(request, service_type):
    """Create a new service request by service type name (admin, tourisme, etc.)"""
    try:
        # Map service type names to categories
        service_type_map = {
            'admin': 'administrative',
            'administrative': 'administrative',
            'tourisme': 'tourism',
            'tourism': 'tourism',
            'immobilier': 'real_estate',
            'real_estate': 'real_estate',
            'fiscal': 'fiscal',
            'tax': 'fiscal',
            'investissement': 'investment',
            'investment': 'investment'
        }
        
        # Get category slug (default to 'administrative' if not found)
        category_slug = service_type_map.get(service_type.lower(), 'administrative')
        
        # Try to find a service category with this slug
        try:
            category = ServiceCategory.objects.get(slug=category_slug)
            # Get first active service in this category
            service = Service.objects.filter(
                service_type__category=category,
                is_active=True
            ).first()
            
            if not service:
                # If no service found in category, get any active service
                service = Service.objects.filter(is_active=True).first()
                if not service:
                    # Store single error message in session
                    messages.error(request, _('No active services found. Please contact support.'))
                    return redirect('client_dashboard')
        except ServiceCategory.DoesNotExist:
            # If category not found, get any active service
            service = Service.objects.filter(is_active=True).first()
            if not service:
                # Store single error message in session
                messages.error(request, _('No active services found. Please contact support.'))
                return redirect('client_dashboard')
        
        # Redirect to the existing create view with the service ID
        return redirect('custom_requests:create_request', service_id=service.id)
    
    except Exception as e:
        messages.error(request, _(f'An error occurred: {str(e)}'))
        return redirect('client_dashboard')

@login_required
def request_detail_view(request, request_id):
    """Display details of a specific request"""
    demande = get_object_or_404(ServiceRequest, id=request_id)
      # Check if user has permission to view this request
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            if demande.client != request.user:  # Compare with the User object, not the Client
                return redirect('home')
        except Client.DoesNotExist:
            return redirect('home')
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            if demande.expert != expert:
                return redirect('home')
        except Expert.DoesNotExist:
            return redirect('home')
    elif request.user.account_type != 'admin':
        return redirect('home')
    
    # Get documents and messages related to this request
    documents = Document.objects.filter(service_request=demande).order_by('-upload_date')
    messages = Message.objects.filter(service_request=demande).order_by('sent_at')
    appointments = RendezVous.objects.filter(service_request=demande).order_by('date_time')
    
    # Handle new message submission
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:            # Create a new message
            if request.user.account_type == 'client':
                # From client to expert or admin
                recipient = demande.expert.user if demande.expert else Utilisateur.objects.filter(account_type='admin').first()
            else:
                # From expert/admin to client
                recipient = demande.client.user
                
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                service_request=demande
            )
            
            # Create notification for recipient
            Notification.objects.create(
                user=recipient,
                type='message',
                title=_('New Message'),
                content=_(f'You have a new message from {request.user.name} {request.user.first_name} regarding request "{demande.title}".'),
                related_service_request=demande,
                related_message=message
            )
    
    context = {
        'demande': demande,
        'documents': documents,
        'messages': messages,
        'appointments': appointments,
    }
    
    return render(request, 'client/request_detail.html', context)

@login_required
def edit_request_view(request, request_id):
    """Edit an existing request"""
    try:
        client = Client.objects.get(user=request.user)
        # Utiliser request.user pour le client car c'est une ForeignKey vers Utilisateur
        demande = get_object_or_404(ServiceRequest, id=request_id, client=request.user)
        
        # Only allow editing if request is new or pending information
        if demande.status not in ['new', 'pending_info']:
            messages.error(request, _('This request cannot be edited in its current status.'))
            return redirect('custom_requests:request_detail', request_id=request_id)
        
        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            priority = request.POST.get('priority')
            
            # Update the request
            demande.title = title
            demande.description = description
            demande.priority = priority
            demande.save()
            
            # Notify assigned expert if any
            # Utiliser demande.expert au lieu de demande.assigned_expert
            if demande.expert:
                Notification.objects.create(
                    user=demande.expert,  # L'expert est déjà un Utilisateur
                    type='request_update',
                    title=_('Request Updated'),
                    content=_(f'Request "{demande.title}" has been updated by {client.user.name} {client.user.first_name}.'),
                    related_service_request=demande
                )
            
            return redirect('custom_requests:request_detail', request_id=request_id)
            
        context = {
            'demande': demande,
        }
        
        return render(request, 'client/edit_request.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def cancel_request_view(request, request_id):
    """Cancel a request"""
    try:
        client = Client.objects.get(user=request.user)
        demande = get_object_or_404(ServiceRequest, id=request_id, client=request.user)
        
        # Only allow cancellation if request is not already completed or cancelled
        if demande.status in ['completed', 'cancelled']:
            messages.error(request, _('This request cannot be cancelled in its current status.'))
            return redirect('custom_requests:request_detail', request_id=request_id)
        
        if request.method == 'POST':
            reason = request.POST.get('reason', '')
            
            # Update the request
            demande.status = 'cancelled'
            demande.save()
            
            # Notify assigned expert if any
            if demande.expert:
                Notification.objects.create(
                    user=demande.expert.user,
                    type='request_update',
                    title=_('Request Cancelled'),
                    content=_(f'Request "{demande.title}" has been cancelled by {client.user.name} {client.user.first_name}. Reason: {reason}'),
                    related_service_request=demande
                )
            
            messages.success(request, _('Request has been cancelled successfully.'))
            return redirect('custom_requests:client_requests')
            
        context = {
            'demande': demande,
        }
        
        return render(request, 'client/cancel_request.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

# Appointment views
@login_required
def client_appointments_view(request):
    """Display client's appointments"""
    try:
        # Get filters
        status = request.GET.get('status', '')
        search = request.GET.get('search', '')
        date = request.GET.get('date', '')
        
        # Start with all appointments for this client
        appointments = RendezVous.objects.filter(client=request.user)
        
        # Apply filters
        if status:
            appointments = appointments.filter(status=status)
        
        if date:
            try:
                # Filter by date only (not time)
                from datetime import datetime
                filter_date = datetime.strptime(date, '%Y-%m-%d').date()
                appointments = appointments.filter(date_time__date=filter_date)
            except ValueError:
                pass  # Invalid date format
        
        if search:
            # Search in service titles and notes
            search_query = Q(notes__icontains=search) | Q(service__title__icontains=search)
            
            # Search in expert's name fields
            search_query |= Q(expert__name__icontains=search) | Q(expert__first_name__icontains=search)
            
            # Search in client's name fields (though this will always be the current user)
            search_query |= Q(client__name__icontains=search) | Q(client__first_name__icontains=search)
            
            # Apply the search query
            appointments = appointments.filter(search_query)
        
        # Order by date_time
        appointments = appointments.order_by('date_time')
        
        # Get services for the "New appointment" form
        services = Service.objects.filter(is_active=True)
        
        # Get available experts
        experts = Expert.objects.filter(user__is_active=True)
        
        # Get client's service requests for the "linked request" dropdown
        service_requests = ServiceRequest.objects.filter(client=request.user).exclude(status='cancelled')
        
        context = {
            'appointments': appointments,
            'services': services,
            'experts': experts,
            'service_requests': service_requests
        }
        
        return render(request, 'client/rendezvous.html', context)
    
    except Client.DoesNotExist:
        return redirect('home')

@login_required
def create_appointment_view(request):
    """Create a new appointment"""
    if request.method != 'POST':
        return redirect('custom_requests:client_appointments')
    
    try:
        client = Client.objects.get(user=request.user)
        
        # Get form data
        expert_id = request.POST.get('expert_id')
        service_id = request.POST.get('service_id')
        date = request.POST.get('date')
        time = request.POST.get('time')
        consultation_type = request.POST.get('consultation_type')
        notes = request.POST.get('notes', '')
        demande_id = request.POST.get('demande_id', '')
        
        # Validate data
        if not (expert_id and service_id and date and time and consultation_type):
            messages.error(request, _('Please fill all required fields.'))
            return redirect('custom_requests:client_appointments')
        
        try:
            # Get the expert, service and service request
            expert = Expert.objects.get(user_id=expert_id)
            service = Service.objects.get(id=service_id)
            
            # Parse the date and time
            from datetime import datetime
            date_time_str = f'{date} {time}'
            date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
            
            # Get the linked service request if provided
            demande = None
            if demande_id:
                demande = get_object_or_404(ServiceRequest, id=demande_id, client=request.user)
            
            # Create the appointment
            appointment = RendezVous.objects.create(
                client=request.user,
                expert=expert.user,
                service=service,
                date_time=date_time,
                consultation_type=consultation_type,
                notes=notes,
                service_request=demande,
                status='scheduled'
            )
              # Create notification for the expert
            Notification.objects.create(
                user=expert.user,
                type='appointment',
                title=_('New Appointment Request'),
                content=_(f'A new appointment has been scheduled by {request.user.name} {request.user.first_name} for {date_time.strftime("%Y-%m-%d %H:%M")}.'),
                related_rendez_vous=appointment
            )
            
            # Send email notification to expert about new appointment
            EmailNotificationService.send_appointment_notification(
                client=request.user,
                expert=expert.user,
                appointment=appointment,
                notification_type='expert_assigned'
            )
            
            # Send email notification to client confirming appointment creation
            EmailNotificationService.send_appointment_notification(
                client=request.user,
                expert=expert.user,
                appointment=appointment,
                notification_type='created'
            )
            
            messages.success(request, _('Appointment successfully scheduled.'))
            
        except (Expert.DoesNotExist, Service.DoesNotExist):
            messages.error(request, _('Invalid expert or service.'))
        except ValueError:
            messages.error(request, _('Invalid date or time format.'))
    
    except Client.DoesNotExist:
        messages.error(request, _('You need a client account to schedule appointments.'))
    
    return redirect('custom_requests:client_appointments')

@login_required
def appointment_detail_view(request, appointment_id):
    """Display details of a specific appointment"""
    appointment = get_object_or_404(RendezVous, id=appointment_id)
    
    # Check if user has permission to view this appointment
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            if appointment.client != request.user:
                return redirect('home')
        except Client.DoesNotExist:
            return redirect('home')
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            if appointment.expert != expert.user:
                return redirect('home')
        except Expert.DoesNotExist:
            return redirect('home')
    elif request.user.account_type != 'admin':
        return redirect('home')
    
    # Get documents related to this appointment
    documents = Document.objects.filter(rendez_vous=appointment).order_by('-upload_date')
    
    context = {
        'appointment': appointment,
        'documents': documents,
    }
    
    return render(request, 'client/appointment_detail.html', context)

@login_required
def cancel_appointment_view(request, appointment_id):
    """Cancel a specific appointment"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Tentative d'annulation du rendez-vous {appointment_id}")
    
    if request.method != 'POST':
        logger.error("Méthode non autorisée")
        messages.error(request, _('Méthode non autorisée.'))
        return redirect('admin_appointments')
        
    appointment = get_object_or_404(RendezVous, id=appointment_id)
    logger.info(f"Statut actuel du rendez-vous: {appointment.status}")
    
    # Check if user has permission to cancel this appointment
    if request.user.account_type != 'admin':
        logger.error("Utilisateur non autorisé")
        messages.error(request, _('Vous n\'êtes pas autorisé à annuler ce rendez-vous.'))
        return redirect('admin_appointments')
    
    # Check if the appointment can be cancelled
    if appointment.status not in ['scheduled', 'confirmed', 'completed']:
        logger.error(f"Statut actuel non autorisé pour l'annulation: {appointment.status}")
        messages.error(request, _('Ce rendez-vous ne peut pas être annulé dans son état actuel.'))
        return redirect('admin_appointments')
    
    # Get the cancellation reason
    cancel_reason = request.POST.get('cancel_reason', '')
    if not cancel_reason:
        logger.error("Raison d'annulation manquante")
        messages.error(request, _('Veuillez fournir une raison pour l\'annulation.'))
        return redirect('admin_appointments')
    
    try:
        # Cancel the appointment
        logger.info("Mise à jour du statut en 'cancelled'")
        appointment.status = 'cancelled'
        appointment.notes = f"Annulé par l'administrateur. Raison : {cancel_reason}"
        appointment.save()
        logger.info("Statut mis à jour avec succès")
        
        # Create notification for the client
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Rendez-vous annulé'),
            content=_(f'Votre rendez-vous du {appointment.date_time.strftime("%d/%m/%Y à %H:%M")} a été annulé par l\'administrateur. Raison : {cancel_reason}'),
            related_rendez_vous=appointment
        )
        
        # Create notification for the expert
        Notification.objects.create(
            user=appointment.expert,
            type='appointment_update',
            title=_('Rendez-vous annulé'),
            content=_(f'Le rendez-vous du {appointment.date_time.strftime("%d/%m/%Y à %H:%M")} avec {appointment.client.first_name} {appointment.client.name} a été annulé par l\'administrateur. Raison : {cancel_reason}'),
            related_rendez_vous=appointment
        )
        
        logger.info("Notifications créées avec succès")
        messages.success(request, _('Le rendez-vous a été annulé avec succès.'))
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation: {str(e)}")
        messages.error(request, _(f'Une erreur est survenue lors de l\'annulation du rendez-vous : {str(e)}'))
    
    return redirect('admin_appointments')

# Expert views
@login_required
def expert_requests_view(request):
    """View function for expert requests."""
    if not request.user.account_type.lower() == 'expert':
        return redirect('home')

    try:
        # Print debug information
        print(f"Expert email: {request.user.email}")
        print(f"Total service requests: {ServiceRequest.objects.count()}")
        print(f"Requests assigned to this expert: {ServiceRequest.objects.filter(expert=request.user).count()}")
        
        # Get service requests assigned to this expert
        requests = ServiceRequest.objects.filter(expert=request.user)
        
        for req in requests:
            print(f"Request ID: {req.id}, Title: {req.title}, Status: {req.status}")
        
        context = {
            'requests': requests,
        }
        
        return render(request, 'expert/demandes.html', context)
    
    except Exception as e:
        print(f"Error in expert_requests_view: {str(e)}")
        return render(request, 'expert/demandes.html', {'requests': []})

@login_required
def expert_appointments_view(request):
    """Display expert's appointments"""
    if request.user.account_type.lower() != 'expert':
        messages.error(request, "Vous devez être connecté en tant qu'expert pour accéder à cette page.")
        return redirect('home')
        
    try:
        expert = Expert.objects.get(user=request.user)
        
        # Check if appointment_id is provided in the query parameters
        appointment_id = request.GET.get('appointment_id')
        if appointment_id:
            return redirect('expert_appointment_detail', appointment_id=appointment_id)
            
        # Get filters from request
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date', '')
        
        # Start with all appointments for this expert
        appointments = RendezVous.objects.filter(expert=expert.user)
        
        # Apply status filter
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        # Apply date filter
        if date_filter:
            try:
                from datetime import datetime
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                appointments = appointments.filter(date_time__date=filter_date)
            except ValueError:
                pass
        
        # Apply search filter
        if search_query:
            search_query = Q(notes__icontains=search_query) | Q(service__title__icontains=search_query)
            search_query |= Q(client__name__icontains=search_query) | Q(client__first_name__icontains=search_query)
            appointments = appointments.filter(search_query)
        
        # Order by date_time
        appointments = appointments.order_by('date_time')
        
        # Get all clients to populate the dropdown in the "Add appointment" modal
        clients = Client.objects.filter(user__is_active=True)
        
        context = {
            'appointments': appointments,
            'clients': clients,
            'current_status': status_filter,
            'current_search': search_query,
            'current_date': date_filter,
        }
        
        return render(request, 'expert/rendezvous.html', context)
    
    except Expert.DoesNotExist:
        messages.error(request, "Profil d'expert non trouvé. Veuillez contacter l'administrateur.")
        return redirect('home')

# Document views
@login_required
def documents_view(request):
    """Display user's documents"""
    # Get filters from request
    doc_type = request.GET.get('type')
    search = request.GET.get('search')
    date_filter = request.GET.get('date')
    
    documents_query = Document.objects.all()
    
    # Apply user filter
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            # Get documents from client's requests - fixed to use correct field names
            documents_query = documents_query.filter(
                Q(service_request__client=request.user) |
                Q(rendez_vous__client=request.user) |
                Q(uploaded_by=request.user)
            ).distinct()
            
            # Get client's service requests for the upload form
            service_requests = ServiceRequest.objects.filter(client=request.user).order_by('-created_at')
            
        except Client.DoesNotExist:
            documents_query = documents_query.filter(uploaded_by=request.user)
            service_requests = []
    
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            # Get documents from expert's assigned requests
            documents_query = documents_query.filter(
                Q(service_request__expert=expert.user) |
                Q(rendez_vous__expert=expert.user) |
                Q(uploaded_by=request.user)
            ).distinct()
            service_requests = []
        except Expert.DoesNotExist:
            documents_query = documents_query.filter(uploaded_by=request.user)
            service_requests = []
    
    elif request.user.account_type == 'admin':
        # Admins can see all documents
        service_requests = []
    
    else:
        documents_query = Document.objects.none()
        service_requests = []
    
    # Apply type filter
    if doc_type:
        documents_query = documents_query.filter(type=doc_type)
    
    # Apply search filter
    if search:
        documents_query = documents_query.filter(
            Q(name__icontains=search) |
            Q(reference_number__icontains=search)
        )
    
    # Apply date filter
    if date_filter:
        documents_query = documents_query.filter(upload_date__date=date_filter)
    
    # Order by upload date
    documents = documents_query.order_by('-upload_date')
    
    context = {
        'documents': documents,
        'service_requests': service_requests,
    }
    
    if request.user.account_type == 'client':
        return render(request, 'client/documents.html', context)
    elif request.user.account_type == 'expert':
        return render(request, 'expert/documents.html', context)
    elif request.user.account_type == 'admin':
        return render(request, 'admin/documents.html', context)
    else:
        return redirect('home')

@login_required
def upload_document_view(request):
    """Upload a document"""
    if request.method == 'POST':
        name = request.POST.get('name')
        document_type = request.POST.get('type', 'other')
        demande_id = request.POST.get('demande_id')
        rendez_vous_id = request.POST.get('rendez_vous_id')
        is_official = request.POST.get('is_official') == 'on'
        reference_number = request.POST.get('reference_number', '')
        
        if 'file' in request.FILES:
            file = request.FILES['file']
            
            # Get related demande and rendez_vous if provided
            demande = None
            rendez_vous = None
            
            if demande_id:
                demande = get_object_or_404(ServiceRequest, id=demande_id)
            
            if rendez_vous_id:
                rendez_vous = get_object_or_404(RendezVous, id=rendez_vous_id)
            
            # Create document - fixed to use correct field names
            document = Document.objects.create(
                service_request=demande,
                rendez_vous=rendez_vous,
                uploaded_by=request.user,
                type=document_type,
                name=name or file.name,
                file=file,
                mime_type=file.content_type,
                file_size=file.size // 1024,  # Convert to KB
                is_official=is_official,
                reference_number=reference_number
            )            # Create notifications
            if demande:
                if request.user.account_type == 'client':
                    # Notify assigned expert if any
                    if demande.expert:
                        Notification.objects.create(
                            user=demande.expert.user,
                            type='document',
                            title=_('New Document Uploaded'),
                            content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for request "{demande.title}".'),
                            related_service_request=demande
                        )
                        
                        # Send email notification to expert
                        EmailNotificationService.send_document_uploaded_notification(
                            request.user, demande.expert.user, document, demande
                        )
                else:
                    # Notify client
                    Notification.objects.create(
                        user=demande.client.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your request "{demande.title}".'),
                            related_service_request=demande
                    )
                      # Send email notification to client
                    EmailNotificationService.send_document_uploaded_notification(
                        request.user, demande.client.user, document, demande
                    )
            
            if rendez_vous:
                if request.user.account_type == 'client':
                    # Notify expert
                    Notification.objects.create(
                        user=rendez_vous.expert.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                        related_rendez_vous=rendez_vous
                    )
                    
                    # Send email notification to expert
                    EmailNotificationService.send_document_uploaded_notification(
                        request.user, rendez_vous.expert.user, document, None
                    )
                else:
                    # Notify client
                    Notification.objects.create(
                        user=rendez_vous.client.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                        related_rendez_vous=rendez_vous
                    )
                    
                    # Send email notification to client
                    EmailNotificationService.send_document_uploaded_notification(
                        request.user, rendez_vous.client.user, document, None
                    )
            
            return redirect('custom_requests:documents')
    
    # Get requests and appointments for association
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            # Use request.user instead of client when filtering ServiceRequest objects
            demandes = ServiceRequest.objects.filter(client=request.user)
            appointments = RendezVous.objects.filter(client=request.user)
        except Client.DoesNotExist:
            demandes = []
            appointments = []
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(expert=expert.user)
            appointments = RendezVous.objects.filter(expert=expert.user)
        except Expert.DoesNotExist:
            demandes = []
            appointments = []
    elif request.user.account_type == 'admin':
        demandes = ServiceRequest.objects.all()
        appointments = RendezVous.objects.all()
    else:
        demandes = []
        appointments = []
    
    context = {
        'demandes': demandes,
        'appointments': appointments,
    }
    
    return render(request, 'upload_document.html', context)

@login_required
def delete_document_view(request, document_id):
    """
    Delete a document
    """
    try:
        # Récupérer le document ou renvoyer 404 si non trouvé
        document = Document.objects.get(id=document_id)
        
        # Vérifier les permissions
        has_permission = False
        
        # Vérifier si l'utilisateur est admin
        if request.user.account_type == 'admin':
            has_permission = True
        # Vérifier si l'utilisateur est le propriétaire du document
        elif document.uploaded_by == request.user:
            has_permission = True
        # Vérifier si l'utilisateur est le client ou l'expert associé à la demande
        elif document.service_request:
            if request.user.account_type == 'client' and document.service_request.client == request.user:
                has_permission = True
            elif request.user.account_type == 'expert' and document.service_request.expert == request.user:
                has_permission = True
        
        if not has_permission:
            messages.error(request, _("Vous n'avez pas la permission de supprimer ce document."))
            return redirect('custom_requests:documents')
        
        # Supprimer le document
        document.delete()
        messages.success(request, _("Le document a été supprimé avec succès."))
        
    except Document.DoesNotExist:
        messages.error(request, _("Le document que vous essayez de supprimer n'existe pas ou a déjà été supprimé."))
    except Exception as e:
        messages.error(request, _("Une erreur s'est produite lors de la suppression du document."))
        # En environnement de développement, vous pouvez logger l'erreur
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la suppression du document {document_id}: {str(e)}")
    
    return redirect('custom_requests:documents')

# Messaging views
@login_required
def messages_view(request):
    """Display user's messages"""
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # Group messages by conversation
    conversations = {}
    for message in messages:
        # Determine the other party in the conversation
        other_party = message.recipient if message.sender == request.user else message.sender
        
        # Create a unique key for this conversation
        conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
        
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'other_party': other_party,
                'latest_message': message,
                'unread_count': 1 if message.recipient == request.user and not message.is_read else 0
            }
        else:
            # Update latest message if this one is newer
            if message.sent_at > conversations[conversation_key]['latest_message'].sent_at:
                conversations[conversation_key]['latest_message'] = message
            
            # Update unread count
            if message.recipient == request.user and not message.is_read:
                conversations[conversation_key]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message date
    conversations_list = sorted(
        conversations.values(),
        key=lambda x: x['latest_message'].sent_at,
        reverse=True
    )
    
    context = {
        'conversations': conversations_list,
    }
    
    if request.user.account_type == 'client':
        return render(request, 'client/messages.html', context)
    elif request.user.account_type == 'expert':
        return render(request, 'expert/messages.html', context)
    elif request.user.account_type == 'admin':
        return render(request, 'admin/messages.html', context)
    else:
        return redirect('home')

@login_required
def send_message_view(request):
    """Send a new message"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        demande_id = request.POST.get('demande_id')
        
        recipient = get_object_or_404(Utilisateur, id=recipient_id)
        
        # Get related request if provided
        demande = None
        if demande_id:
            demande = get_object_or_404(ServiceRequest, id=demande_id)
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content,
            service_request=demande
        )
          # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('New Message'),
            content=_(f'You have a new message from {request.user.name} {request.user.first_name}.'),
            related_message=message,
            related_service_request=demande
        )
        
        # Send email notification
        try:
            EmailNotificationService.send_new_message_notification(
                sender=request.user,
                recipient=recipient,
                message_content=content
            )
        except Exception as email_error:
            print(f"Failed to send email notification: {email_error}")
            # Continue without failing the request
        
        return redirect('custom_requests:messages')
    
    # Get potential recipients based on user type
    recipients = []
    
    if request.user.account_type == 'client':
        # Clients can message experts they have appointments with and admins
        try:
            client = Client.objects.get(user=request.user)
            expert_users = Utilisateur.objects.filter(
                expert_profile__appointments__client=client
            ).distinct()
            admin_users = Utilisateur.objects.filter(account_type='admin', is_active=True)
            recipients = list(expert_users) + list(admin_users)
        except Client.DoesNotExist:
            pass
    
    elif request.user.account_type == 'expert':
        # Experts can message clients they have appointments with and admins
        try:
            expert = Expert.objects.get(user=request.user)
            client_users = Utilisateur.objects.filter(
                client_profile__appointments__expert=expert
            ).distinct()
            admin_users = Utilisateur.objects.filter(account_type='admin', is_active=True)
            recipients = list(client_users) + list(admin_users)
        except Expert.DoesNotExist:
            pass
    
    elif request.user.account_type == 'admin':
        # Admins can message all clients and experts
        client_users = Utilisateur.objects.filter(account_type='client', is_active=True)
        expert_users = Utilisateur.objects.filter(account_type='expert', is_active=True)
        recipients = list(client_users) + list(expert_users)
    
    # Get requests the user is involved in
    if request.user.account_type == 'client':
        try:
            client = Client.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(client=request.user)
        except Client.DoesNotExist:
            demandes = []
    elif request.user.account_type == 'expert':
        try:
            expert = Expert.objects.get(user=request.user)
            demandes = ServiceRequest.objects.filter(expert=expert.user)
        except Expert.DoesNotExist:
            demandes = []
    elif request.user.account_type == 'admin':
        demandes = ServiceRequest.objects.all()
    else:
        demandes = []
    
    context = {
        'recipients': recipients,
        'demandes': demandes,
    }
    
    return render(request, 'send_message.html', context)

# Notification views
@login_required
def notifications_view(request):
    """Display user's notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    if request.user.account_type == 'client':
        return render(request, 'client/notifications.html', context)
    elif request.user.account_type == 'expert':
        return render(request, 'expert/notifications.html', context)
    elif request.user.account_type == 'admin':
        return render(request, 'admin/notifications.html', context)
    else:
        return redirect('home')

@login_required
def mark_notification_read_view(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        # Retrieve redirect URL if provided
        redirect_url = request.GET.get('redirect_url')
        
        # Redirect to related content if available
        if notification.related_service_request:
            return redirect('custom_requests:request_detail', request_id=notification.related_service_request.id)
        elif notification.related_rendez_vous:
            return redirect('expert_appointment_detail', appointment_id=notification.related_rendez_vous.id)
        elif notification.related_message:
            # Redirect to appropriate messages page based on user account type
            sender_id = notification.related_message.sender.id
            if request.user.account_type == 'client':
                return redirect(f'/client/messages/?contact={sender_id}')
            elif request.user.account_type == 'expert':
                return redirect(f'/expert/messages/?client={sender_id}')
            elif request.user.account_type == 'admin':
                return redirect(f'/admin/messages/?user={sender_id}')
        elif redirect_url:
            # Use the provided redirect URL if none of the above conditions are met
            return redirect(redirect_url)
        else:
            return redirect('custom_requests:notifications')
            
    except Notification.DoesNotExist:
        messages.error(request, _("Notification introuvable."))
        return redirect('client_dashboard')

@require_POST
def mark_all_notifications_read(request):
    """Mark all unread notifications as read"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)
    
    try:
        # Marquer toutes les notifications non lues comme lues
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': f'{updated} notifications marquées comme lues',
            'updated_count': updated
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# AJAX view for client request creation
@login_required
@csrf_exempt
@require_POST
def ajax_create_request(request):
    """Create a new service request via AJAX"""
    try:
        # Verify user is a client
        client = Client.objects.get(user=request.user)
        
        # Get form data
        data = request.POST
        service_type = data.get('serviceType')
        title = data.get('requestTitle')
        description = data.get('requestDescription')
        priority = data.get('priority', 'medium')
        
        # Map service type to actual service
        service_type_map = {
            'Service Administratif': 'administrative',
            'Services Administratifs': 'administrative',
            'Service Tourisme': 'tourism',
            'Tourisme': 'tourism',
            'Service Immobilier': 'real_estate',
            'Immobilier': 'real_estate',
            'Service Fiscal': 'fiscal',
            'Fiscalité': 'fiscal',
            'Service Investissement': 'investment',
            'Investissement': 'investment'
        }
        
        # Get category slug
        category_slug = service_type_map.get(service_type, 'administrative')
        
        # Try to find a service category with this slug
        try:
            category = ServiceCategory.objects.get(slug=category_slug)
            # Get first active service in this category
            service = Service.objects.filter(
                service_type__category=category,
                is_active=True
            ).first()
            
            if not service:
                # If no service found in category, get any active service
                service = Service.objects.filter(is_active=True).first()
                if not service:
                    return JsonResponse({
                        'success': False,
                        'message': _('No active services found. Please contact support.')
                    })
        except ServiceCategory.DoesNotExist:
            # If category not found, get any active service
            service = Service.objects.filter(is_active=True).first()
            if not service:
                return JsonResponse({
                    'success': False,
                    'message': _('No active services found. Please contact support.')
                })
        
        # Create the request
        demande = ServiceRequest.objects.create(
            client=request.user,
            service=service,
            title=title,
            description=description,
            priority=priority,
            status='new'
        )
        
        # Upload documents if provided
        for file_key in request.FILES:
            # Skip if file_key is 'files[]' as it's already processed from request.FILES.getlist('files[]')
            if file_key == 'files[]' or '[' in file_key:
                continue
                
            file = request.FILES[file_key]
            document = Document.objects.create(
                service_request=demande,
                uploaded_by=request.user,
                type='other',
                name=file.name,
                file=file,
                mime_type=file.content_type,
                file_size=file.size // 1024  # Convert to KB
            )
            
        # Process files[] as list instead of individually
        files_list = request.FILES.getlist('files[]')
        for file in files_list:
            document = Document.objects.create(
                service_request=demande,
                uploaded_by=request.user,
                type='other',
                name=file.name,
                file=file,
                mime_type=file.content_type,
                file_size=file.size // 1024  # Convert to KB
            )
        
        # Create a notification for admins
        for admin_user in Utilisateur.objects.filter(account_type='admin', is_active=True):
            Notification.objects.create(
                user=admin_user,
                type='request_update',
                title=_('New Service Request'),
                content=_(f'A new service request "{title}" has been created by {client.user.name} {client.user.first_name}.'),
                related_service_request=demande
            )
        
        return JsonResponse({
            'success': True,
            'message': _('Your request has been created successfully.'),
            'request_id': demande.id
        })
    
    except Client.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Client profile not found.')
        }, status=403)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

# API endpoints
@login_required
@csrf_exempt
def api_client_requests(request):
    """API endpoint for client requests"""
    try:
        client = Client.objects.get(user=request.user)
        requests_query = ServiceRequest.objects.filter(client=request.user).order_by('-created_at')
        
        # Apply status filter if provided
        status = request.GET.get('status')
        if status:
            requests_query = requests_query.filter(status=status)
        
        # Prepare response data
        requests_data = []
        for demande in requests_query:
            requests_data.append({
                'id': demande.id,
                'title': demande.title,
                'service': {
                    'id': demande.service.id,
                    'title': demande.service.title,
                    'category': demande.service.category
                },                'status': demande.status,
                'priority': demande.priority,
                'created_at': demande.created_at.isoformat(),
                'expert': {
                    'id': demande.expert.id,
                    'name': f"{demande.expert.user.name} {demande.expert.user.first_name}",
                } if demande.expert else None
            })
        
        return JsonResponse({
            'success': True,
            'requests': requests_data
        })
    
    except Client.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Client profile not found.')
        }, status=404)

@login_required
@csrf_exempt
def api_request_detail(request, request_id):
    """API endpoint for request details"""
    try:
        demande = get_object_or_404(ServiceRequest, id=request_id)
        
        # Check permission
        if request.user.account_type == 'client':
            client = Client.objects.get(user=request.user)
            if demande.client != client:                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to view this request.')
                }, status=403)
        elif request.user.account_type == 'expert':
            expert = Expert.objects.get(user=request.user)
            if demande.expert != expert:
                return JsonResponse({
                    'success': False,
                    'message': _('You do not have permission to view this request.')
                }, status=403)
        elif request.user.account_type != 'admin':
            return JsonResponse({
                'success': False,
                'message': _('You do not have permission to view this request.')
            }, status=403)
        
        # Get documents
        documents = []
        for doc in Document.objects.filter(service_request=demande):
            documents.append({
                'id': doc.id,
                'name': doc.name,
                'type': doc.type,
                'uploaded_by': f"{doc.uploaded_by.name} {doc.uploaded_by.first_name}",
                'upload_date': doc.upload_date.isoformat(),
                'is_official': doc.is_official
            })
        
        # Get messages
        messages_data = []
        for msg in Message.objects.filter(service_request=demande).order_by('sent_at'):
            messages_data.append({
                'id': msg.id,
                'sender': {
                    'id': msg.sender.id,
                    'name': f"{msg.sender.name} {msg.sender.first_name}",
                    'account_type': msg.sender.account_type
                },
                'content': msg.content,
                'sent_at': msg.sent_at.isoformat(),
                'is_read': msg.is_read
            })
        
        # Get appointments
        appointments = []
        for appt in RendezVous.objects.filter(service_request=demande):
            appointments.append({
                'id': appt.id,
                'date_time': appt.date_time.isoformat(),
                'expert': {
                    'id': appt.expert.id,
                    'name': f"{appt.expert.user.name} {appt.expert.user.first_name}"
                },
                'consultation_type': appt.consultation_type,
                'status': appt.status
            })
        
        # Prepare response data
        request_data = {
            'id': demande.id,
            'title': demande.title,
            'description': demande.description,
            'service': {
                'id': demande.service.id,
                'title': demande.service.title,
                'category': demande.service.category
            },
            'client': {
                'id': demande.client.id,
                'name': f"{demande.client.user.name} {demande.client.user.first_name}"
            },
            'status': demande.status,
            'priority': demande.priority,
            'created_at': demande.created_at.isoformat(),            'expert': {
                'id': demande.expert.id,
                'name': f"{demande.expert.user.name} {demande.expert.user.first_name}",
            } if demande.expert else None,
            'documents': documents,
            'messages': messages_data,
            'appointments': appointments
        }
        
        return JsonResponse({
            'success': True,
            'request': request_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=404)

@login_required
@csrf_exempt
def api_client_appointments(request):
    """API endpoint for client appointments"""
    try:
        if request.user.account_type == 'client':
            client = Client.objects.get(user=request.user)
            appointments_query = RendezVous.objects.filter(client=request.user).order_by('date_time')
        elif request.user.account_type == 'expert':
            expert = Expert.objects.get(user=request.user)
            appointments_query = RendezVous.objects.filter(expert=expert).order_by('date_time')
        elif request.user.account_type == 'admin':
            appointments_query = RendezVous.objects.all().order_by('date_time')
        else:
            return JsonResponse({
                'success': False,
                'message': _('Invalid user type.')
            }, status=403)
        
        # Apply status filter if provided
        status = request.GET.get('status')
        if status:
            appointments_query = appointments_query.filter(status=status)
        
        # Apply date filter if provided
        date_from = request.GET.get('date_from')
        if date_from:
            try:
                date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                date_from = timezone.make_aware(date_from)
                appointments_query = appointments_query.filter(date_time__gte=date_from)
            except ValueError:
                pass
        
        date_to = request.GET.get('date_to')
        if date_to:
            try:
                date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                date_to = timezone.make_aware(date_to)
                appointments_query = appointments_query.filter(date_time__lte=date_to)
            except ValueError:
                pass
        
        # Prepare response data
        appointments_data = []
        for appointment in appointments_query:
            appointments_data.append({
                'id': appointment.id,
                'date_time': appointment.date_time.isoformat(),
                'duration': appointment.duration,
                'client': {
                    'id': appointment.client.id,
                    'name': f"{appointment.client.user.name} {appointment.client.user.first_name}"
                },
                'expert': {
                    'id': appointment.expert.id,
                    'name': f"{appointment.expert.user.name} {appointment.expert.user.first_name}"
                },
                'service': {
                    'id': appointment.service.id,
                    'title': appointment.service.title,
                } if appointment.service else None,
                'consultation_type': appointment.consultation_type,
                'status': appointment.status,
                'request': {
                    'id': appointment.service_request.id,
                    'title': appointment.service_request.title
                } if appointment.service_request else None
            })
        
        return JsonResponse({
            'success': True,
            'appointments': appointments_data
        })
    
    except (Client.DoesNotExist, Expert.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': _('Profile not found.')
        }, status=404)

@login_required
@csrf_exempt
def api_expert_requests(request):
    """API endpoint for expert requests"""
    try:
        expert = Expert.objects.get(user=request.user)
        requests_query = ServiceRequest.objects.filter(expert=expert.user).order_by('-created_at')
        
        # Apply status filter if provided
        status = request.GET.get('status')
        if status:
            requests_query = requests_query.filter(status=status)
        
        # Prepare response data
        requests_data = []
        for demande in requests_query:
            requests_data.append({
                'id': demande.id,
                'title': demande.title,
                'service': {
                    'id': demande.service.id,
                    'title': demande.service.title,
                    'category': demande.service.category
                },
                'client': {
                    'id': demande.client.id,
                    'name': f"{demande.client.user.name} {demande.client.user.first_name}"
                },
                'status': demande.status,
                'priority': demande.priority,
                'created_at': demande.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'requests': requests_data
        })
    
    except Expert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Expert profile not found.')
        }, status=404)

@login_required
@csrf_exempt
@require_POST
def api_upload_document(request):
    """API endpoint to upload a document"""
    try:
        data = request.POST
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({
                'success': False,
                'message': _('No file provided.')
            }, status=400)
        
        name = data.get('name', file.name)
        document_type = data.get('type', 'other')
        demande_id = data.get('demande_id')
        rendez_vous_id = data.get('rendez_vous_id')
        is_official = data.get('is_official') == 'true'
        reference_number = data.get('reference_number', '')
        
        # Get related demande and rendez_vous if provided
        demande = None
        rendez_vous = None
        
        if demande_id:
            demande = get_object_or_404(ServiceRequest, id=demande_id)
        
        if rendez_vous_id:
            rendez_vous = get_object_or_404(RendezVous, id=rendez_vous_id)
        
        # Create document
        document = Document.objects.create(
            service_request=demande,
            rendez_vous=rendez_vous,
            uploaded_by=request.user,
            type=document_type,
            name=name,
            file=file,
            mime_type=file.content_type,
            file_size=file.size // 1024,  # Convert to KB
            is_official=is_official,
            reference_number=reference_number
        )        
        # Create appropriate notifications
        if demande:
            if request.user.account_type == 'client':
                if demande.expert:
                    Notification.objects.create(
                        user=demande.expert.user,
                        type='document',
                        title=_('New Document Uploaded'),
                        content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for request "{demande.title}".'),
                        related_service_request=demande
                    )
            else:
                Notification.objects.create(
                    user=demande.client.user,
                    type='document',
                    title=_('New Document Uploaded'),
                    content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your request "{demande.title}".'),
                    related_service_request=demande
                )
        
        if rendez_vous:
            if request.user.account_type == 'client':
                Notification.objects.create(
                    user=rendez_vous.expert.user,
                    type='document',
                    title=_('New Document Uploaded'),
                    content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                        related_rendez_vous=rendez_vous
                )
            else:
                Notification.objects.create(
                    user=rendez_vous.client.user,
                    type='document',
                    title=_('New Document Uploaded'),
                    content=_(f'A new document "{document.name}" has been uploaded by {request.user.name} {request.user.first_name} for your appointment on {rendez_vous.date_time.strftime("%Y-%m-%d %H:%M")}.'),
                        related_rendez_vous=rendez_vous
                )
        
        return JsonResponse({
            'success': True,
            'document': {
                'id': document.id,
                'name': document.name,
                'type': document.type,
                'file_url': document.file.url if document.file else None,
                'upload_date': document.upload_date.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@csrf_exempt
def api_messages(request):
    """API endpoint for user messages"""
    if request.method == 'GET':
        # Get messages with a specific user if provided
        other_user_id = request.GET.get('user_id')
        if other_user_id:
            try:
                other_user = Utilisateur.objects.get(id=other_user_id)
                messages_query = Message.objects.filter(
                    (Q(sender=request.user) & Q(recipient=other_user)) |
                    (Q(sender=other_user) & Q(recipient=request.user))
                ).order_by('sent_at')
                
                # Mark messages as read
                Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(
                    is_read=True,
                    read_at=timezone.now()
                )
                  # Prepare response data with content safety
                messages_data = []
                for message in messages_query:
                    # Sanitize and limit content length for safety
                    safe_content = str(message.content)[:2000] if message.content else ""
                    
                    messages_data.append({
                        'id': message.id,
                        'sender': {
                            'id': message.sender.id,
                            'name': f"{message.sender.name} {message.sender.first_name}",
                            'account_type': message.sender.account_type
                        },
                        'content': safe_content,
                        'sent_at': message.sent_at.isoformat(),
                        'is_read': message.is_read,
                        'is_mine': message.sender == request.user
                    })
                
                return JsonResponse({
                    'success': True,
                    'messages': messages_data,
                    'other_user': {
                        'id': other_user.id,
                        'name': f"{other_user.name} {other_user.first_name}",
                        'account_type': other_user.account_type
                    }
                })
                
            except Utilisateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': _('User not found.')
                }, status=404)
          # Otherwise, return conversation summary with content safety
        messages = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).order_by('-sent_at')[:100]  # Limit to last 100 messages for performance
        
        # Group messages by conversation
        conversations = {}
        for message in messages:
            # Determine the other party in the conversation
            other_party = message.recipient if message.sender == request.user else message.sender
            
            # Create a unique key for this conversation
            conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
            
            # Sanitize content for safety
            safe_content = str(message.content)[:200] if message.content else ""
            
            if conversation_key not in conversations:
                conversations[conversation_key] = {
                    'user': {
                        'id': other_party.id,
                        'name': f"{other_party.name} {other_party.first_name}",
                        'account_type': other_party.account_type
                    },
                    'latest_message': {
                        'id': message.id,
                        'content': safe_content,
                        'sent_at': message.sent_at.isoformat(),
                        'is_read': message.is_read,
                        'is_mine': message.sender == request.user
                    },
                    'unread_count': 1 if message.recipient == request.user and not message.is_read else 0
                }
            else:
                # Update latest message if this one is newer
                if message.sent_at > timezone.datetime.fromisoformat(conversations[conversation_key]['latest_message']['sent_at']):
                    conversations[conversation_key]['latest_message'] = {
                        'id': message.id,
                        'content': safe_content,
                        'sent_at': message.sent_at.isoformat(),
                        'is_read': message.is_read,
                        'is_mine': message.sender == request.user
                    }
                
                # Update unread count
                if message.recipient == request.user and not message.is_read:
                    conversations[conversation_key]['unread_count'] += 1
          # Convert dictionary to list and sort by latest message date
        conversations_list = sorted(
            conversations.values(),
            key=lambda x: x['latest_message']['sent_at'],
            reverse=True
        )
        
        return JsonResponse({
            'success': True,
            'conversations': conversations_list
        })
    
    elif request.method == 'POST':
        # Send a new message with content validation
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        demande_id = data.get('demande_id')
        
        if not content or not recipient_id:
            return JsonResponse({
                'success': False,
                'message': _('Recipient and content are required.')
            }, status=400)
        
        # Validate content length for safety
        if len(str(content)) > 2000:
            return JsonResponse({
                'success': False,
                'message': _('Message content is too long. Maximum 2000 characters allowed.')
            }, status=400)
        
        # Sanitize content
        content = str(content).strip()
        
        if not content:
            return JsonResponse({
                'success': False,
                'message': _('Recipient and content are required.')
            }, status=400)
        
        try:
            recipient = Utilisateur.objects.get(id=recipient_id)
            
            # Get related request if provided
            demande = None
            if demande_id:
                demande = get_object_or_404(ServiceRequest, id=demande_id)
            
            # Create message
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                service_request=demande
            )
            
            # Create notification for recipient
            Notification.objects.create(
                user=recipient,
                type='message',
                title=_('New Message'),
                content=_(f'You have a new message from {request.user.name} {request.user.first_name}.'),
                related_message=message,
                related_service_request=demande
            )
            
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sent_at': message.sent_at.isoformat(),
                    'is_read': message.is_read
                }
            })
            
        except Utilisateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Recipient not found.')
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': _('Method not allowed.')
    }, status=405)

@login_required
@csrf_exempt
def api_notifications(request):
    """API endpoint for user notifications"""
    notifications_query = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Get only unread if specified
    unread_only = request.GET.get('unread_only') == 'true'
    if unread_only:
        notifications_query = notifications_query.filter(is_read=False)
    
    # Limit number of notifications if specified
    limit = request.GET.get('limit')
    if limit:
        try:
            limit = int(limit)
            notifications_query = notifications_query[:limit]
        except ValueError:
            pass
    
    # Prepare response data
    notifications_data = []
    for notification in notifications_query:
        notifications_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'content': notification.content,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'related_service_request_id': notification.related_service_request.id if notification.related_service_request else None,
            'related_rendez_vous_id': notification.related_rendez_vous.id if notification.related_rendez_vous else None,
            'related_message_id': notification.related_message.id if notification.related_message else None
        })
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_data,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()    })

@login_required
def expert_create_appointment_view(request):
    """Handle expert appointment creation from the expert rendezvous page"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            client_id = request.POST.get('client')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            appointment_type = request.POST.get('type')
            description = request.POST.get('description', '')
            
            # Validate required fields
            if not all([title, client_id, start_time, end_time, appointment_type]):
                messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
                return redirect('expert_rendezvous')
              # Get client and expert
            try:
                client = Client.objects.get(id=client_id)
                client_user = client.user
                expert = request.user
            except Client.DoesNotExist:
                messages.error(request, 'Client non trouvé.')
                return redirect('expert_rendezvous')
              # Parse datetime
            try:
                start_datetime = timezone.datetime.fromisoformat(start_time.replace('T', ' '))
                end_datetime = timezone.datetime.fromisoformat(end_time.replace('T', ' '))
                
                # Make timezone aware
                if timezone.is_naive(start_datetime):
                    start_datetime = timezone.make_aware(start_datetime)
                if timezone.is_naive(end_datetime):
                    end_datetime = timezone.make_aware(end_datetime)
                    
                # Calculate duration in minutes
                duration = int((end_datetime - start_datetime).total_seconds() / 60)
            except ValueError:
                messages.error(request, 'Format de date/heure invalide.')
                return redirect('expert_rendezvous')
            
            # Combine title and description for notes
            notes = f"{title}"
            if description:
                notes += f"\n{description}"
              # Create appointment
            appointment = RendezVous.objects.create(
                client=client_user,
                expert=expert,
                date_time=start_datetime,
                duration=duration,
                consultation_type=appointment_type,
                notes=notes,
                status='scheduled'
            )
              # Send notification to client
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                subject = f'Nouveau rendez-vous programmé: {title}'
                message = f'Un nouveau rendez-vous a été programmé pour le {start_datetime.strftime("%d/%m/%Y à %H:%M")}.'
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [client_user.email])
            except Exception as e:
                pass  # Continue even if email fails
            
            # Send email notification to client about new appointment
            EmailNotificationService.send_appointment_notification(
                client=client_user,
                expert=expert,
                appointment=appointment,
                notification_type='created'
            )
            
            messages.success(request, 'Rendez-vous créé avec succès!')
            return redirect('expert_rendezvous')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du rendez-vous: {str(e)}')
            return redirect('expert_rendezvous')
    
    return redirect('expert_rendezvous')
