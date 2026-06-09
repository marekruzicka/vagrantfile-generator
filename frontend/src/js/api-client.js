/**
 * API client utility with authentication support.
 * 
 * Automatically adds Authorization headers and handles 401 responses.
 */

class ApiClient {
    constructor() {
        this.baseUrl = '';
    }

    /**
     * Get headers for API request.
     * @param {Object} customHeaders - Additional headers to include
     * @returns {Object} Headers object
     */
    getHeaders(customHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...customHeaders
        };

        // Add authorization header if authenticated
        const token = window.authManager?.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    /**
     * Handle API response.
     * @param {Response} response - Fetch response
     * @returns {Promise<any>} Parsed response data
     */
    async handleResponse(response) {
        // Handle 401 Unauthorized
        if (response.status === 401) {
            console.log('401 Unauthorized - clearing auth and redirecting to login');
            
            // Clear auth state
            if (window.authManager) {
                window.authManager.clearAuth();
            }

            // Check if we're in public mode before redirecting
            if (window.deploymentManager) {
                const isPublic = await window.deploymentManager.isPublicMode();
                if (isPublic) {
                    // Redirect to login
                    window.location.href = '/views/login/login.html';
                    throw new Error('Unauthorized - redirecting to login');
                }
            }
        }

        // Handle other errors
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || errorData.message || `HTTP error ${response.status}`;
            throw new Error(errorMessage);
        }

        // Parse successful response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return await response.text();
    }

    /**
     * Make GET request.
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async get(url, options = {}) {
        const response = await fetch(this.baseUrl + url, {
            method: 'GET',
            headers: this.getHeaders(options.headers),
            ...options
        });

        return this.handleResponse(response);
    }

    /**
     * Make POST request.
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async post(url, data = null, options = {}) {
        const response = await fetch(this.baseUrl + url, {
            method: 'POST',
            headers: this.getHeaders(options.headers),
            body: data ? JSON.stringify(data) : null,
            ...options
        });

        return this.handleResponse(response);
    }

    /**
     * Make PUT request.
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async put(url, data = null, options = {}) {
        const response = await fetch(this.baseUrl + url, {
            method: 'PUT',
            headers: this.getHeaders(options.headers),
            body: data ? JSON.stringify(data) : null,
            ...options
        });

        return this.handleResponse(response);
    }

    /**
     * Make PATCH request.
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async patch(url, data = null, options = {}) {
        const response = await fetch(this.baseUrl + url, {
            method: 'PATCH',
            headers: this.getHeaders(options.headers),
            body: data ? JSON.stringify(data) : null,
            ...options
        });

        return this.handleResponse(response);
    }

    /**
     * Make DELETE request.
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async delete(url, options = {}) {
        const response = await fetch(this.baseUrl + url, {
            method: 'DELETE',
            headers: this.getHeaders(options.headers),
            ...options
        });

        return this.handleResponse(response);
    }
}

// Global API client instance
const apiClient = new ApiClient();

// Export for use in other modules
window.apiClient = apiClient;
