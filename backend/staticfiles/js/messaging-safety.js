/**
 * Messaging System Safety Enhancements
 * 
 * This script provides defensive programming techniques to prevent browser crashes
 * and enhance the stability of the messaging system.
 */

(function() {
    'use strict';
    
    // Global variables to track state and prevent excessive operations
    let messagePollingActive = false;
    let lastPollTime = 0;
    let maxPollFrequency = 5000; // ms
    let consecutiveErrorCount = 0;
    let maxConsecutiveErrors = 3;
    
    // Safely get and parse contact ID
    function getSafeContactId() {
        // Find the active contact
        const activeContact = document.querySelector('.contact-item.active');
        if (!activeContact || !activeContact.dataset.contactId) {
            return null;
        }
        
        // Validate that it's a number
        const contactId = activeContact.dataset.contactId;
        const parsedId = parseInt(contactId, 10);
        
        if (isNaN(parsedId) || parsedId <= 0) {
            console.warn('Invalid contact ID detected:', contactId);
            return null;
        }
        
        return parsedId;
    }
    
    // Safe version of the contact item click handler
    function setupSafeContactClicks() {
        // Unbind any existing handlers to prevent duplicates
        const contactItems = document.querySelectorAll('.contact-item');
        
        contactItems.forEach(item => {
            // First, remove existing click handlers by cloning and replacing
            const newItem = item.cloneNode(true);
            if (item.parentNode) {
                item.parentNode.replaceChild(newItem, item);
            }
            
            // Then add our safe handler
            newItem.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get and validate contact ID
                const contactId = this.dataset.contactId;
                if (!contactId) {
                    console.warn('No contact ID found');
                    return;
                }
                
                const parsedId = parseInt(contactId, 10);
                if (isNaN(parsedId) || parsedId <= 0) {
                    console.warn('Invalid contact ID:', contactId);
                    return;
                }
                
                // Check for rapid clicking (prevent within 1 second)
                const lastClick = sessionStorage.getItem('lastContactClick');
                const now = Date.now();
                
                if (lastClick && (now - parseInt(lastClick, 10)) < 1000) {
                    console.log('Click throttled to prevent rapid navigation');
                    return;
                }
                
                // Store click time
                sessionStorage.setItem('lastContactClick', now);
                
                // Navigate with timeout to allow the click event to complete
                setTimeout(() => {
                    const baseUrl = document.querySelector('meta[name="client-messages-url"]')?.getAttribute('content') || '/client/messages/';
                    window.location.href = `${baseUrl}?contact=${parsedId}`;
                }, 50);
            });
        });
    }
    
    // Safe polling for new messages
    function safeCheckNewMessages() {
        // Throttle checks to prevent overwhelming the server
        const now = Date.now();
        if (messagePollingActive || (now - lastPollTime < maxPollFrequency)) {
            return;
        }
        
        // Get contact ID safely
        const contactId = getSafeContactId();
        if (!contactId) {
            return;
        }
        
        // Mark that we're actively polling
        messagePollingActive = true;
        lastPollTime = now;
        
        // Add timestamp to prevent caching
        const timestamp = now;
        
        // Get the check URL from meta tag or construct it
        const checkUrl = document.querySelector('meta[name="check-messages-url"]')?.getAttribute('content') || 
                        '/client/check-messages/';
        
        // Handle the fetch operation in a try-catch
        try {
            fetch(`${checkUrl}?contact=${contactId}&_=${timestamp}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                },
                // Set a reasonable timeout
                signal: AbortSignal.timeout(5000)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Reset error counter on success
                consecutiveErrorCount = 0;
                
                // Only reload if explicitly told to and we haven't recently reloaded
                if (data.success && data.new_messages) {
                    const lastReload = sessionStorage.getItem('lastMessageReload');
                    const now = Date.now();
                    
                    // Only reload if it's been at least 10 seconds since last reload
                    if (!lastReload || (now - parseInt(lastReload, 10)) > 10000) {
                        console.log('Reloading for new messages');
                        sessionStorage.setItem('lastMessageReload', now);
                        
                        // Use location.replace instead of reload to avoid history issues
                        window.location.replace(window.location.href);
                    }
                }
            })
            .catch(error => {
                console.error('Error checking for messages:', error);
                consecutiveErrorCount++;
                
                // If we've had too many consecutive errors, stop polling
                if (consecutiveErrorCount >= maxConsecutiveErrors) {
                    console.warn('Disabling message polling due to consecutive errors');
                    clearInterval(pollInterval);
                }
            })
            .finally(() => {
                // Always mark polling as complete
                messagePollingActive = false;
            });
        } catch (error) {
            console.error('Fatal error in message polling:', error);
            messagePollingActive = false;
            consecutiveErrorCount++;
        }
    }
    
    // Safe initialization function
    function safeInit() {
        try {
            // Setup contact clicks safely
            setupSafeContactClicks();
            
            // Setup polling with increasing backoff on errors
            let pollInterval = setInterval(() => {
                // Increase polling time based on consecutive errors
                maxPollFrequency = 5000 + (consecutiveErrorCount * 5000);
                
                // Cap at 30 seconds
                if (maxPollFrequency > 30000) {
                    maxPollFrequency = 30000;
                }
                
                safeCheckNewMessages();
            }, 10000);
            
            // Clean up when leaving the page
            window.addEventListener('beforeunload', () => {
                clearInterval(pollInterval);
            });
            
            console.log('Messaging safety enhancements loaded successfully');
        } catch (error) {
            console.error('Error initializing messaging safety:', error);
        }    }
    
    // Add a meta tag for the check messages URL
    function addUrlMetaTags() {
        // Get URLs from the page or use defaults
        const checkUrl = document.querySelector('a[data-check-messages-url]')?.getAttribute('data-check-messages-url') || 
                          '/requests/client/check_messages/';
        
        const messagesUrl = document.querySelector('a[data-messages-url]')?.getAttribute('data-messages-url') || 
                           '/client/messages/';
        
        // Create meta tags if they don't exist
        if (!document.querySelector('meta[name="check-messages-url"]')) {
            const meta = document.createElement('meta');
            meta.name = 'check-messages-url';
            meta.content = checkUrl;
            document.head.appendChild(meta);
        }
        
        if (!document.querySelector('meta[name="client-messages-url"]')) {
            const meta = document.createElement('meta');
            meta.name = 'client-messages-url';
            meta.content = messagesUrl;
            document.head.appendChild(meta);
        }
    }
    
    // Wait for DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            addUrlMetaTags();
            safeInit();
        });
    } else {
        addUrlMetaTags();
        safeInit();
    }
    
    // Export functions for debugging
    window.messagingSafety = {
        checkMessages: safeCheckNewMessages,
        setupClicks: setupSafeContactClicks,
        getContactId: getSafeContactId
    };
})();
