// Register Alpine components BEFORE Alpine initializes
document.addEventListener('alpine:init', () => {
    console.log('Main.js: alpine:init fired - registering components');
    
    // Register the main app component
    if (typeof vagrantApp === 'function') {
        Alpine.data('vagrantApp', vagrantApp);
        console.log('Main.js: Registered vagrantApp component');
    } else {
        console.error('Main.js: vagrantApp function is NOT available');
    }
    
    // footerComponent is already available globally from footer-component.js
    if (typeof footerComponent === 'function') {
        console.log('Main.js: footerComponent is available');
    } else {
        console.error('Main.js: footerComponent is NOT available');
    }
});

// Load HTML partials after DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Main.js: DOMContentLoaded fired');
    
    // Wait for HTML partials to load
    if (window.htmlLoader) {
        console.log('Main.js: Loading HTML partials...');
        await window.htmlLoader.loadPartials();
        console.log('Main.js: HTML partials loaded');
    }
    
    console.log('Main.js: Initialization complete');
});