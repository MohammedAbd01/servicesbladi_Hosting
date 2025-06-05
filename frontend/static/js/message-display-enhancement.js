/**
 * Message Display Enhancement
 * 
 * This script ensures that message content is properly displayed and formatted,
 * preventing issues with malformed content that could cause browser crashes.
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        maxMessageLength: 5000, // Characters
        maxMessageDisplayLength: 1000, // Characters before truncation in UI
        sanitizationEnabled: true,
        messageSelector: '.message-content div:first-child'
    };
    
    // Message sanitization function
    function sanitizeMessageContent(content) {
        if (!config.sanitizationEnabled) return content;
        
        try {
            // Basic sanitization
            let sanitized = content
                // Convert potential HTML entities
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;')
                // Remove any script-like content
                .replace(/javascript:/gi, 'blocked:')
                .replace(/on\w+=/gi, 'data-blocked=');
                
            // Check length and truncate if needed
            if (sanitized.length > config.maxMessageLength) {
                sanitized = sanitized.substring(0, config.maxMessageLength) + '... [message truncated]';
            }
            
            return sanitized;
        } catch (e) {
            console.error('Error sanitizing message:', e);
            return '[Message content could not be displayed]';
        }
    }
    
    // Function to safely process and display message content
    function processMessageDisplay() {
        const messageContents = document.querySelectorAll(config.messageSelector);
        
        messageContents.forEach(messageElement => {
            try {
                // Skip already processed messages
                if (messageElement.hasAttribute('data-processed')) return;
                
                // Get and sanitize the content
                const originalContent = messageElement.textContent;
                const sanitizedContent = sanitizeMessageContent(originalContent);
                
                // Display the content safely (with truncation for display if needed)
                if (sanitizedContent.length > config.maxMessageDisplayLength) {
                    const shortContent = sanitizedContent.substring(0, config.maxMessageDisplayLength);
                    
                    // Create a controlled UI for long messages
                    messageElement.innerHTML = `
                        <div class="message-preview">${shortContent}...</div>
                        <button class="message-expand-btn">Show more</button>
                        <div class="message-full" style="display:none;">${sanitizedContent}</div>
                    `;
                    
                    // Add toggle functionality
                    const expandBtn = messageElement.querySelector('.message-expand-btn');
                    if (expandBtn) {
                        expandBtn.addEventListener('click', function() {
                            const preview = messageElement.querySelector('.message-preview');
                            const full = messageElement.querySelector('.message-full');
                            
                            if (preview.style.display === 'none') {
                                preview.style.display = 'block';
                                full.style.display = 'none';
                                this.textContent = 'Show more';
                            } else {
                                preview.style.display = 'none';
                                full.style.display = 'block';
                                this.textContent = 'Show less';
                            }
                        });
                    }
                } else {
                    // For normal length messages, just set the content
                    messageElement.textContent = sanitizedContent;
                }
                
                // Mark as processed
                messageElement.setAttribute('data-processed', 'true');
            } catch (e) {
                console.error('Error processing message display:', e);
                messageElement.textContent = '[Message could not be displayed]';
                messageElement.setAttribute('data-processed', 'true');
            }
        });
    }
    
    // Process messages when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        try {
            processMessageDisplay();
            
            // Also observe for dynamically added messages
            const observer = new MutationObserver(function(mutations) {
                let hasNewMessages = false;
                
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList' && mutation.addedNodes.length) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1 && 
                                (node.classList.contains('message') || 
                                 node.querySelector && node.querySelector('.message-content'))) {
                                hasNewMessages = true;
                            }
                        });
                    }
                });
                
                if (hasNewMessages) {
                    processMessageDisplay();
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        } catch (e) {
            console.error('Error initializing message display enhancement:', e);
        }
    });
    
    // Process on initial load and also after AJAX content loads
    window.addEventListener('load', processMessageDisplay);
    
    // Expose API for debugging
    window.messageDisplayEnhancement = {
        processMessages: processMessageDisplay,
        config: config
    };
})();
