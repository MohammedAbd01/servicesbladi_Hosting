from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Utilisateur, Client, Expert
from .models import Message, Notification, ServiceRequest
from services.email_notifications import EmailNotificationService

@login_required
def client_messages_view(request):
    """Display client's messages and handle conversations"""
    # Get the active contact if provided
    active_contact_id = request.GET.get('contact')
    active_contact = None
    messages_list = []
    
    # Get all messages for this user
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # Group messages by conversation
    conversations = {}
    for message in all_messages:
        # Determine the other party in the conversation
        other_party = message.recipient if message.sender == request.user else message.sender
          # Create a unique key for this conversation
        conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"            # Check if other_party user object is valid before proceeding
        if other_party is None or not hasattr(other_party, 'id'):
            continue
            
        # Safely get and truncate message content to prevent display issues
        try:
            if message.content:
                # Limit content length to prevent performance issues
                safe_content = message.content[:2000]  # Limit to 2000 chars
                # Replace potentially problematic characters that might cause display issues
                safe_content = safe_content.replace('<', '&lt;').replace('>', '&gt;')
            else:
                safe_content = ""
        except Exception as e:
            print(f"Error processing message content: {str(e)}")
            safe_content = "[Message content unavailable]"
            
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'user': other_party,
                'latest_message': message,
                'unread_count': 1 if message.recipient == request.user and not message.is_read else 0,
                'last_message': safe_content[:50] + '...' if len(safe_content) > 50 else safe_content,
                'last_message_time': message.sent_at
            }
        else:            # Update latest message if this one is newer
            if message.sent_at > conversations[conversation_key]['latest_message'].sent_at:
                conversations[conversation_key]['latest_message'] = message
                
                # Safely get and truncate message content
                try:
                    if message.content:
                        # Limit content length to prevent performance issues
                        safe_content = message.content[:2000]  # Limit to 2000 chars
                        # Replace potentially problematic characters
                        safe_content = safe_content.replace('<', '&lt;').replace('>', '&gt;')
                    else:
                        safe_content = ""
                except Exception as e:
                    print(f"Error processing message content: {str(e)}")
                    safe_content = "[Message content unavailable]"
                
                conversations[conversation_key]['last_message'] = safe_content[:50] + '...' if len(safe_content) > 50 else safe_content
                conversations[conversation_key]['last_message_time'] = message.sent_at
            
            # Update unread count
            if message.recipient == request.user and not message.is_read:
                conversations[conversation_key]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message date
    contacts = sorted(
        conversations.values(),
        key=lambda x: x['latest_message'].sent_at,
        reverse=True
    )
      # If a contact is selected, get conversation with that contact
    if active_contact_id:
        try:
            # Convert to integer to prevent injection
            active_contact_id = int(active_contact_id)
            
            try:
                active_contact = Utilisateur.objects.get(id=active_contact_id)
                  # Get conversation messages
                messages_list = Message.objects.filter(
                    (Q(sender=request.user) & Q(recipient=active_contact)) |
                    (Q(sender=active_contact) & Q(recipient=request.user))
                ).order_by('sent_at')
                  # Process message content for safety
                safe_messages = []
                for msg in messages_list:
                    try:
                        # Create a safe copy of the message
                        safe_msg = msg
                        
                        # Sanitize content if it exists
                        if msg.content:
                            # Limit content length and sanitize
                            safe_content = msg.content[:10000]  # 10k char limit for full messages
                            safe_content = safe_content.replace('<', '&lt;').replace('>', '&gt;')
                            safe_msg.content = safe_content
                        else:
                            safe_msg.content = ""
                            
                        safe_messages.append(safe_msg)
                    except Exception as e:
                        print(f"Error processing message {msg.id}: {str(e)}")
                        # Create a safe placeholder message
                        safe_msg = msg
                        safe_msg.content = "[Message content could not be displayed]"
                        safe_messages.append(safe_msg)
                
                # Mark messages as read
                unread_messages = Message.objects.filter(
                    recipient=request.user, 
                    is_read=False,
                    sender=active_contact
                )
                unread_messages.update(is_read=True, read_at=timezone.now())
                
                # Replace the original messages with sanitized ones
                messages_list = safe_messages
            except Utilisateur.DoesNotExist:
                # If contact doesn't exist, don't crash, just don't show any messages
                active_contact = None
                messages_list = []
        except ValueError:
            # If contact_id is not a valid integer, don't crash
            active_contact = None
            messages_list = []
    
    # Count total unread messages
    unread_messages_count = sum([conv['unread_count'] for conv in conversations.values()])
    
    context = {
        'contacts': contacts,
        'messages': messages_list,
        'active_contact': active_contact,
        'unread_messages_count': unread_messages_count
    }
    
    return render(request, 'client/messages.html', context)

@login_required
def client_send_message(request, recipient_id):
    """Handle sending a new message from client"""
    if request.method != 'POST':
        return redirect('client_messages')
    
    recipient = get_object_or_404(Utilisateur, id=recipient_id)
    content = request.POST.get('message', '').strip()
    
    if not content:
        return redirect('client_messages')
    
    try:
        # Sanitize and limit content length to prevent issues
        if len(content) > 10000:  # Limit to 10k chars
            content = content[:10000] + "... [message truncated]"
              # Create message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content
        )
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient,
            type='message',
            title=_('New Message'),
            content=_(f'You have a new message from {request.user.name} {request.user.first_name}.'),
            related_message=message
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
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sent_at': message.sent_at.isoformat()
                }
            })
        
        # Otherwise redirect back to the conversation
        return redirect(f'/client/messages/?contact={recipient_id}')
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while sending the message'
            })
        return redirect('client_messages')

@login_required
def client_check_messages(request):
    """Check for new messages in the current conversation"""
    contact_id = request.GET.get('contact')
    if not contact_id or contact_id == 'undefined':
        return JsonResponse({'success': False, 'error': 'Invalid contact ID'})
    
    try:
        # Convert contact_id to integer to prevent injection
        contact_id = int(contact_id)
        
        # Try to get the contact user
        try:
            contact = Utilisateur.objects.get(id=contact_id)
        except Utilisateur.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Contact not found'})
        
        # Check for new unread messages from this contact
        new_messages = Message.objects.filter(
            sender=contact,
            recipient=request.user,
            is_read=False
        ).exists()
        
        return JsonResponse({
            'success': True,
            'new_messages': new_messages
        })
    except ValueError:
        # Handle the case where contact_id is not a valid integer
        return JsonResponse({'success': False, 'error': 'Invalid contact ID format'})
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error in client_check_messages: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while checking messages'})

@login_required
def expert_messages_view(request):
    """Display expert's messages with clients"""
    # Similar logic to client_messages_view but for experts
    # Get the active client if provided
    active_client_id = request.GET.get('client')
    active_client = None
    messages_list = []
    
    # Get all messages for this expert
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-sent_at')
    
    # Group messages by conversation (similar to client_messages_view)
    conversations = {}
    for message in all_messages:
        other_party = message.recipient if message.sender == request.user else message.sender
        conversation_key = f"{min(request.user.id, other_party.id)}_{max(request.user.id, other_party.id)}"
        
        if other_party.account_type != 'client':
            continue  # Only show conversations with clients
        
        # Similar logic to client_messages_view...
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'id': other_party.id,
                'name': f"{other_party.name} {other_party.first_name}",
                'email': other_party.email,
                'latest_message': message.content[:50] + '...' if len(message.content) > 50 else message.content,
                'unread_count': 1 if message.recipient == request.user and not message.is_read else 0,
                'time': message.sent_at,
                'is_online': False  # This could be updated with a real online status system
            }
        else:
            if message.recipient == request.user and not message.is_read:
                conversations[conversation_key]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message time
    clients = sorted(
        conversations.values(),
        key=lambda x: x['time'],
        reverse=True
    )
    
    # If a client is selected, get conversation with that client
    if active_client_id:
        active_client = get_object_or_404(Utilisateur, id=active_client_id)
          # Get conversation messages
        messages_list = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient=active_client)) |
            (Q(sender=active_client) & Q(recipient=request.user))
        ).order_by('sent_at')
          # Mark messages as read - using Message.objects to ensure we're working with a QuerySet
        unread_messages = Message.objects.filter(
            recipient=request.user, 
            is_read=False,
            sender=active_client
        )
        unread_messages.update(is_read=True, read_at=timezone.now())
          # Limit message count to prevent memory issues (show only last 100 messages)
        messages_list = messages_list[:100]
        
        # Process message content for safety - using a more efficient approach
        # Instead of creating copies, we'll sanitize in the template or use a property
        # This prevents memory issues from object duplication
    
    # Count total unread messages
    unread_messages_count = sum([client.get('unread_count', 0) for client in clients])
    
    context = {
        'clients': clients,
        'messages': messages_list,
        'active_client': active_client,
        'unread_messages_count': unread_messages_count
    }
    
    return render(request, 'expert/messages.html', context)

@login_required
def expert_send_message(request, client_id):
    """Handle sending a new message from expert to client"""
    # Similar implementation to client_send_message
    if request.method != 'POST':
        return redirect('expert_messages')
    
    client = get_object_or_404(Utilisateur, id=client_id, account_type='client')
    content = request.POST.get('message', '').strip()
    
    if not content:
        return redirect('expert_messages')
    
    # Create message
    message = Message.objects.create(
        sender=request.user,
        recipient=client,
        content=content
    )
      # Create notification for client
    Notification.objects.create(
        user=client,
        type='message',
        title=_('New Message'),
        content=_(f'You have a new message from your expert {request.user.name} {request.user.first_name}.'),
        related_message=message
    )
    
    # Send email notification
    try:
        EmailNotificationService.send_new_message_notification(
            sender=request.user,
            recipient=client,
            message_content=content
        )
    except Exception as email_error:
        print(f"Failed to send email notification: {email_error}")
        # Continue without failing the request
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sent_at': message.sent_at.isoformat()
            }
        })
      # Otherwise redirect back to the conversation
    return redirect(f'/expert/messages/?client={client_id}')

@login_required
def expert_check_messages(request):
    """Check for new messages from a client"""
    # Similar implementation to client_check_messages
    client_id = request.GET.get('client')
    if not client_id or client_id == 'undefined':
        return JsonResponse({'success': False, 'error': 'Invalid client ID'})
    
    try:
        client = get_object_or_404(Utilisateur, id=client_id, account_type='client')
        
        # Check for new unread messages from this client
        new_messages = Message.objects.filter(
            sender=client,
            recipient=request.user,
            is_read=False
        ).exists()
        
        return JsonResponse({
            'success': True,
            'new_messages': new_messages
        })
    except ValueError:
        # Handle the case where client_id is not a valid integer
        return JsonResponse({'success': False, 'error': 'Invalid client ID format'})
