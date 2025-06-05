/**
 * Quick Messaging Interface Validation
 * Run this in browser console on any messaging page
 */

function quickMessagingValidation() {
    console.log('🔍 Quick Messaging Interface Validation');
    console.log('=====================================');
    
    // Check for message elements
    const messages = document.querySelectorAll('.message, .message-content, [class*="message"]');
    console.log(`📨 Found ${messages.length} message-related elements`);
    
    // Check CSS fixes
    const messageContents = document.querySelectorAll('.message-content');
    let fixedCount = 0;
    
    messageContents.forEach((element, index) => {
        const styles = window.getComputedStyle(element);
        const wordBreak = styles.wordBreak;
        const whiteSpace = styles.whiteSpace;
        const overflowWrap = styles.overflowWrap;
        
        console.log(`📝 Message Content ${index + 1}:`);
        console.log(`   word-break: ${wordBreak}`);
        console.log(`   white-space: ${whiteSpace}`);
        console.log(`   overflow-wrap: ${overflowWrap}`);
        
        if (wordBreak === 'normal' && whiteSpace === 'normal') {
            fixedCount++;
            console.log(`   ✅ FIXED - Normal text flow`);
        } else {
            console.log(`   ❌ ISSUE - May cause vertical stacking`);
        }
    });
    
    // Check if JavaScript fix is loaded
    const jsFixLoaded = typeof window.fixMessagingLayout === 'function';
    console.log(`🔧 JavaScript Fix: ${jsFixLoaded ? '✅ LOADED' : '❌ NOT LOADED'}`);
    
    // Check for outgoing message styling
    const outgoingMessages = document.querySelectorAll('.message-outgoing, .sent');
    console.log(`📤 Outgoing messages: ${outgoingMessages.length}`);
    
    outgoingMessages.forEach((element, index) => {
        const styles = window.getComputedStyle(element);
        const backgroundColor = styles.backgroundColor;
        const color = styles.color;
        
        console.log(`📤 Outgoing Message ${index + 1}:`);
        console.log(`   background: ${backgroundColor}`);
        console.log(`   color: ${color}`);
        
        // Check for proper contrast (light green background, dark text)
        if (backgroundColor.includes('220, 248, 198') || backgroundColor.includes('#DCF8C6')) {
            console.log(`   ✅ PROPER BACKGROUND - Light green`);
        } else {
            console.log(`   ⚠️ BACKGROUND - ${backgroundColor}`);
        }
        
        if (color.includes('31, 31, 31') || color.includes('#1f1f1f') || color === 'rgb(31, 31, 31)') {
            console.log(`   ✅ PROPER TEXT COLOR - Dark text`);
        } else {
            console.log(`   ⚠️ TEXT COLOR - ${color}`);
        }
    });
    
    // Summary
    console.log('');
    console.log('📊 VALIDATION SUMMARY');
    console.log('====================');
    console.log(`Message elements found: ${messages.length}`);
    console.log(`Message content elements: ${messageContents.length}`);
    console.log(`CSS fixes applied: ${fixedCount}/${messageContents.length}`);
    console.log(`JavaScript fix loaded: ${jsFixLoaded ? 'Yes' : 'No'}`);
    console.log(`Outgoing messages styled: ${outgoingMessages.length}`);
    
    if (fixedCount === messageContents.length && jsFixLoaded) {
        console.log('🎉 ALL CHECKS PASSED - Messaging fix is working!');
    } else {
        console.log('⚠️ Some issues detected - manual inspection recommended');
        
        if (!jsFixLoaded) {
            console.log('💡 Try running: window.fixMessagingLayout() if available');
        }
    }
    
    return {
        messageElements: messages.length,
        messageContentElements: messageContents.length,
        cssFixesApplied: fixedCount,
        jsFixLoaded: jsFixLoaded,
        outgoingMessages: outgoingMessages.length,
        allGood: fixedCount === messageContents.length && jsFixLoaded
    };
}

// Auto-run validation
quickMessagingValidation();
