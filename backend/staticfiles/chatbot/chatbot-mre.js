// Chatbot MRE - Expert des services aux Marocains Résidant à l'Étranger
class ChatbotMRE {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.userIsClient = window.userIsClient || false; // Défini par Django
        this.sessionId = null; // Géré par le backend Django
        
        this.init();
    }

    init() {
        this.cacheDOMElements();
        this.bindEvents();
        this.addPulseAnimation();
    }

    cacheDOMElements() {
        this.chatbotButton = document.getElementById('chatbot-button');
        this.chatbotWindow = document.getElementById('chatbot-window');
        this.chatbotClose = document.getElementById('chatbot-close');
        this.chatbotInput = document.getElementById('chatbot-input');
        this.chatbotSend = document.getElementById('chatbot-send');
        this.chatbotMessages = document.getElementById('chatbot-messages');
        this.chatbotTyping = document.getElementById('chatbot-typing');
    }

    bindEvents() {
        this.chatbotButton.addEventListener('click', () => this.toggleChatbot());
        this.chatbotClose.addEventListener('click', () => this.closeChatbot());
        this.chatbotSend.addEventListener('click', () => this.sendMessage());
        
        this.chatbotInput.addEventListener('input', (e) => {
            this.chatbotSend.disabled = e.target.value.trim() === '';
        });
        
        this.chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Fermer avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChatbot();
            }
        });
    }

    addPulseAnimation() {
        // Animation d'attention toutes les 10 secondes
        setInterval(() => {
            if (!this.isOpen) {
                this.chatbotButton.classList.add('pulse');
                setTimeout(() => {
                    this.chatbotButton.classList.remove('pulse');
                }, 2000);
            }
        }, 10000);
    }

    toggleChatbot() {
        if (this.isOpen) {
            this.closeChatbot();
        } else {
            this.openChatbot();
        }
    }

    openChatbot() {
        this.chatbotWindow.classList.add('open');
        this.chatbotButton.style.display = 'none';
        this.isOpen = true;
        this.chatbotInput.focus();
    }

    closeChatbot() {
        this.chatbotWindow.classList.remove('open');
        this.chatbotButton.style.display = 'flex';
        this.isOpen = false;
    }

    async sendMessage() {
        const message = this.chatbotInput.value.trim();
        if (!message || this.isTyping) return;

        // Ajouter le message utilisateur
        this.addUserMessage(message);
        this.chatbotInput.value = '';
        this.chatbotSend.disabled = true;

        // Afficher l'indicateur de frappe
        this.showTyping();

        try {
            const response = await this.callGeminiAPI(message);
            this.hideTyping();
            this.addBotMessage(response);
        } catch (error) {
            this.hideTyping();
            this.addErrorMessage(error.message);
        }
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement(message, 'user');
        this.chatbotMessages.appendChild(messageElement);
        this.scrollToBottom();
    }    addBotMessage(message) {
        const messageElement = this.createMessageElement(message, 'bot');
        
        // Ajouter l'ID du message pour le feedback
        if (this.lastMessageId) {
            messageElement.dataset.messageId = this.lastMessageId;
        }
        
        this.chatbotMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        // Ajouter les boutons de feedback après un délai
        setTimeout(() => {
            this.addFeedbackButtons(messageElement);
        }, 1000);
    }

    addErrorMessage(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <strong>❌ Erreur de connexion</strong><br>
            ${error}<br>
            <small>Veuillez réessayer dans quelques instants.</small>
        `;
        this.chatbotMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    createMessageElement(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        const avatarImg = document.createElement('img');
        if (type === 'user') {
            avatarImg.src = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face&auto=format';
            avatarImg.alt = 'Utilisateur';
        } else {
            avatarImg.src = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=40&h=40&fit=crop&crop=face&auto=format';
            avatarImg.alt = 'Assistant MRE';
        }
        
        avatarDiv.appendChild(avatarImg);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Traiter le contenu (markdown simple, liens, etc.)
        contentDiv.innerHTML = this.processMessageContent(content, type);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        return messageDiv;
    }

    processMessageContent(content, type) {
        if (type === 'user') {
            return `<p>${this.escapeHtml(content)}</p>`;
        }

        // Traitement pour les messages du bot
        let processed = content;

        // Remplacer les émojis de drapeaux par le composant flag
        processed = processed.replace(/🇲🇦/g, '<span class="morocco-flag"></span>');

        // Traiter les listes
        processed = processed.replace(/^\* (.+)$/gm, '<li>$1</li>');
        processed = processed.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Traiter les paragraphes
        const paragraphs = processed.split('\n').filter(p => p.trim());
        processed = paragraphs.map(p => {
            if (p.includes('<ul>') || p.includes('<li>')) return p;
            return `<p>${p}</p>`;
        }).join('');

        // Ajouter des boutons d'action selon le contexte
        if (this.shouldAddActionButtons(content)) {
            processed += this.getActionButtons();
        }

        return processed;
    }

    shouldAddActionButtons(content) {
        const keywords = ['inscription', 'inscrire', 'compte', 'service', 'demande', 'aide personnalisée'];
        return keywords.some(keyword => content.toLowerCase().includes(keyword));
    }    getActionButtons() {
        if (this.userIsClient) {
            const serviceUrl = window.serviceRequestUrl || '/demande-service/';
            const dashboardUrl = window.myServicesUrl || '/mes-services/';
            return `
                <div class="action-buttons">
                    <a href="${serviceUrl}" class="action-btn">📋 Nouvelle demande</a>
                    <a href="${dashboardUrl}" class="action-btn">📊 Mes services</a>
                </div>
            `;
        } else {
            const registerUrl = window.registerUrl || '/inscription/';
            const loginUrl = window.loginUrl || '/connexion/';
            return `
                <div class="action-buttons">
                    <a href="${registerUrl}" class="action-btn">✨ S'inscrire</a>
                    <a href="${loginUrl}" class="action-btn">🔑 Se connecter</a>
                </div>
            `;
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    showTyping() {
        this.isTyping = true;
        this.chatbotTyping.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        this.chatbotTyping.style.display = 'none';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatbotMessages.scrollTop = this.chatbotMessages.scrollHeight;
        }, 100);
    }    async callGeminiAPI(userMessage) {
        // Utiliser l'API Django au lieu d'appeler directement Gemini
        const apiUrl = window.chatbotApiUrl || '/chatbot/api/chat/';
        
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: this.sessionId
                }),
                signal: controller.signal
            });

            clearTimeout(timeout);

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(`Erreur serveur (${response.status}): ${errorData?.error || 'Erreur inconnue'}`);
            }

            const data = await response.json();
              // Stocker l'ID de session pour les prochaines requêtes
            this.sessionId = data.session_id;
            this.lastMessageId = data.message_id; // Stocker l'ID du message pour le feedback
            
            return data.response;

        } catch (error) {
            clearTimeout(timeout);
            
            if (error.name === 'AbortError') {
                throw new Error('Délai d\'attente dépassé. Veuillez réessayer.');
            }
            
            console.error('Erreur API:', error);
            throw new Error(`Impossible de contacter l'assistant: ${error.message}`);
        }
    }    getCSRFToken() {
        // Récupérer le token CSRF depuis la configuration globale
        if (window.csrfToken) {
            return window.csrfToken;
        }
        
        // Alternative: récupérer depuis les cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Alternative: récupérer depuis un meta tag
        const csrfMeta = document.querySelector('meta[name=csrf-token]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        
        // Alternative: récupérer depuis un input hidden
        const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
          return '';
    }

    addFeedbackButtons(messageElement) {
        // Ne pas ajouter de feedback aux messages système
        if (messageElement.dataset.messageId) {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-buttons';
            feedbackDiv.innerHTML = `
                <small>Cette réponse vous a-t-elle aidé ?</small>
                <button class="feedback-btn helpful" data-feedback="helpful" title="Utile">👍</button>
                <button class="feedback-btn not-helpful" data-feedback="not_helpful" title="Pas utile">👎</button>
            `;
            
            const contentDiv = messageElement.querySelector('.message-content');
            contentDiv.appendChild(feedbackDiv);
            
            // Ajouter les événements de feedback
            feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.sendFeedback(messageElement.dataset.messageId, e.target.dataset.feedback);
                    feedbackDiv.innerHTML = '<small style="color: #28a745;">✓ Merci pour votre retour !</small>';
                });
            });
        }
    }

    async sendFeedback(messageId, feedbackType) {
        try {
            const response = await fetch(window.feedbackApiUrl || '/chatbot/api/feedback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message_id: messageId,
                    feedback_type: feedbackType
                })
            });

            if (response.ok) {
                console.log('Feedback envoyé avec succès');
            }
        } catch (error) {
            console.error('Erreur lors de l\'envoi du feedback:', error);
        }
    }

    getSystemPrompt() {
        const clientStatus = this.userIsClient ? "client inscrit" : "nouveau visiteur";
        
        return `Tu es un expert des services aux Marocains Résidant à l'Étranger (MRE). 

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
4. L'utilisateur est actuellement: ${clientStatus}

LOGIQUE CONDITIONNELLE:
- Si nouveau visiteur → propose inscription sur la plateforme
- Si client inscrit → propose de remplir une demande de service

STYLE DE RÉPONSE:
- Utilise le drapeau 🇲🇦 dans tes messages
- Reste professionnel mais chaleureux
- Sois concis et précis
- Utilise des puces pour organiser l'information
- Propose toujours une action concrète

Réponds en français uniquement.`;
    }
}

// Initialisation du chatbot
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si l'utilisateur est connecté (peut être défini par Django)
    if (typeof window.userIsClient === 'undefined') {
        window.userIsClient = false; // Par défaut, nouveau visiteur
    }
    
    // Initialiser le chatbot
    new ChatbotMRE();
});

// Export pour utilisation dans d'autres scripts
window.ChatbotMRE = ChatbotMRE;
