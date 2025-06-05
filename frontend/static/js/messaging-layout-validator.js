/**
 * Messaging Layout Fix Validator
 * This script can be run in the browser console to validate the fix
 */

function validateMessagingLayoutFix() {
    console.log('🔍 Validating messaging layout fix...');
    
    const results = {
        cssPropertiesFixed: false,
        messageContentElements: 0,
        problematicElements: 0,
        messageWidthOk: false,
        jsFixLoaded: false
    };
    
    // Check if message content elements exist
    const messageContents = document.querySelectorAll('.message-content');
    results.messageContentElements = messageContents.length;
    
    if (messageContents.length === 0) {
        console.log('ℹ️ No message content elements found on this page');
        return results;
    }
    
    // Check CSS properties on message content elements
    let fixedElements = 0;
    let problematicElements = 0;
    
    messageContents.forEach(element => {
        const styles = window.getComputedStyle(element);
        const wordBreak = styles.getPropertyValue('word-break');
        const whiteSpace = styles.getPropertyValue('white-space');
        const overflowWrap = styles.getPropertyValue('overflow-wrap');
        
        console.log(`Element styles - word-break: ${wordBreak}, white-space: ${whiteSpace}, overflow-wrap: ${overflowWrap}`);
        
        if (wordBreak === 'normal' && whiteSpace === 'normal' && overflowWrap === 'normal') {
            fixedElements++;
        } else if (wordBreak === 'break-word' || whiteSpace === 'pre-wrap') {
            problematicElements++;
            console.warn('⚠️ Found problematic element with vertical text stacking styles:', element);
        }
    });
    
    results.cssPropertiesFixed = fixedElements === messageContents.length;
    results.problematicElements = problematicElements;
    
    // Check message bubble widths
    const messages = document.querySelectorAll('.message');
    if (messages.length > 0) {
        const firstMessage = messages[0];
        const styles = window.getComputedStyle(firstMessage);
        const maxWidth = styles.getPropertyValue('max-width');
        const minWidth = styles.getPropertyValue('min-width');
        
        results.messageWidthOk = maxWidth !== 'none' && minWidth !== '0px';
        console.log(`Message bubble sizing - max-width: ${maxWidth}, min-width: ${minWidth}`);
    }
    
    // Check if JavaScript fix is loaded
    results.jsFixLoaded = typeof window.fixMessagingLayout === 'function';
    
    // Print results
    console.log('\n📊 Validation Results:');
    console.log(`✅ Message content elements found: ${results.messageContentElements}`);
    console.log(`${results.cssPropertiesFixed ? '✅' : '❌'} CSS properties fixed: ${results.cssPropertiesFixed}`);
    console.log(`${results.problematicElements === 0 ? '✅' : '❌'} Problematic elements: ${results.problematicElements}`);
    console.log(`${results.messageWidthOk ? '✅' : '❌'} Message bubble sizing: ${results.messageWidthOk}`);
    console.log(`${results.jsFixLoaded ? '✅' : '❌'} JavaScript fix loaded: ${results.jsFixLoaded}`);
    
    const allGood = results.cssPropertiesFixed && 
                   results.problematicElements === 0 && 
                   results.messageWidthOk && 
                   results.jsFixLoaded;
    
    if (allGood) {
        console.log('\n🎉 All validations passed! Messaging layout fix is working correctly.');
    } else {
        console.log('\n⚠️ Some validations failed. The fix may need adjustment.');
        
        if (results.jsFixLoaded) {
            console.log('💡 Try running: window.fixMessagingLayout()');
        }
    }
    
    return results;
}

// Auto-run validation if this script is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', validateMessagingLayoutFix);
} else {
    validateMessagingLayoutFix();
}

// Export for manual usage
window.validateMessagingLayoutFix = validateMessagingLayoutFix;
