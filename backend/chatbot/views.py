from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.paginator import Paginator
import json
import uuid
import time
import requests
from datetime import datetime, timedelta

from .models import ChatSession, ChatMessage, ChatFeedback, ChatAnalytics, ChatbotConfiguration


class ChatbotView(View):
    """Vue principale pour l'interface du chatbot"""
    
    def get(self, request):
        """Afficher l'interface chatbot"""
        context = {
            'user_is_client': request.user.is_authenticated,
            'show_chatbot': True,
        }
        return render(request, 'chatbot/chatbot.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    """API pour les interactions du chatbot"""
    
    def post(self, request):
        """Traiter un message utilisateur"""
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id')
            
            if not user_message:
                return JsonResponse({'error': 'Message requis'}, status=400)
            
            # Créer ou récupérer la session
            session = self.get_or_create_session(request, session_id)
            
            # Enregistrer le message utilisateur
            user_msg = ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message,
                domain_category=self.classify_domain(user_message)
            )
            
            # Générer la réponse du bot
            start_time = time.time()
            bot_response = self.generate_bot_response(user_message, session)
            response_time = int((time.time() - start_time) * 1000)
            
            # Enregistrer la réponse du bot
            bot_msg = ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content=bot_response,
                response_time_ms=response_time,
                domain_category=user_msg.domain_category
            )
            
            # Mettre à jour les analytics
            self.update_analytics(user_msg.domain_category)
            
            return JsonResponse({
                'response': bot_response,
                'session_id': session.session_id,
                'message_id': bot_msg.id,
                'response_time': response_time
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_or_create_session(self, request, session_id=None):
        """Créer ou récupérer une session de chat"""
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id, is_active=True)
                session.updated_at = timezone.now()
                session.save()
                return session
            except ChatSession.DoesNotExist:
                pass
        
        # Créer une nouvelle session
        session = ChatSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=str(uuid.uuid4()),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=self.get_client_ip(request)        )
        return session
    
    def get_client_ip(self, request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def classify_domain(self, message):
        """Classifier le domaine de la question"""
        message_lower = message.lower()
        
        # Mots-clés par domaine
        keywords = {
            'fiscalite': ['impôt', 'taxe', 'déclaration', 'fiscal', 'tva', 'ir', 'is', 'convention'],
            'immobilier': ['maison', 'appartement', 'terrain', 'achat', 'vente', 'location', 'immobilier'],
            'investissement': ['investir', 'placement', 'bourse', 'opcvm', 'action', 'obligation', 'projet'],
            'administration': ['consulat', 'passeport', 'visa', 'état civil', 'document', 'carte'],
            'formation': ['formation', 'diplôme', 'certification', 'cours', 'apprentissage', 'métier']
        }
        
        for domain, words in keywords.items():
            if any(word in message_lower for word in words):
                return domain
        
        return 'other'
    
    def generate_bot_response(self, user_message, session):
        """Générer une réponse du bot via l'API Gemini"""
        try:
            # Récupérer la clé API et le modèle depuis la configuration
            api_key = ChatbotConfiguration.get_value('gemini_api_key', '')
            model = ChatbotConfiguration.get_value('gemini_model', 'gemini-pro')
            
            if not api_key:
                print("Erreur: Clé API Gemini manquante")
                return self.get_fallback_response()
            
            # Vérifier si la question est similaire aux questions précédentes
            if self.is_question_repeated(user_message, session):
                return """🇲🇦 Je remarque que vous avez posé une question similaire. 

Pour vous aider au mieux, pourriez-vous :
• Préciser votre question
• Donner plus de détails sur votre situation
• Me dire si ma réponse précédente n'était pas claire

Je suis là pour vous aider avec précision !"""
            
            # Récupérer l'historique des messages récents (limité à 3 pour éviter la confusion)
            recent_messages = ChatMessage.objects.filter(
                session=session
            ).order_by('-created_at')[:3]
            
            # Construire l'historique de conversation avec un format plus strict
            conversation_history = []
            
            # Ajouter le message système en premier
            system_prompt = self.get_system_prompt(session.user)
            conversation_history.append({
                "role": "system",
                "parts": [{"text": system_prompt}]
            })
            
            # Ajouter l'historique des messages
            for msg in reversed(recent_messages):
                role = "user" if msg.message_type == "user" else "assistant"
                # Ajouter un préfixe pour différencier les messages
                prefix = "Question: " if role == "user" else "Réponse: "
                conversation_history.append({
                    "role": role,
                    "parts": [{"text": f"{prefix}{msg.content}"}]
                })
            
            # Ajouter le message actuel
            conversation_history.append({
                "role": "user",
                "parts": [{"text": f"Question: {user_message}"}]
            })
            
            # Préparer la requête pour Gemini avec des paramètres plus stricts
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            payload = {
                "contents": conversation_history,
                "generationConfig": {
                    "temperature": 0.7,  # Réduit pour plus de cohérence
                    "topK": 20,  # Réduit pour plus de précision
                    "topP": 0.8,  # Réduit pour éviter les répétitions
                    "maxOutputTokens": 800,  # Réduit pour des réponses plus concises
                    "stopSequences": ["Question:", "Réponse:", "User:", "Assistant:"]
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Faire la requête avec un timeout plus court
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'candidates' in data and data['candidates']:
                bot_response = data['candidates'][0]['content']['parts'][0]['text']
                
                # Nettoyer la réponse (enlever les préfixes potentiels)
                bot_response = bot_response.replace("Réponse:", "").strip()
                
                # Vérifications supplémentaires
                if (self.is_response_repetitive(bot_response, session) or 
                    len(bot_response) < 20 or  # Réponse trop courte
                    len(bot_response) > 1000):  # Réponse trop longue
                    return self.get_fallback_response()
                
                return bot_response
            else:
                print("Erreur: Pas de réponse valide de l'API Gemini")
                return self.get_fallback_response()
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête API Gemini: {e}")
            return self.get_fallback_response()
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            return self.get_fallback_response()
    
    def is_question_repeated(self, question, session):
        """Vérifier si la question est similaire aux questions précédentes"""
        recent_questions = ChatMessage.objects.filter(
            session=session,
            message_type='user'
        ).order_by('-created_at')[:3]  # Dernières 3 questions
        
        for msg in recent_questions:
            if self.calculate_similarity(question, msg.content) > 0.7:  # Seuil plus bas pour les questions
                return True
        return False
    
    def is_response_repetitive(self, response, session):
        """Vérifier si la réponse est trop similaire aux messages précédents"""
        recent_bot_messages = ChatMessage.objects.filter(
            session=session,
            message_type='bot'
        ).order_by('-created_at')[:3]
        
        # Vérifications multiples
        for msg in recent_bot_messages:
            # Vérifier la similarité globale
            if self.calculate_similarity(response, msg.content) > 0.6:  # Seuil plus strict
                return True
            
            # Vérifier les phrases identiques
            response_sentences = set(s.strip() for s in response.split('.') if len(s.strip()) > 20)
            msg_sentences = set(s.strip() for s in msg.content.split('.') if len(s.strip()) > 20)
            
            if response_sentences.intersection(msg_sentences):
                return True
        
        return False
    
    def calculate_similarity(self, text1, text2):
        """Calculer la similarité entre deux textes (méthode simple)"""
        # Convertir en minuscules et en ensembles de mots
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculer le coefficient de Jaccard
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def get_system_prompt(self, user):
        """Construire le prompt système personnalisé"""
        client_status = "client inscrit" if user and user.is_authenticated else "nouveau visiteur"
        
        return f"""Tu es un expert des services aux Marocains Résidant à l'Étranger (MRE). 

DOMAINES D'EXPERTISE EXCLUSIFS:
- 📊 Fiscalité (impôts, déclarations, conventions fiscales)
- 🏠 Immobilier au Maroc (achat, vente, investissement)
- 💰 Investissements (OPCVM, bourse, projets)
- 📋 Administration (documents, visas, consulats)
- 🎓 Formation professionnelle (certifications, reconversion)

INSTRUCTIONS STRICTES:
1. Réponds UNIQUEMENT aux questions liées à ces 5 domaines
2. Si la question est hors sujet, réponds poliment que tu ne peux traiter que les sujets MRE
3. Si tu ne peux pas répondre précisément, propose une assistance personnalisée
4. L'utilisateur est actuellement: {client_status}

LOGIQUE CONDITIONNELLE:
- Si nouveau visiteur → propose inscription sur la plateforme
- Si client inscrit → propose de remplir une demande de service

STYLE DE RÉPONSE:
- Utilise le drapeau 🇲🇦 dans tes messages
- Reste professionnel mais chaleureux
- Sois concis et précis
- Utilise des puces pour organiser l'information
- Propose toujours une action concrète

Réponds en français uniquement."""
    
    def get_fallback_response(self):
        """Réponse de secours en cas d'erreur"""
        return """🇲🇦 Je rencontre une difficulté technique temporaire. 

En attendant, je peux vous orienter vers nos ressources :

• 📊 Questions fiscales → Consultez notre guide fiscal MRE
• 🏠 Immobilier → Découvrez nos opportunités d'investissement
• 💰 Placements → Explorez nos solutions d'épargne
• 📋 Administration → Trouvez les formulaires consulaires
• 🎓 Formation → Parcourez notre catalogue de formations

💡 Pour une assistance personnalisée immédiate, n'hésitez pas à vous inscrire sur notre plateforme ou à contacter directement nos experts."""
    
    def update_analytics(self, domain_category):
        """Mettre à jour les analytics quotidiennes"""
        today = timezone.now().date()
        analytics, created = ChatAnalytics.objects.get_or_create(date=today)
        
        analytics.total_messages += 1
        
        # Incrémenter le compteur de domaine
        if domain_category == 'fiscalite':
            analytics.fiscalite_questions += 1
        elif domain_category == 'immobilier':
            analytics.immobilier_questions += 1
        elif domain_category == 'investissement':
            analytics.investissement_questions += 1
        elif domain_category == 'administration':
            analytics.administration_questions += 1
        elif domain_category == 'formation':
            analytics.formation_questions += 1
        else:
            analytics.off_topic_questions += 1
        
        analytics.save()


@method_decorator(csrf_exempt, name='dispatch')
class ChatFeedbackView(View):
    """Vue pour enregistrer le feedback utilisateur"""
    
    def post(self, request):
        """Enregistrer un feedback"""
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            feedback_type = data.get('feedback_type')
            comment = data.get('comment', '')
            
            if not message_id or not feedback_type:
                return JsonResponse({'error': 'message_id et feedback_type requis'}, status=400)
            
            message = ChatMessage.objects.get(id=message_id)
            
            feedback = ChatFeedback.objects.create(
                message=message,
                feedback_type=feedback_type,
                comment=comment,
                ip_address=self.get_client_ip(request)
            )
            
            return JsonResponse({'status': 'success', 'feedback_id': feedback.id})
            
        except ChatMessage.DoesNotExist:
            return JsonResponse({'error': 'Message non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def get_client_ip(self, request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@login_required
def chat_history(request):
    """Historique des conversations pour l'utilisateur connecté"""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sessions': page_obj,
        'total_sessions': sessions.count()
    }
    return render(request, 'chatbot/history.html', context)


@login_required 
def chat_analytics(request):
    """Tableau de bord analytics pour les admins"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    # Analytics des 30 derniers jours
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    analytics = ChatAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
      # Agrégations
    total_stats = analytics.aggregate(
        total_sessions=Sum('total_sessions'),
        total_messages=Sum('total_messages'),
        avg_response_time=Avg('avg_response_time_ms'),
        avg_satisfaction=Avg('satisfaction_avg')
    )
    
    # Top domaines
    domain_stats = {
        'fiscalite': analytics.aggregate(Sum('fiscalite_questions'))['fiscalite_questions__sum'] or 0,
        'immobilier': analytics.aggregate(Sum('immobilier_questions'))['immobilier_questions__sum'] or 0,
        'investissement': analytics.aggregate(Sum('investissement_questions'))['investissement_questions__sum'] or 0,
        'administration': analytics.aggregate(Sum('administration_questions'))['administration_questions__sum'] or 0,
        'formation': analytics.aggregate(Sum('formation_questions'))['formation_questions__sum'] or 0,
        'off_topic': analytics.aggregate(Sum('off_topic_questions'))['off_topic_questions__sum'] or 0,
    }
    
    context = {
        'analytics': analytics,
        'total_stats': total_stats,
        'domain_stats': domain_stats,
        'date_range': f"{start_date} - {end_date}"
    }
    
    return render(request, 'chatbot/analytics.html', context)
