// VagrantAPI class (keeping original functionality)
class VagrantAPI {
    constructor(baseURL = null) {
        // Auto-detect the correct API URL based on configuration
        if (!baseURL) {
            // First try environment variable (for production/explicit configuration)
            if (typeof __API_URL__ !== 'undefined' && __API_URL__ && __API_URL__.trim() !== '') {
                baseURL = __API_URL__;
                if (!baseURL.endsWith('/api')) {
                    baseURL += '/api';
                }
            } else {
                // Default to localhost for development
                baseURL = 'http://localhost:8000/api';
            }
        }
        this.baseURL = baseURL;
        this.config = {};
        
        console.log(`VagrantAPI initialized with baseURL: ${this.baseURL}`);
    }

    setConfig(config) {
        this.config = config;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        // Add configuration headers
        if (this.config.allowPublicIPsInPrivateNetworks) {
            config.headers['X-Allow-Public-IPs'] = 'true';
        }

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (response.status === 204 || response.headers.get('content-length') === '0') {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return {};
            }
            
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                throw new Error('Invalid JSON response');
            }

            if (!response.ok) {
                // Handle validation errors properly
                if (data.detail && Array.isArray(data.detail)) {
                    const validationErrors = data.detail.map(err => err.msg).join(', ');
                    throw new Error(validationErrors);
                } else {
                    throw new Error(data.detail || data.error || `HTTP ${response.status}`);
                }
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    async getProjects(status = null) { 
        const endpoint = status ? `/projects?status=${status}` : '/projects';
        return this.request(endpoint); 
    }
    async getProject(id) { return this.request(`/projects/${id}`); }
    async createProject(data) { return this.request('/projects', { method: 'POST', body: data }); }
    async deleteProject(id) { return this.request(`/projects/${id}`, { method: 'DELETE' }); }
    async updateProjectDeploymentStatus(id, status) { 
        return this.request(`/projects/${id}/deployment-status?status=${status}`, { 
            method: 'PATCH'
        }); 
    }
    async getProjectStats() { return this.request('/projects/stats'); }
    async createVM(projectId, data) { return this.request(`/projects/${projectId}/vms`, { method: 'POST', body: data }); }
    async updateVM(projectId, vmName, data) { return this.request(`/projects/${projectId}/vms/${vmName}`, { method: 'PUT', body: data }); }
    async deleteVM(projectId, vmName) { return this.request(`/projects/${projectId}/vms/${vmName}`, { method: 'DELETE' }); }
    async generateVagrantfile(projectId) { return this.request(`/projects/${projectId}/generate`, { method: 'POST' }); }
    async getBoxes() { return this.request('/vagrant/boxes'); }
    
    // Box management methods
    async getBoxesList() { return this.request('/boxes'); }
    async getBox(id) { return this.request(`/boxes/${id}`); }
    async createBox(boxData) { return this.request('/boxes', { method: 'POST', body: boxData }); }
    async updateBox(id, boxData) { return this.request(`/boxes/${id}`, { method: 'PUT', body: boxData }); }
    async deleteBox(id) { return this.request(`/boxes/${id}`, { method: 'DELETE' }); }

    // Network interface management methods
    async addNetworkInterface(projectId, vmName, interfaceData) { 
        return this.request(`/projects/${projectId}/vms/${vmName}/network-interfaces`, { 
            method: 'POST', 
            body: interfaceData 
        }); 
    }
    async updateNetworkInterface(projectId, vmName, interfaceId, interfaceData) { 
        return this.request(`/projects/${projectId}/vms/${vmName}/network-interfaces/${interfaceId}`, { 
            method: 'PUT', 
            body: interfaceData 
        }); 
    }
    async deleteNetworkInterface(projectId, vmName, interfaceId) { 
        return this.request(`/projects/${projectId}/vms/${vmName}/network-interfaces/${interfaceId}`, { 
            method: 'DELETE' 
        }); 
    }

    async downloadVagrantfile(projectId) {
        const response = await fetch(`${this.baseURL}/projects/${projectId}/download`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Vagrantfile';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// Global API instance
const api = new VagrantAPI();