from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse

from accounts.models import Utilisateur, Expert, Client
from custom_requests.models import ServiceRequest, Document, RendezVous, Message, Notification
from services.email_notifications import EmailNotificationService

@login_required
def expert_confirm_appointment(request, appointment_id):
    """Confirm an appointment."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointment details
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=request.user)
        
        # Update appointment status        appointment.status = 'confirmed'
        appointment.save()
        
        # Create notification for client
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Rendez-vous confirmé'),
            content=_('Votre rendez-vous du {} a été confirmé par l\'expert.').format(
                appointment.date_time.strftime('%d/%m/%Y à %H:%M')
            ),
            related_rendez_vous=appointment
        )
        
        # Send email notification to client about appointment confirmation
        EmailNotificationService.send_appointment_notification(
            client=appointment.client,
            expert=request.user,
            appointment=appointment,
            notification_type='confirmed'
        )
        
        # Add a success message
        messages.success(request, _('Le rendez-vous a été confirmé avec succès.'))
        
        return redirect('expert_rendezvous')
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_cancel_appointment(request, appointment_id):
    """Cancel an appointment."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointment details
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=request.user)
          # Update appointment status
        appointment.status = 'cancelled'
        appointment.save()
        
        # Create notification for client
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Rendez-vous annulé'),
            content=_('Votre rendez-vous du {} a été annulé par l\'expert.').format(
                appointment.date_time.strftime('%d/%m/%Y à %H:%M')
            ),
            related_rendez_vous=appointment
        )
        
        # Send email notification to client about appointment cancellation
        EmailNotificationService.send_appointment_notification(
            client=appointment.client,
            expert=request.user,
            appointment=appointment,
            notification_type='cancelled'
        )
        
        # Add a success message
        messages.success(request, _('Le rendez-vous a été annulé avec succès.'))
        
        return redirect('expert_rendezvous')
    
    except Expert.DoesNotExist:
        return redirect('home')

@login_required
def expert_complete_appointment(request, appointment_id):
    """Mark an appointment as completed."""
    if request.user.account_type.lower() != 'expert':
        return redirect('home')

    try:
        expert = Expert.objects.get(user=request.user)
        
        # Get appointment details
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=request.user)
        
        # Update appointment status
        appointment.status = 'completed'
          # Get notes from POST data if any
        notes = request.POST.get('notes', '')
        if notes:
            appointment.notes = notes
            appointment.save()
        
        # Create notification for client
        Notification.objects.create(
            user=appointment.client,
            type='appointment_update',
            title=_('Rendez-vous terminé'),
            content=_('Votre rendez-vous du {} a été marqué comme terminé par l\'expert.').format(
                appointment.date_time.strftime('%d/%m/%Y à %H:%M')
            ),
            related_rendez_vous=appointment
        )
        
        # Send email notification to client about appointment completion
        EmailNotificationService.send_request_status_update(
            client=appointment.client,
            expert=request.user,
            request_obj=appointment.service_request if appointment.service_request else None,
            new_status='completed',
            updated_by=request.user
        )
        
        # Add a success message
        messages.success(request, _('Le rendez-vous a été marqué comme terminé avec succès.'))
        
        return redirect('expert_appointment_detail', appointment_id=appointment.id)
    
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
        appointment = get_object_or_404(RendezVous, id=appointment_id, expert=request.user)
        
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
