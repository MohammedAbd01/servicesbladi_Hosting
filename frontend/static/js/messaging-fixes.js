/**
 * ServicesBladi - Messaging Fixes Utilities
 * Common JavaScript functions to fix messaging interface issues
 * 1. Avatar Image Fallbacks
 * 2. Message Text Color/Contrast Fixes
 */

// Create a placeholder avatar with user initials
const createDefaultAvatar = (name = 'User') => {
    // Create a data URL for a default avatar with the user's initials
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 200;
    const context = canvas.getContext('2d');
    
    // Create a gradient background for better aesthetics
    const gradient = context.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#f0f2f5');
    gradient.addColorStop(1, '#e1e4e8');
    context.fillStyle = gradient;
    context.fillRect(0, 0, canvas.width, canvas.height);
    
    // Add a subtle circular border
    context.beginPath();
    context.arc(canvas.width/2, canvas.height/2, 95, 0, 2 * Math.PI);
    context.strokeStyle = 'rgba(0,0,0,0.1)';
    context.lineWidth = 3;
    context.stroke();
    
    // Text settings with improved font
    context.font = 'bold 80px Arial, Helvetica, sans-serif';
    context.fillStyle = '#5a7184';  // Softer blue-gray for better readability
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    
    // Get first initials from the name (max 2 characters)
    let initials = 'U';
    if (name && name !== 'User' && name !== 'undefined') {
        initials = name.split(' ')
            .filter(part => part && part.length > 0)
            .map(part => part.charAt(0))
            .join('')
            .toUpperCase()
            .substring(0, 2);
    }
    
    // Draw the text with a subtle shadow for depth
    context.shadowColor = 'rgba(0,0,0,0.1)';
    context.shadowBlur = 4;
    context.shadowOffsetX = 1;
    context.shadowOffsetY = 1;
    context.fillText(initials, canvas.width/2, canvas.height/2);
    
    return canvas.toDataURL('image/png');
};

// Fix all avatar images with improved error detection
const fixAvatarImages = () => {
    // Select all avatar images in the chat
    document.querySelectorAll('.contact-avatar, .chat-avatar, .profile-image, .avatar, .user-avatar, .profile-pic').forEach(img => {
        // Handle error when image fails to load
        img.onerror = function() {
            // Get name from alt text or use 'User'
            const name = this.alt || this.getAttribute('data-name') || 'User';
            // Generate and set a default avatar with initials
            this.src = createDefaultAvatar(name);
            // Add a class for styling
            this.classList.add('avatar-fallback');
            // Remove error handler to prevent loops
            this.onerror = null;
        };
        
        // Enhanced check for broken images:
        // 1. Image is fully loaded but has no width (broken)
        // 2. Image has no source or undefined source
        // 3. Image source is an invalid URL
        // 4. Image source ends with default placeholder that doesn't exist
        if ((img.complete && img.naturalWidth === 0) || 
            !img.src || 
            img.src === 'undefined' || 
            img.src.includes('undefined') ||
            (img.src.includes('/media/profile_pictures/') && img.src.endsWith('.jpg') && !img.naturalWidth)) {
            img.onerror();
        }
        
        // Also test image validity by trying to fetch it
        if (img.src && !img.src.startsWith('data:')) {
            fetch(img.src, { method: 'HEAD' })
                .catch(() => {
                    // If fetch fails, the image URL is invalid
                    if (!img.classList.contains('avatar-fallback')) {
                        img.onerror();
                    }
                });
        }
    });
};

// Fix any message bubble styles that might be dynamically added
const fixMessageStyles = () => {
    // Targets all outgoing message elements with the correct selectors
    document.querySelectorAll('.message-outgoing, .message.sent, .sent .message-content, .outgoing, .sent, .message.sent .message-content').forEach(msg => {
        // Fix the background color and remove any gradients
        msg.style.setProperty('background', '#DCF8C6', 'important');
        msg.style.setProperty('background-color', '#DCF8C6', 'important');
        msg.style.setProperty('background-image', 'none', 'important');
        msg.style.setProperty('color', '#1f1f1f', 'important');
        
        // Fix all child elements
        const allChildren = msg.querySelectorAll('*');
        allChildren.forEach(el => {
            el.style.setProperty('color', '#1f1f1f', 'important');
            el.style.setProperty('-webkit-text-fill-color', '#1f1f1f', 'important');
        });
        
        // Fix timestamps with special coloring
        const timestamps = msg.querySelectorAll('.message-timestamp, .message-time, .message-status');
        timestamps.forEach(timestamp => {
            timestamp.style.setProperty('color', 'rgba(31, 31, 31, 0.7)', 'important');
            timestamp.style.setProperty('-webkit-text-fill-color', 'rgba(31, 31, 31, 0.7)', 'important');
        });
    });
    
    // Fix any elements with inline styles that may be overriding our CSS
    document.querySelectorAll('[style*="background-color: rgb(0, 132, 255)"], [style*="background-color: #0084ff"]').forEach(el => {
        el.style.setProperty('background-color', '#DCF8C6', 'important');
        el.style.setProperty('color', '#1f1f1f', 'important');
        
        // Fix all child elements
        const allChildren = el.querySelectorAll('*');
        allChildren.forEach(child => {
            child.style.setProperty('color', '#1f1f1f', 'important');
        });
    });
};

// Run all fixes
const runAllMessageFixers = () => {
    fixAvatarImages();
    fixMessageStyles();
};

// Set up observer for dynamic content
const setupMessageFixesObserver = () => {
    // Watch for dynamically added elements with improved mutation handling
    const observer = new MutationObserver((mutations) => {
        let shouldFix = false;
        
        // Check if any relevant nodes were added
        mutations.forEach(mutation => {
            if (mutation.type === 'childList') {
                // Check added nodes
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        // If this is an image element that might need fixing
                        if (node.tagName === 'IMG') {
                            shouldFix = true;
                        }
                        // If this contains image elements that might need fixing
                        else if (node.querySelector && node.querySelector('img')) {
                            shouldFix = true;
                        }
                        // If this is a message or contains messages
                        else if (node.classList && 
                                (node.classList.contains('message') || 
                                 node.classList.contains('message-outgoing') || 
                                 node.classList.contains('sent'))) {
                            shouldFix = true;
                        }
                        // If this contains messages
                        else if (node.querySelector && 
                                (node.querySelector('.message') || 
                                 node.querySelector('.message-outgoing') || 
                                 node.querySelector('.sent'))) {
                            shouldFix = true;
                        }
                    }
                });
            }
            // Check attribute changes (src attribute of images or style attribute of messages)
            else if (mutation.type === 'attributes') {
                if (mutation.attributeName === 'src' && mutation.target.tagName === 'IMG') {
                    shouldFix = true;
                }
                else if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
                    shouldFix = true;
                }
            }
        });
        
        // Only run the fix if necessary
        if (shouldFix) {
            runAllMessageFixers();
        }
    });
    
    // Observe the entire body for changes, with all necessary options
    observer.observe(document.body, {
        childList: true,    // Watch for added/removed nodes
        subtree: true,      // Watch all descendants
        attributes: true,   // Watch attributes
        attributeFilter: ['src', 'style', 'class']  // Only care about these attribute changes
    });
};

// Initialize all messaging fixes
const initializeMessagingFixes = () => {
    // Run fixes immediately
    runAllMessageFixers();
    
    // Set up observer
    setupMessageFixesObserver();
    
    // Also run fixes when page is fully loaded (images, etc.)
    window.addEventListener('load', runAllMessageFixers);
    
    // Run periodically to catch any edge cases
    setInterval(runAllMessageFixers, 3000);
};

// If this script is loaded in a page with jQuery, run after DOM is ready
if (typeof jQuery !== 'undefined') {
    jQuery(document).ready(initializeMessagingFixes);
} else {
    // Otherwise run when DOM is loaded
    document.addEventListener('DOMContentLoaded', initializeMessagingFixes);
}
