from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from custom_requests.models import RendezVous, Notification
from datetime import timedelta, datetime
from services.email_notifications import EmailNotificationService

@login_required
@require_http_methods(["GET"])
def client_appointments_api(request):
    """API endpoint to get client appointments for the calendar"""
    client = request.user
    
    # Get query parameters for filtering
    filter_type = request.GET.get('type', None)
    filter_status = request.GET.get('status', None)
    
    # Pagination parameters
    limit = request.GET.get('limit', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    
    # Base query - get all appointments for the client
    appointments = RendezVous.objects.filter(client=client).order_by('date_time')
    
    # Apply filters if specified
    if filter_type:
        appointments = appointments.filter(consultation_type=filter_type)
    if filter_status:
        appointments = appointments.filter(status=filter_status)
    
    # Apply date filtering if specified
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            appointments = appointments.filter(date_time__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            appointments = appointments.filter(date_time__date__lte=to_date)
        except ValueError:
            pass
    
    # Apply limit if specified lol
    total_count = appointments.count()
    if limit:
        try:
            limit = int(limit)
            appointments = appointments[:limit]
        except ValueError:
            pass
    
    # Format appointments for the calendar
    formatted_appointments = []
    for appointment in appointments:
        # Calculate end time based on duration
        end_time = appointment.date_time + timedelta(minutes=appointment.duration)
        
        # Map the consultation type to a human-readable label
        type_label = {
            'in_person': 'En personne',
            'video': 'Vidéo',
            'phone': 'Téléphone',
        }.get(appointment.consultation_type, appointment.consultation_type)
          # Map the status to a human-readable label
        status_label = {
            'scheduled': 'Planifié',
            'completed': 'Terminé',
            'cancelled': 'Annulé',
            'pending': 'En attente'
        }.get(appointment.status, appointment.status)
        
        formatted_appointment = {
            'id': appointment.id,
            'date_time': appointment.date_time.isoformat(),
            'end_time': end_time.isoformat(),
            'consultation_type': appointment.consultation_type,
            'consultation_type_label': type_label,
            'service_title': appointment.service.title if appointment.service else (
                appointment.service_request.title if appointment.service_request else 'Rendez-vous'
            ),
            'expert_name': f"{appointment.expert.name} {appointment.expert.first_name}" if appointment.expert else "Expert non assigné",
            'expert_id': appointment.expert.id if appointment.expert else None,
            'location': appointment.location or appointment.notes or "",  # Using notes as fallback, empty string as final fallback
            'notes': appointment.notes or "",
            'status': appointment.status,
            'status_label': status_label,
            'duration': appointment.duration
        }
        
        formatted_appointments.append(formatted_appointment)
    
    # Get unique consultation types for filtering
    consultation_types = list(set(a.consultation_type for a in appointments))
    type_labels = {
        'in_person': 'En personne',
        'video': 'Vidéo',
        'phone': 'Téléphone',
    }
    
    type_options = [{'value': t, 'label': type_labels.get(t, t)} for t in consultation_types]
    
    # Get unique statuses for filtering
    statuses = list(set(a.status for a in appointments))
    status_labels = {
        'scheduled': 'Planifié',
        'completed': 'Terminé',
        'cancelled': 'Annulé',
        'pending': 'En attente'
    }
    
    status_options = [{'value': s, 'label': status_labels.get(s, s)} for s in statuses]
    
    return JsonResponse({
        'success': True,
        'appointments': formatted_appointments,
        'total_count': total_count,
        'returned_count': len(formatted_appointments),
        'filter_options': {
            'types': type_options,
            'statuses': status_options
        }
    })

@login_required
@require_http_methods(["POST"])
def cancel_appointment_api(request, appointment_id):
    """API endpoint to cancel an appointment"""
    # Get the appointment or return 404
    appointment = get_object_or_404(RendezVous, id=appointment_id)
    
    # Check if the user is authorized to cancel this appointment
    if appointment.client != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Vous n\'êtes pas autorisé à annuler ce rendez-vous.'
        }, status=403)
    
    # Check if the appointment can be cancelled
    if appointment.status not in ['scheduled', 'pending', 'confirmed']:
        return JsonResponse({
            'success': False,
            'message': 'Ce rendez-vous ne peut pas être annulé dans son état actuel.'
        }, status=400)
    
    # Cancel the appointment
    appointment.status = 'cancelled'
    appointment.save()
      # Create notification for the expert
    if appointment.expert:
        Notification.objects.create(
            user=appointment.expert,
            type='appointment_update',
            title='Rendez-vous annulé',
            content=f'Le rendez-vous du {appointment.date_time.strftime("%d/%m/%Y à %H:%M")} a été annulé par le client.',
            related_rendez_vous=appointment
        )
        
        # Send email notification to expert about appointment cancellation
        EmailNotificationService.send_appointment_notification(
            client=appointment.expert,
            expert=request.user,
            appointment=appointment,
            notification_type='cancelled'
        )
    
    return JsonResponse({
        'success': True,
        'message': 'Rendez-vous annulé avec succès.',
        'appointment_id': appointment.id
    })
