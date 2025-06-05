/**
 * Message Anti-Crash Protection
 * 
 * This script detects and prevents potential browser crashes in the messaging system
 * by monitoring for memory leaks, infinite loops, and unresponsive UI elements.
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        memoryCheckInterval: 5000,  // How often to check memory usage (ms)
        memoryThreshold: 100,       // Memory increase threshold in MB that triggers intervention
        timeoutThreshold: 500,      // Timeout for detecting unresponsive UI (ms)
        maxConsecutiveSlowFrames: 5, // Number of consecutive slow frames before intervention
        maxPollingErrors: 3,        // Max number of fetch errors before disabling polling
        safetyMode: false           // Whether we're currently in safety mode
    };
    
    // State tracking
    let lastMemoryUsage = 0;
    let consecutiveSlowFrames = 0;
    let pollingErrors = 0;
    let originalFetch = window.fetch;
    let originalSetInterval = window.setInterval;
    let originalSetTimeout = window.setTimeout;
    let intervals = [];
    let timeouts = [];
    
    // ========================
    // Memory usage monitoring
    // ========================
    
    // Check if we can monitor memory
    const canCheckMemory = typeof performance !== 'undefined' && 
                         typeof performance.memory !== 'undefined';
    
    // Monitor memory usage
    function checkMemoryUsage() {
        if (!canCheckMemory) return;
        
        try {
            const currentMemory = performance.memory.usedJSHeapSize / (1024 * 1024); // MB
            
            // First run, just set the baseline
            if (lastMemoryUsage === 0) {
                lastMemoryUsage = currentMemory;
                return;
            }
            
            // Check for significant memory increase
            const memoryDiff = currentMemory - lastMemoryUsage;
            
            if (memoryDiff > config.memoryThreshold) {
                console.warn(`Memory usage increased by ${memoryDiff.toFixed(2)}MB. Taking action.`);
                enableSafetyMode();
            }
            
            lastMemoryUsage = currentMemory;
        } catch (e) {
            console.error('Error checking memory:', e);
        }
    }
    
    // ========================
    // Frame rate monitoring
    // ========================
    
    // Monitor frame rate using requestAnimationFrame
    let lastFrameTime = 0;
    
    function monitorFrameRate(timestamp) {
        if (lastFrameTime === 0) {
            lastFrameTime = timestamp;
            requestAnimationFrame(monitorFrameRate);
            return;
        }
        
        const frameTime = timestamp - lastFrameTime;
        lastFrameTime = timestamp;
        
        // Check if frame is slow (less than 30fps means >33ms per frame)
        if (frameTime > 33) {
            consecutiveSlowFrames++;
            if (consecutiveSlowFrames >= config.maxConsecutiveSlowFrames) {
                console.warn(`Detected ${consecutiveSlowFrames} consecutive slow frames. Taking action.`);
                enableSafetyMode();
                consecutiveSlowFrames = 0;
            }
        } else {
            consecutiveSlowFrames = 0;
        }
        
        requestAnimationFrame(monitorFrameRate);
    }
    
    // ========================
    // Network request monitoring
    // ========================
    
    // Intercept fetch to monitor for errors
    function monitorNetworkRequests() {
        window.fetch = function(...args) {
            const url = args[0].toString();
            
            // Only monitor messaging-related requests
            if (url.includes('message') || url.includes('chat')) {
                return originalFetch.apply(this, args)
                    .then(response => {
                        if (!response.ok && response.status >= 400) {
                            pollingErrors++;
                            if (pollingErrors >= config.maxPollingErrors) {
                                console.warn('Too many network errors. Enabling safety mode.');
                                enableSafetyMode();
                            }
                        } else {
                            // Reset on success
                            pollingErrors = 0;
                        }
                        return response;
                    })
                    .catch(error => {
                        pollingErrors++;
                        console.error('Fetch error:', error);
                        if (pollingErrors >= config.maxPollingErrors) {
                            enableSafetyMode();
                        }
                        throw error;
                    });
            }
            
            // Pass through other requests
            return originalFetch.apply(this, args);
        };
    }
    
    // ========================
    // Timer monitoring
    // ========================
    
    // Monitor and control setInterval
    function monitorIntervals() {
        window.setInterval = function(callback, delay, ...args) {
            // Add a try-catch wrapper
            const safeCallback = function() {
                try {
                    callback.apply(this, args);
                } catch (e) {
                    console.error('Error in interval callback:', e);
                    
                    // Clear the interval if it errors
                    if (intervalId) {
                        clearInterval(intervalId);
                        const index = intervals.indexOf(intervalId);
                        if (index > -1) {
                            intervals.splice(index, 1);
                        }
                    }
                }
            };
            
            // Create the interval and track it
            const intervalId = originalSetInterval.call(this, safeCallback, 
                                                      Math.max(delay, 1000), // Enforce minimum delay
                                                      ...args);
            intervals.push(intervalId);
            return intervalId;
        };
    }
    
    // Monitor setTimeout to catch potential issues
    function monitorTimeouts() {
        window.setTimeout = function(callback, delay, ...args) {
            // Enforce a minimum delay
            const actualDelay = Math.max(delay, 50);
            
            // Add a try-catch wrapper
            const safeCallback = function() {
                try {
                    callback.apply(this, args);
                } catch (e) {
                    console.error('Error in timeout callback:', e);
                }
                
                // Remove from tracking
                const index = timeouts.indexOf(timeoutId);
                if (index > -1) {
                    timeouts.splice(index, 1);
                }
            };
            
            // Create and track the timeout
            const timeoutId = originalSetTimeout.call(this, safeCallback, actualDelay, ...args);
            timeouts.push(timeoutId);
            return timeoutId;
        };
    }
    
    // ========================
    // Safety mode
    // ========================
    
    // Enable safety mode when issues are detected
    function enableSafetyMode() {
        if (config.safetyMode) return; // Already in safety mode
        
        console.warn('Enabling messaging safety mode');
        config.safetyMode = true;
        
        // Show a notification to the user
        showSafetyNotification();
        
        // Clear all intervals and timeouts
        intervals.forEach(id => clearInterval(id));
        timeouts.forEach(id => clearTimeout(id));
        intervals = [];
        timeouts = [];
        
        // Disable automatic reload
        const reloadButtons = document.querySelectorAll('[data-action="reload"]');
        reloadButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.reload();
            });
        });
        
        // Add a manual refresh button
        addRefreshButton();
          // Create a beacon to report the crash
        if (navigator.sendBeacon) {
            const data = new FormData();
            data.append('event', 'messaging_crash_prevention');
            data.append('url', window.location.href);
            data.append('timestamp', new Date().toISOString());
            data.append('memoryUsage', lastMemoryUsage);
            data.append('pollingErrors', pollingErrors);
            navigator.sendBeacon('/client/telemetry/', data);
        }
        
        // Also log the issue to the console with additional debugging info
        console.warn('Messaging safety mode details:', {
            memoryUsage: lastMemoryUsage + 'MB',
            pollingErrors,
            consecutiveSlowFrames,
            url: window.location.href,
            timestamp: new Date().toISOString()
        });
    }
    
    // Show a notification to the user
    function showSafetyNotification() {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'safety-notification';
        notification.innerHTML = `
            <div class="safety-message">
                <strong>Problème détecté</strong>
                <p>Un problème a été détecté dans la messagerie. Les mises à jour automatiques ont été désactivées pour éviter tout plantage.</p>
                <button data-action="reload" class="refresh-button">Actualiser manuellement</button>
            </div>
        `;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #fff8e1;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            z-index: 9999;
            max-width: 300px;
            font-size: 14px;
        `;
        
        // Style the button
        const buttonStyle = `
            background-color: #ffc107;
            color: #000;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
            font-weight: bold;
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Style the button after it's in the DOM
        notification.querySelector('.refresh-button').style.cssText = buttonStyle;
        
        // Add click handler for the reload button
        notification.querySelector('[data-action="reload"]').addEventListener('click', function(e) {
            e.preventDefault();
            window.location.reload();
        });
    }
    
    // Add a refresh button at the bottom of the messages
    function addRefreshButton() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const refreshButton = document.createElement('div');
        refreshButton.className = 'refresh-messages-button';
        refreshButton.innerHTML = `
            <button data-action="reload">
                <i class="bi bi-arrow-clockwise"></i> Actualiser les messages
            </button>
        `;
        
        // Style the button
        refreshButton.style.cssText = `
            text-align: center;
            padding: 15px 0;
            margin-top: 10px;
        `;
        
        refreshButton.querySelector('button').style.cssText = `
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            color: #495057;
        `;
        
        // Add to messages
        chatMessages.appendChild(refreshButton);
        
        // Add click handler
        refreshButton.querySelector('button').addEventListener('click', function(e) {
            e.preventDefault();
            window.location.reload();
        });
    }
    
    // ========================
    // Initialization
    // ========================
    
    function init() {
        // Only run on messaging pages
        if (!window.location.pathname.includes('message')) return;
        
        // Monitor memory usage if available
        if (canCheckMemory) {
            setInterval(checkMemoryUsage, config.memoryCheckInterval);
        }
        
        // Monitor frame rate
        requestAnimationFrame(monitorFrameRate);
        
        // Monitor network
        monitorNetworkRequests();
        
        // Monitor timers
        monitorIntervals();
        monitorTimeouts();
        
        console.log('Message anti-crash protection initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose for debugging
    window.messageAntiCrash = {
        config: config,
        enableSafetyMode: enableSafetyMode
    };
})();
