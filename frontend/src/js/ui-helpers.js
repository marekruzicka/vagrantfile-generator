// UI helper functions and utilities
const VagrantUIHelpers = {
    // Validation
    validateProjectForm(app) {
        app.validationErrors = {};
        
        if (!app.newProject.name.trim()) {
            app.validationErrors.projectName = 'Project name is required';
        } else if (app.newProject.name.length < 3) {
            app.validationErrors.projectName = 'Project name must be at least 3 characters';
        }
        
        return Object.keys(app.validationErrors).length === 0;
    },

    validateVMForm(app, vmData = null) {
        app.validationErrors = {};
        const vm = vmData || app.newVM;
        
        if (!vm.name.trim()) {
            app.validationErrors.name = 'VM name is required';
        } else if (!/^[a-zA-Z0-9-_]+$/.test(vm.name)) {
            app.validationErrors.name = 'VM name can only contain letters, numbers, hyphens, and underscores';
        }
        
        if (!vm.box) {
            app.validationErrors.box = 'Box selection is required';
        }
        
        if (vm.memory < app.config.minMemoryMB) {
            app.validationErrors.memory = `Memory must be at least ${app.config.minMemoryMB} MB`;
        } else if (vm.memory > app.config.maxMemoryMB) {
            app.validationErrors.memory = `Memory cannot exceed ${app.config.maxMemoryMB} MB (${app.config.maxMemoryMB / 1024} GB)`;
        }
        
        if (vm.cpus < 1) {
            app.validationErrors.cpus = 'Must have at least 1 CPU';
        } else if (vm.cpus > app.config.maxCpus) {
            app.validationErrors.cpus = `Cannot exceed ${app.config.maxCpus} CPUs`;
        }
        
        return Object.keys(app.validationErrors).length === 0;
    },

    // Array Management
    addForwardedPort(app) {
        app.newVM.forwarded_ports.push({ guest: '', host: '', protocol: 'tcp' });
    },
    
    removeForwardedPort(app, index) {
        app.newVM.forwarded_ports.splice(index, 1);
    },
    
    addSyncedFolder(app) {
        app.newVM.synced_folders.push({ host_path: '', guest_path: '', type: 'nfs' });
    },
    
    removeSyncedFolder(app, index) {
        app.newVM.synced_folders.splice(index, 1);
    },
    
    addPrivateNetwork(app) {
        app.newVM.private_networks.push({ ip: '', netmask: '255.255.255.0' });
    },
    
    removePrivateNetwork(app, index) {
        app.newVM.private_networks.splice(index, 1);
    },

    // Modals
    openCreateProjectModal(app) {
        app.newProject = { name: '', description: '' };
        app.validationErrors = {};
        app.showCreateProjectModal = true;
    },
    
    openCreateVMModal(app) {
        app.newVM = {
            name: '',
            box: 'generic/debian12',
            memory: 1024,
            cpus: 1,
            hostname: '',
            count: 1,
            labels: [],
            forwarded_ports: [],
            synced_folders: [],
            private_networks: []
        };
        app.validationErrors = {};
        app.activeFormSection = 'general';
        app.showCreateVMModal = true;
    },
    
    openEditVMModal(app, vm) {
        app.editingVM = { ...vm, originalName: vm.name };
        // Ensure labels is always an array
        if (!app.editingVM.labels || !Array.isArray(app.editingVM.labels)) {
            app.editingVM.labels = [];
        }
        app.validationErrors = {};
        app.activeFormSection = 'general';
        app.showEditVMModal = true;
    },
    
    openDeleteConfirmModal(app, target, type) {
        app.deleteTarget = { ...target, type };
        app.showDeleteConfirmModal = true;
    },
    
    closeDeleteConfirmModal(app) {
        app.showDeleteConfirmModal = false;
        app.deleteTarget = null;
    },

    async confirmDelete(app) {
        if (!app.deleteTarget) return;
        
        app.setLoading(true);
        try {
            if (app.deleteTarget.type === 'project') {
                await app.deleteProject(app.deleteTarget.id);
                app.setSuccess(`Project "${app.deleteTarget.name}" deleted successfully`);
            } else if (app.deleteTarget.type === 'vm') {
                await app.deleteVM(app.deleteTarget.name);
                app.setSuccess(`VM "${app.deleteTarget.name}" deleted successfully`);
            }
            VagrantUIHelpers.closeDeleteConfirmModal(app);
        } catch (error) {
            app.setError(`Failed to delete ${app.deleteTarget.type}: ${error.message}`);
        } finally {
            app.setLoading(false);
        }
    },

    // Helper methods
    syncProjectInList(app) {
        // Sync currentProject VM count back to projects list
        if (app.currentProject) {
            const projectIndex = app.projects.findIndex(p => p.id === app.currentProject.id);
            if (projectIndex !== -1) {
                app.projects[projectIndex].vm_count = app.currentProject.vms.length;
            }
        }
    },
    
    getDeleteMessage(app) {
        if (!app.deleteTarget) return '';
        
        if (app.deleteTarget.type === 'project') {
            const vmCount = app.deleteTarget.vm_count || 0;
            const vmText = vmCount === 1 ? '1 VM' : `${vmCount} VMs`;
            return `Are you sure you want to delete the project "${app.deleteTarget.name}"? This will also delete ${vmText} and cannot be undone.`;
        } else if (app.deleteTarget.type === 'vm') {
            return `Are you sure you want to delete the VM "${app.deleteTarget.name}"? This action cannot be undone.`;
        }
        return 'Are you sure you want to delete this item?';
    },

    // Navigation
    showProjects(app) {
        app.currentView = 'projects';
        app.currentProject = null;
        app.error = null;
        app.successMessage = null;
    },

    showSettings(app) {
        app.currentView = 'settings';
        app.currentProject = null;
        app.error = null;
        app.successMessage = null;
    },

    // Form helpers
    resetNewProject(app) {
        app.newProject = { name: '', description: '' };
    },
    
    resetNewVM(app) {
        app.newVM = {
            name: '',
            box: 'generic/debian12',
            memory: 1024,
            cpus: 1,
            hostname: '',
            count: 1,
            labels: [],
            forwarded_ports: [],
            synced_folders: [],
            private_networks: []
        };
    },

    // UI helpers
    setLoading(app, loading) { 
        app.isLoading = loading; 
    },
    
    setError(app, error) {
        app.error = error;
        app.successMessage = null;
        setTimeout(() => app.error = null, 5000);
    },
    
    setSuccess(app, message) {
        app.successMessage = message;
        app.error = null;
        setTimeout(() => { app.error = null; app.successMessage = null; }, 3000);
    },
    
    clearError(app) { 
        app.error = null; 
    },
    
    clearMessages(app) { 
        app.error = null; 
        app.successMessage = null; 
    },
    
    formatDate(dateString) { 
        return new Date(dateString).toLocaleDateString(); 
    },
    
    copyToClipboard(app, text) {
        navigator.clipboard.writeText(text).then(() => {
            VagrantUIHelpers.setSuccess(app, 'Copied to clipboard!');
        }).catch(err => {
            VagrantUIHelpers.setError(app, 'Failed to copy to clipboard');
        });
    },

    // Form sections
    setActiveFormSection(app, section) { 
        app.activeFormSection = section; 
    },
    
    isFormSectionActive(app, section) { 
        return app.activeFormSection === section; 
    }
};

// Make helper functions available globally
window.VagrantUIHelpers = VagrantUIHelpers;