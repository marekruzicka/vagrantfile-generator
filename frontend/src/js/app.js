// Application state and main functionality
function vagrantApp() {
    return {
        // State
        projects: [],
        currentProject: null,
        currentView: 'projects',
        isLoading: false,
        error: null,
        successMessage: null,
        
        // Modals
        showCreateProjectModal: false,
        showCreateVMModal: false,
        showEditVMModal: false,
        showVagrantfileModal: false,
        showDeleteConfirmModal: false,
        deleteTarget: null,
        editingVM: null,
        
        // Forms
        newProject: { name: '', description: '' },
        newVM: {
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
        },
        
        vagrantfileContent: '',
        availableBoxes: [],
        validationErrors: {},
        activeFormSection: 'general',
        
        // Configuration settings
        config: {
            maxCpus: 8,
            maxMemoryMB: 16384,
            minMemoryMB: 512,
            memoryStep: 256
        },
        
        // Box management state
        showBoxModal: false,
        showDeleteBoxConfirmModal: false,
        boxToDelete: null,
        editingBox: null,
        boxForm: {
            name: '',
            description: '',
            provider: 'libvirt',
            version: '',
            url: ''
        },
        
        // VM labeling and selection state
        selectedVMs: [],
        projectLabels: [], // All available labels for current project
        selectedLabels: [], // Labels used for quick filtering
        currentLabelInput: '', // Current label being typed for new VMs
        currentEditLabelInput: '', // Current label being typed for edit VM
        currentBulkLabelInput: '', // Current label being typed for bulk edit
        showBulkEditModal: false,
        showBulkDeleteModal: false,
        showLabelModal: false,
        bulkEditForm: {
            memory: '',
            cpus: '',
            labels: []
        },
        labelForm: {
            name: '',
            color: '#3b82f6'
        },
        
        // Init
        async init() {
            this.loadConfiguration();
            await this.loadProjects();
            await this.loadBoxes();
        },
        
        // Configuration management
        loadConfiguration() {
            try {
                const savedConfig = localStorage.getItem('vagrantfile-generator-config');
                if (savedConfig) {
                    const config = JSON.parse(savedConfig);
                    this.config = { ...this.config, ...config };
                }
            } catch (error) {
                console.error('Failed to load configuration:', error);
            }
        },
        
        saveConfiguration() {
            try {
                localStorage.setItem('vagrantfile-generator-config', JSON.stringify(this.config));
                this.setSuccess('Configuration saved successfully!');
            } catch (error) {
                console.error('Failed to save configuration:', error);
                this.setError('Failed to save configuration');
            }
        },
        
        async loadBoxes() {
            try {
                const result = await api.getBoxesList();
                this.availableBoxes = result || [];
            } catch (error) {
                console.error('Failed to load boxes:', error);
            }
        },
        
        // Box management methods
        openAddBoxModal() {
            this.editingBox = null;
            this.boxForm = {
                name: '',
                description: '',
                provider: 'libvirt',
                version: '',
                url: ''
            };
            this.showBoxModal = true;
        },
        
        openEditBoxModal(box) {
            this.editingBox = box;
            // Fetch full box details including version and url
            this.loadBoxForEdit(box.id);
            this.showBoxModal = true;
        },
        
        async loadBoxForEdit(boxId) {
            try {
                const fullBox = await api.getBox(boxId);
                this.boxForm = {
                    name: fullBox.name || '',
                    description: fullBox.description || '',
                    provider: fullBox.provider || 'libvirt',
                    version: fullBox.version || '',
                    url: fullBox.url || ''
                };
            } catch (error) {
                console.error('Failed to load box details:', error);
                // Fallback to summary data
                this.boxForm = {
                    name: this.editingBox.name || '',
                    description: this.editingBox.description || '',
                    provider: this.editingBox.provider || 'libvirt',
                    version: '',
                    url: ''
                };
            }
        },
        
        closeBoxModal() {
            this.showBoxModal = false;
            this.editingBox = null;
            this.boxForm = {
                name: '',
                description: '',
                provider: 'libvirt',
                version: '',
                url: ''
            };
        },
        
        async saveBox() {
            try {
                if (!this.boxForm.name.trim() || !this.boxForm.description.trim()) {
                    alert('Box name and description are required');
                    return;
                }
                
                const boxData = {
                    name: this.boxForm.name.trim(),
                    description: this.boxForm.description.trim(),
                    provider: this.boxForm.provider,
                    version: this.boxForm.version.trim() || null,
                    url: this.boxForm.url.trim() || null
                };
                
                if (this.editingBox) {
                    await api.updateBox(this.editingBox.id, boxData);
                } else {
                    await api.createBox(boxData);
                }
                
                await this.loadBoxes();
                this.closeBoxModal();
            } catch (error) {
                console.error('Failed to save box:', error);
                alert('Failed to save box: ' + (error.message || 'Unknown error'));
            }
        },
        
        confirmDeleteBox(box) {
            this.boxToDelete = box;
            this.showDeleteBoxConfirmModal = true;
        },
        
        closeDeleteBoxModal() {
            this.showDeleteBoxConfirmModal = false;
            this.boxToDelete = null;
        },
        
        async deleteBox() {
            if (!this.boxToDelete) return;
            
            try {
                await api.deleteBox(this.boxToDelete.id);
                await this.loadBoxes();
                this.closeDeleteBoxModal();
            } catch (error) {
                console.error('Failed to delete box:', error);
                alert('Failed to delete box: ' + (error.message || 'Unknown error'));
            }
        },
        
        // Projects
        async loadProjects() {
            this.setLoading(true);
            try {
                const result = await api.getProjects();
                this.projects = result.projects || result;
                this.clearError();
            } catch (error) {
                this.setError('Failed to load projects: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        async createProject() {
            if (!this.validateProjectForm()) return;
            
            this.setLoading(true);
            try {
                const project = await api.createProject(this.newProject);
                this.projects.push(project);
                this.resetNewProject();
                this.showCreateProjectModal = false;
                this.setSuccess('Project created successfully!');
            } catch (error) {
                this.setError('Failed to create project: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        async deleteProject(projectId) {
            this.setLoading(true);
            try {
                await api.deleteProject(projectId);
                this.projects = this.projects.filter(p => p.id !== projectId);
                if (this.currentProject && this.currentProject.id === projectId) {
                    this.currentProject = null;
                    this.currentView = 'projects';
                }
                this.setSuccess('Project deleted successfully!');
            } catch (error) {
                this.setError('Failed to delete project: ' + error.message);
            } finally {
                this.setLoading(false);
                this.showDeleteConfirmModal = false;
                this.deleteTarget = null;
            }
        },

        async loadProject(projectId) {
            this.setLoading(true);
            try {
                this.currentProject = await api.getProject(projectId);
                this.currentView = 'project-detail';
                
                // Ensure all VMs have labels array (for backward compatibility)
                if (this.currentProject.vms) {
                    this.currentProject.vms.forEach(vm => {
                        if (!vm.labels || !Array.isArray(vm.labels)) {
                            vm.labels = [];
                        }
                    });
                }
                
                // Initialize project labels
                this.updateProjectLabels();
                
                this.clearError();
            } catch (error) {
                this.setError('Failed to load project: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        // VMs
        async createVM() {
            if (!this.validateVMForm()) return;
            
            this.setLoading(true);
            try {
                const count = parseInt(this.newVM.count) || 1;
                const createdVMs = [];
                
                for (let i = 1; i <= count; i++) {
                    const vmData = { ...this.newVM };
                    
                    // Ensure numeric values
                    vmData.memory = parseInt(vmData.memory) || 1024;
                    vmData.cpus = parseInt(vmData.cpus) || 1;
                    
                    // Remove count from VM data
                    delete vmData.count;
                    
                    // Append index to name and hostname if creating multiple VMs
                    if (count > 1) {
                        vmData.name = `${this.newVM.name}-${i}`;
                        if (this.newVM.hostname) {
                            vmData.hostname = `${this.newVM.hostname}-${i}`;
                        }
                    }
                    
                    const vm = await api.createVM(this.currentProject.id, vmData);
                    
                    createdVMs.push(vm);
                    this.currentProject.vms.push(vm);
                }
                
                // Update project labels list
                this.updateProjectLabels();
                
                this.syncProjectInList();
                this.resetNewVM();
                this.showCreateVMModal = false;
                
                const successMessage = count === 1 
                    ? 'VM created successfully!' 
                    : `${count} VMs created successfully!`;
                this.setSuccess(successMessage);
            } catch (error) {
                this.setError('Failed to create VM: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        async updateVM() {
            if (!this.validateVMForm(this.editingVM)) return;
            
            this.setLoading(true);
            try {
                const originalName = this.editingVM.originalName;
                
                // Create a clean VM object without the originalName property
                const vmData = { ...this.editingVM };
                
                // Ensure numeric values
                vmData.memory = parseInt(vmData.memory) || 1024;
                vmData.cpus = parseInt(vmData.cpus) || 1;
                
                delete vmData.originalName;
                
                const vm = await api.updateVM(this.currentProject.id, originalName, vmData);
                
                // Update VM in current project
                const vmIndex = this.currentProject.vms.findIndex(v => v.name === originalName);
                if (vmIndex !== -1) {
                    this.currentProject.vms[vmIndex] = vm;
                }
                
                // Update project labels list
                this.updateProjectLabels();
                
                this.syncProjectInList();
                
                this.showEditVMModal = false;
                this.editingVM = null;
                this.setSuccess('VM updated successfully!');
            } catch (error) {
                this.setError('Failed to update VM: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        async deleteVM(vmName) {
            this.setLoading(true);
            try {
                await api.deleteVM(this.currentProject.id, vmName);
                this.currentProject.vms = this.currentProject.vms.filter(vm => vm.name !== vmName);
                
                // Update project labels list
                this.updateProjectLabels();
                
                this.syncProjectInList();
                
                this.setSuccess('VM deleted successfully!');
            } catch (error) {
                this.setError('Failed to delete VM: ' + error.message);
            } finally {
                this.setLoading(false);
                this.showDeleteConfirmModal = false;
                this.deleteTarget = null;
            }
        },

        // Vagrantfile
        async generateVagrantfile() {
            if (!this.currentProject) return;
            
            this.setLoading(true);
            try {
                const response = await api.generateVagrantfile(this.currentProject.id);
                this.vagrantfileContent = response.content;
                this.showVagrantfileModal = true;
                this.setSuccess('Vagrantfile generated successfully!');
                
                setTimeout(() => {
                    if (window.Prism) {
                        window.Prism.highlightAll();
                    }
                }, 100);
            } catch (error) {
                this.setError('Failed to generate Vagrantfile: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        async downloadVagrantfile() {
            if (!this.currentProject) return;
            
            try {
                await api.downloadVagrantfile(this.currentProject.id);
                this.setSuccess('Vagrantfile downloaded successfully!');
            } catch (error) {
                this.setError('Failed to download Vagrantfile: ' + error.message);
            }
        },

        // Integration methods - delegate to helper modules
        validateProjectForm() {
            return VagrantUIHelpers.validateProjectForm(this);
        },

        validateVMForm(vmData = null) {
            return VagrantUIHelpers.validateVMForm(this, vmData);
        },

        // Array Management
        addForwardedPort() { VagrantUIHelpers.addForwardedPort(this); },
        removeForwardedPort(index) { VagrantUIHelpers.removeForwardedPort(this, index); },
        addSyncedFolder() { VagrantUIHelpers.addSyncedFolder(this); },
        removeSyncedFolder(index) { VagrantUIHelpers.removeSyncedFolder(this, index); },
        addPrivateNetwork() { VagrantUIHelpers.addPrivateNetwork(this); },
        removePrivateNetwork(index) { VagrantUIHelpers.removePrivateNetwork(this, index); },

        // Modals
        openCreateProjectModal() { VagrantUIHelpers.openCreateProjectModal(this); },
        openCreateVMModal() { VagrantUIHelpers.openCreateVMModal(this); },
        openEditVMModal(vm) { VagrantUIHelpers.openEditVMModal(this, vm); },
        openDeleteConfirmModal(target, type) { VagrantUIHelpers.openDeleteConfirmModal(this, target, type); },
        closeDeleteConfirmModal() { VagrantUIHelpers.closeDeleteConfirmModal(this); },
        async confirmDelete() { return VagrantUIHelpers.confirmDelete(this); },

        // Helper methods
        syncProjectInList() { VagrantUIHelpers.syncProjectInList(this); },
        getDeleteMessage() { return VagrantUIHelpers.getDeleteMessage(this); },

        // Navigation
        showProjects() { VagrantUIHelpers.showProjects(this); },
        showSettings() { VagrantUIHelpers.showSettings(this); },

        // Form helpers
        resetNewProject() { VagrantUIHelpers.resetNewProject(this); },
        resetNewVM() { VagrantUIHelpers.resetNewVM(this); },

        // VM Selection and Grouping
        toggleVMSelection(vmName) { VagrantVMManager.toggleVMSelection(this, vmName); },
        isVMSelected(vmName) { return VagrantVMManager.isVMSelected(this, vmName); },
        selectAllVMs() { VagrantVMManager.selectAllVMs(this); },
        clearVMSelection() { VagrantVMManager.clearVMSelection(this); },
        getSelectedVMs() { return VagrantVMManager.getSelectedVMs(this); },
        selectVMsByLabel(label) { VagrantVMManager.selectVMsByLabel(this, label); },
        isLabelFullySelected(label) { return VagrantVMManager.isLabelFullySelected(this, label); },
        getVMCountByLabel(label) { return VagrantVMManager.getVMCountByLabel(this, label); },
        openBulkEditModal() { VagrantVMManager.openBulkEditModal(this); },
        openBulkDeleteModal() { VagrantVMManager.openBulkDeleteModal(this); },
        async bulkDeleteVMs() { return VagrantVMManager.bulkDeleteVMs(this); },
        async bulkUpdateVMs(updates) { return VagrantVMManager.bulkUpdateVMs(this, updates); },
        getVMGroup(vmName) { return VagrantVMManager.getVMGroup(this, vmName); },

        // Label management methods
        addLabel() { VagrantVMManager.addLabel(this); },
        removeLabel(index) { VagrantVMManager.removeLabel(this, index); },
        toggleLabel(label) { VagrantVMManager.toggleLabel(this, label); },
        addEditLabel() { VagrantVMManager.addEditLabel(this); },
        removeEditLabel(index) { VagrantVMManager.removeEditLabel(this, index); },
        toggleEditLabel(label) { VagrantVMManager.toggleEditLabel(this, label); },
        addBulkLabel() { VagrantVMManager.addBulkLabel(this); },
        removeBulkLabel(index) { VagrantVMManager.removeBulkLabel(this, index); },
        toggleBulkLabel(label) { VagrantVMManager.toggleBulkLabel(this, label); },
        updateProjectLabels() { VagrantVMManager.updateProjectLabels(this); },

        // UI helpers
        setLoading(loading) { VagrantUIHelpers.setLoading(this, loading); },
        setError(error) { VagrantUIHelpers.setError(this, error); },
        setSuccess(message) { VagrantUIHelpers.setSuccess(this, message); },
        clearError() { VagrantUIHelpers.clearError(this); },
        clearMessages() { VagrantUIHelpers.clearMessages(this); },
        formatDate(dateString) { return VagrantUIHelpers.formatDate(dateString); },
        copyToClipboard(text) { VagrantUIHelpers.copyToClipboard(this, text); },

        // Form sections
        setActiveFormSection(section) { VagrantUIHelpers.setActiveFormSection(this, section); },
        isFormSectionActive(section) { return VagrantUIHelpers.isFormSectionActive(this, section); }
    };
}

// Make vagrantApp available globally
window.vagrantApp = vagrantApp;