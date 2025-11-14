/**
 * Authentication utilities for frontend.
 * 
 * Handles authentication state, token validation, and login redirects.
 */

class AuthManager {
    constructor() {
        this.token = null;
        this.user = null;
    }

    /**
     * Check if user is authenticated.
     * @returns {Promise<Object|null>} User profile if authenticated, null otherwise
     */
    async checkAuth() {
        // Get token from localStorage
        this.token = localStorage.getItem('auth_token');
        
        if (!this.token) {
            return null;
        }

        // Verify token with backend
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                // Token is invalid or expired
                this.clearAuth();
                return null;
            }

            this.user = await response.json();
            return this.user;
        } catch (error) {
            console.error('Error checking authentication:', error);
            this.clearAuth();
            return null;
        }
    }

    /**
     * Redirect to login page if in public mode and not authenticated.
     */
    async redirectToLogin() {
        // Check deployment mode first
        if (!window.deploymentManager) {
            console.error('DeploymentManager not initialized');
            return;
        }

        const isPublic = await window.deploymentManager.isPublicMode();
        
        // Only redirect if in public mode
        if (!isPublic) {
            console.log('Self-hosted mode - no authentication required');
            return;
        }

        // Check if authenticated
        const user = await this.checkAuth();
        
        if (!user) {
            // Not authenticated in public mode - redirect to login
            console.log('Not authenticated - redirecting to login');
            window.location.href = '/views/login/login.html';
        } else {
            console.log('Authenticated as:', user.email);
        }
    }

    /**
     * Get current authentication token.
     * @returns {string|null} JWT token or null
     */
    getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('auth_token');
        }
        return this.token;
    }

    /**
     * Get current user profile.
     * @returns {Object|null} User profile or null
     */
    getUser() {
        if (!this.user) {
            const userData = localStorage.getItem('user_profile');
            if (userData) {
                try {
                    this.user = JSON.parse(userData);
                } catch (e) {
                    console.error('Error parsing user profile:', e);
                    this.user = null;
                }
            }
        }
        return this.user;
    }

    /**
     * Logout current user.
     */
    async logout() {
        // Call logout endpoint (optional, for logging)
        if (this.token) {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });
            } catch (error) {
                console.error('Error calling logout endpoint:', error);
            }
        }

        // Clear local auth state
        this.clearAuth();

        // Redirect to login
        window.location.href = '/views/login/login.html';
    }

    /**
     * Clear authentication state.
     */
    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_profile');
    }

    /**
     * Check if user is authenticated (synchronous, uses cached data).
     * @returns {boolean} True if authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    }
}

// Global auth manager instance
const authManager = new AuthManager();

// Export for use in other modules
window.authManager = authManager;
