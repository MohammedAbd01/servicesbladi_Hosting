/**
 * Messaging Text Layout Fix - JavaScript Component
 * Ensures proper horizontal text flow in messaging interfaces
 * Prevents vertical character stacking issues
 */

(function() {
    'use strict';
    
    // Function to fix message content styles
    function fixMessageContentStyles() {
        const messageContents = document.querySelectorAll('.message-content, .message .message-content');
        
        messageContents.forEach(function(element) {
            // Remove problematic CSS properties
            element.style.setProperty('word-break', 'normal', 'important');
            element.style.setProperty('white-space', 'normal', 'important');
            element.style.setProperty('overflow-wrap', 'normal', 'important');
            element.style.setProperty('word-wrap', 'normal', 'important');
            
            // Ensure proper text orientation
            element.style.setProperty('text-orientation', 'mixed', 'important');
            element.style.setProperty('writing-mode', 'horizontal-tb', 'important');
            element.style.setProperty('direction', 'ltr', 'important');
            
            // Ensure proper display
            element.style.setProperty('display', 'block', 'important');
            element.style.setProperty('line-height', '1.4', 'important');
            
            // Reset font properties that might interfere
            element.style.setProperty('font-feature-settings', 'normal', 'important');
            element.style.setProperty('font-variant', 'normal', 'important');
            element.style.setProperty('text-transform', 'none', 'important');
        });
    }
    
    // Function to fix message bubble sizing
    function fixMessageBubbleSizing() {
        const messages = document.querySelectorAll('.message, [class*="message"]');
        
        messages.forEach(function(element) {
            // Ensure adequate width for text flow
            if (!element.style.minWidth) {
                element.style.setProperty('min-width', '120px', 'important');
            }
            if (!element.style.maxWidth) {
                element.style.setProperty('max-width', '85%', 'important');
            }
            
            // Ensure proper box model
            element.style.setProperty('box-sizing', 'border-box', 'important');
        });
    }
    
    // Apply fixes immediately
    function applyFixes() {
        fixMessageContentStyles();
        fixMessageBubbleSizing();
    }
    
    // Apply fixes when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyFixes);
    } else {
        applyFixes();
    }
    
    // Create a MutationObserver to handle dynamically added messages
    const observer = new MutationObserver(function(mutations) {
        let needsUpdate = false;
        
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    if (node.classList.contains('message') || 
                        node.querySelector && node.querySelector('.message-content')) {
                        needsUpdate = true;
                    }
                }
            });
        });
        
        if (needsUpdate) {
            // Delay slightly to allow other scripts to finish
            setTimeout(applyFixes, 10);
        }
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Re-apply fixes periodically as a safety measure
    setInterval(function() {
        const problemElements = document.querySelectorAll('.message-content[style*="word-break: break"], .message-content[style*="white-space: pre"]');
        if (problemElements.length > 0) {
            console.log('Messaging layout fix: Re-applying styles to', problemElements.length, 'elements');
            applyFixes();
        }
    }, 2000);
    
    // Export function for manual usage if needed
    window.fixMessagingLayout = applyFixes;
    
    console.log('Messaging text layout fix loaded and active');
})();
