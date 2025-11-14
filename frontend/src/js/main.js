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

// Global error handler utility
window.showError = function(message, details = null) {
    console.error('Error:', message, details);
    
    // Show error in UI (could be enhanced with a toast/notification system)
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded shadow-lg z-50 max-w-md';
    errorDiv.setAttribute('role', 'alert');
    errorDiv.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium">${message}</p>
                ${details ? `<p class="text-xs mt-1 text-red-600">${details}</p>` : ''}
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-3 flex-shrink-0">
                <span class="sr-only">Dismiss</span>
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        </div>
    `;
    document.body.appendChild(errorDiv);
    
    // Auto-dismiss after 8 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 8000);
};

// Global fetch error interceptor
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    try {
        const response = await originalFetch.apply(this, args);
        
        // Handle error responses
        if (!response.ok) {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.clone().json();
                
                // Handle structured errors
                if (errorData.status === 'error') {
                    const errorMessage = errorData.error || 'An error occurred';
                    const errorDetails = errorData.details 
                        ? errorData.details.map(d => `${d.field}: ${d.message}`).join(', ')
                        : null;
                    
                    // Don't show error for 401 (handled by auth manager)
                    if (response.status !== 401) {
                        window.showError(errorMessage, errorDetails);
                    }
                }
            }
        }
        
        return response;
    } catch (error) {
        // Network errors or other fetch failures
        console.error('Network error:', error);
        window.showError('Network error. Please check your connection and try again.');
        throw error;
    }
};

// Global unhandled error handler
window.addEventListener('error', function(event) {
    console.error('Unhandled error:', event.error);
    window.showError('An unexpected error occurred. Please refresh the page.');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    window.showError('An unexpected error occurred. Please try again.');
});

// Load HTML partials after DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Main.js: DOMContentLoaded fired');
    
    // Check for token in URL query parameter (from OIDC callback)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
        console.log('Main.js: Token found in URL, storing and cleaning URL');
        localStorage.setItem('auth_token', token);
        
        // Remove token from URL without page reload
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
        
        // Verify token with backend
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const user = await response.json();
                localStorage.setItem('user_profile', JSON.stringify(user));
                console.log('Main.js: OIDC authentication successful for', user.email);
            }
        } catch (error) {
            console.error('Main.js: Failed to verify OIDC token:', error);
        }
    }
    
    if (window.__loadRuntimeConfig && typeof window.__loadRuntimeConfig === 'function') {
        try {
            console.log('Main.js: Loading runtime config...');
            await window.__loadRuntimeConfig();
            console.log('Main.js: Runtime config loaded');
        } catch (error) {
            console.warn('Main.js: Runtime config loader failed', error);
        }
    } else {
        console.log('Main.js: No runtime config loader present; skipping');
    }

    // Initialize deployment manager
    if (!window.deploymentManager) {
        console.log('Main.js: Creating deployment manager instance...');
        window.deploymentManager = new DeploymentManager();
    }

    // Check authentication before loading app
    console.log('Main.js: Checking authentication...');
    await window.authManager.redirectToLogin();
    console.log('Main.js: Authentication check complete');

    // Wait for HTML partials to load
    if (window.htmlLoader) {
        console.log('Main.js: Loading HTML partials...');
        await window.htmlLoader.loadPartials();
        console.log('Main.js: HTML partials loaded');
    }
    
    console.log('Main.js: Initialization complete');
});