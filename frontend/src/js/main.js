// Main application initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Alpine.js when the DOM is ready
    if (typeof Alpine !== 'undefined') {
        // Register the main app component
        Alpine.data('vagrantApp', vagrantApp);
        
        // Start Alpine.js
        Alpine.start();
    } else {
        console.error('Alpine.js is not loaded. Please ensure Alpine.js is included before this script.');
    }
});