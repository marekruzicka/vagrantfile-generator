/**
 * Deployment mode utilities for frontend.
 * 
 * Fetches and caches deployment mode from backend API.
 */

class DeploymentManager {
    constructor() {
        this._mode = null;
        this._fetched = false;
    }

    /**
     * Fetch deployment mode from backend.
     * @returns {Promise<string>} Deployment mode ('self-hosted' or 'public')
     */
    async fetchDeploymentMode() {
        if (this._fetched) {
            return this._mode;
        }

        try {
            const response = await fetch('/api/config/deployment-mode');
            if (!response.ok) {
                throw new Error(`Failed to fetch deployment mode: ${response.statusText}`);
            }

            const data = await response.json();
            this._mode = data.mode;
            this._fetched = true;

            console.log(`Deployment mode: ${this._mode}`);
            return this._mode;
        } catch (error) {
            console.error('Error fetching deployment mode:', error);
            // Default to self-hosted on error for backward compatibility
            this._mode = 'self-hosted';
            this._fetched = true;
            return this._mode;
        }
    }

    /**
     * Check if app is running in public mode.
     * @returns {Promise<boolean>} True if public mode
     */
    async isPublicMode() {
        const mode = await this.fetchDeploymentMode();
        return mode === 'public';
    }

    /**
     * Check if app is running in self-hosted mode.
     * @returns {Promise<boolean>} True if self-hosted mode
     */
    async isSelfHostedMode() {
        const mode = await this.fetchDeploymentMode();
        return mode === 'self-hosted';
    }

    /**
     * Get cached deployment mode (returns null if not fetched yet).
     * @returns {string|null} Deployment mode or null
     */
    getCachedMode() {
        return this._mode;
    }

    /**
     * Clear cached deployment mode (for testing).
     */
    clearCache() {
        this._mode = null;
        this._fetched = false;
    }
}

// Global deployment manager instance
const deploymentManager = new DeploymentManager();

// Export for use in other modules
window.deploymentManager = deploymentManager;
