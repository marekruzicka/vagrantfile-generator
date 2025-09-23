// API Service for Vagrantfile GUI Generator
class VagrantAPI {
    constructor(baseURL = 'http://localhost:8000/api') {
        this.baseURL = baseURL;
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

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Project endpoints
    async getProjects() {
        return this.request('/projects');
    }

    async getProject(id) {
        return this.request(`/projects/${id}`);
    }

    async createProject(projectData) {
        return this.request('/projects', {
            method: 'POST',
            body: projectData,
        });
    }

    async updateProject(id, projectData) {
        return this.request(`/projects/${id}`, {
            method: 'PUT',
            body: projectData,
        });
    }

    async deleteProject(id) {
        return this.request(`/projects/${id}`, {
            method: 'DELETE',
        });
    }

    // VM endpoints
    async addVM(projectId, vmData) {
        return this.request(`/projects/${projectId}/vms`, {
            method: 'POST',
            body: vmData,
        });
    }

    async updateVM(projectId, vmName, vmData) {
        return this.request(`/projects/${projectId}/vms/${vmName}`, {
            method: 'PUT',
            body: vmData,
        });
    }

    async deleteVM(projectId, vmName) {
        return this.request(`/projects/${projectId}/vms/${vmName}`, {
            method: 'DELETE',
        });
    }

    // Network interface endpoints
    async addNetworkInterface(projectId, vmName, interfaceData) {
        return this.request(`/projects/${projectId}/vms/${vmName}/interfaces`, {
            method: 'POST',
            body: interfaceData,
        });
    }

    async updateNetworkInterface(projectId, vmName, interfaceId, interfaceData) {
        return this.request(`/projects/${projectId}/vms/${vmName}/interfaces/${interfaceId}`, {
            method: 'PUT',
            body: interfaceData,
        });
    }

    async deleteNetworkInterface(projectId, vmName, interfaceId) {
        return this.request(`/projects/${projectId}/vms/${vmName}/interfaces/${interfaceId}`, {
            method: 'DELETE',
        });
    }

    // Generation endpoints
    async generateVagrantfile(projectId) {
        return this.request(`/projects/${projectId}/generate`, {
            method: 'POST',
        });
    }

    // Helper endpoints
    async getVagrantBoxes() {
        return this.request('/vagrant/boxes');
    }

    async getVagrantPlugins() {
        return this.request('/vagrant/plugins');
    }
}

// Global API instance
window.api = new VagrantAPI();