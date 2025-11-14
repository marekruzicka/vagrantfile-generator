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