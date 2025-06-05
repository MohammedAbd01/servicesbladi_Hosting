import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from custom_requests.models import ServiceRequest, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.room_group_name = f'chat_{self.request_id}'

        # Vérifier si l'utilisateur est autorisé à accéder à cette demande
        if not await self.is_user_authorized():
            await self.close()
            return

        # Rejoindre la room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Quitter la room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        # Handle typing indicators
        if 'typing' in text_data_json:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'typing': {
                        'user_id': self.scope['user'].id,
                        'user_name': getattr(self.scope['user'], 'name', self.scope['user'].username or self.scope['user'].email),
                        'is_typing': text_data_json['typing']
                    }
                }
            )
            return
        
        # Handle regular messages
        if 'message' in text_data_json:
            message = text_data_json['message']

            # Sauvegarder le message en base de données
            saved_message = await self.save_message(message)

            # Envoyer le message à la room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.scope['user'].id,
                    'sender_name': getattr(self.scope['user'], 'name', self.scope['user'].username or self.scope['user'].email),
                    'timestamp': saved_message.sent_at.isoformat() if saved_message else None
                }
            )

    async def chat_message(self, event):
        # Envoyer le message au websocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))

    async def typing_indicator(self, event):
        # Envoyer l'indicateur de frappe au websocket
        await self.send(text_data=json.dumps({
            'typing': event['typing']
        }))

    @database_sync_to_async
    def is_user_authorized(self):
        """Vérifie si l'utilisateur est autorisé à accéder à cette conversation"""
        user = self.scope['user']
        if not user.is_authenticated:
            return False

        try:
            request = ServiceRequest.objects.get(pk=self.request_id)
            # Vérifier si l'utilisateur est le client ou l'expert associé à cette demande
            return user == request.client or user == request.expert or user.is_staff
        except ServiceRequest.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_text):
        """Enregistre le message dans la base de données"""
        user = self.scope['user']
        try:
            request = ServiceRequest.objects.get(pk=self.request_id)
            
            # Determine recipient based on sender
            if user == request.client:
                recipient = request.expert
            elif user == request.expert:
                recipient = request.client
            else:
                recipient = None  # For staff users
            
            message = Message.objects.create(
                service_request=request,
                sender=user,
                recipient=recipient,
                content=message_text
            )
            return message
        except (ServiceRequest.DoesNotExist, Exception):
            return None
