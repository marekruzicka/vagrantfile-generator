// Main application initialization
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Main.js: DOMContentLoaded event fired');
    
    // Initialize Alpine.js when the DOM is ready
    if (typeof Alpine !== 'undefined') {
        console.log('Main.js: Alpine.js is available');
        
        // Check if footerComponent function exists
        if (typeof footerComponent === 'function') {
            console.log('Main.js: footerComponent function is available');
        } else {
            console.error('Main.js: footerComponent function is NOT available');
        }
        
        // Register the main app component
        Alpine.data('vagrantApp', vagrantApp);
        console.log('Main.js: Registered vagrantApp component');
        
        // footerComponent is already available globally from footer-component.js
        // No need to re-register it
        
        // Wait for HTML partials to load before starting Alpine.js
        if (window.htmlLoader) {
            console.log('Main.js: Waiting for HTML partials to load before starting Alpine.js...');
            await window.htmlLoader.loadPartials();
            console.log('Main.js: HTML partials loaded, starting Alpine.js...');
        } else {
            console.log('Main.js: No htmlLoader found, starting Alpine.js immediately...');
        }
        
        // Start Alpine.js (using deferred loading)
        if (window.startAlpine) {
            console.log('Main.js: Starting Alpine.js via deferred loader');
            window.startAlpine();
        } else {
            console.log('Main.js: Starting Alpine.js directly');
            Alpine.start();
        }
        console.log('Main.js: Alpine.js startup completed');
    } else {
        console.error('Alpine.js is not loaded. Please ensure Alpine.js is included before this script.');
    }
});