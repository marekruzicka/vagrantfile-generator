// Application state and main functionality
function vagrantApp() {
    return {
        // State
        projects: [],
        projectStats: {
            total_projects: 0,
            total_vms: 0,
            ready: 0,
            draft: 0
        },
        globalStats: {
            total_plugins: 0,
            total_provisioners: 0,
            total_triggers: 0
        },
        currentProject: null,
        currentView: 'projects',
        projectFilter: 'all', // 'all', 'draft', 'ready'
        isLoading: false,
        
        // Section collapse state
        sectionsOpen: {
            // Project detail page
            projectPlugins: true,
            projectProvisioners: true,
            projectTriggers: true,
            projectVMs: true,
            // Settings page
            settingsBoxes: true,
            settingsPlugins: true,
            settingsProvisioners: true,
            settingsTriggers: true
        },
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
            private_networks: [],
            network_interfaces: []
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
            memoryStep: 256,
            allowPublicIPsInPrivateNetworks: false
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
        
        // Plugin management state
        availablePlugins: [],
        showPluginModal: false,
        showDeletePluginConfirmModal: false,
        pluginToDelete: null,
        editingPlugin: null,
        pluginForm: {
            name: '',
            description: '',
            source_url: '',
            documentation_url: '',
            default_version: '',
            configuration: '',
            is_deprecated: false
        },
        
        // Project Plugin management state
        showAddProjectPluginModal: false,
        showDeleteProjectPluginModal: false,
        showBulkDeletePluginsModal: false,
        deletingProjectPlugin: null,
        selectedPlugins: [],
        projectPluginForm: {
            selectedPluginIds: []
        },
        
        // Global Provisioner management state
        availableProvisioners: [],
        showProvisionerModal: false,
        showDeleteProvisionerConfirmModal: false,
        provisionerToDelete: null,
        editingProvisioner: null,
        provisionerForm: {
            name: '',
            description: '',
            shell_config: {
                script: '',
                privileged: true,
                run: 'once',
                path: ''
            }
        },
        
        // Project Provisioner management state
        showAddProjectProvisionerModal: false,
        showDeleteProjectProvisionerModal: false,
        showBulkDeleteProvisionersModal: false,
        deletingProjectProvisioner: null,
        selectedProvisioners: [],
        projectProvisionersCache: {}, // Cache provisioner details by ID
        projectProvisionerForm: {
            selectedProvisionerIds: []
        },
        
        // Global Trigger management state
        availableTriggers: [],
        showEditTriggerModal: false,
        showDeleteTriggerConfirmModal: false,
        triggerToDelete: null,
        editingTrigger: null,
        returnToProjectTriggerModal: false, // Track if we should return to add project trigger modal
        triggerForm: {
            id: null,
            name: '',
            description: '',
            executionTarget: 'run', // 'run' or 'run_remote'
            trigger_config: {
                timing: 'after',
                stage: 'up',
                run: '',
                run_remote_inline: '',
                name: '',
                info: '',
                warn: '',
                on_error: 'continue'
            }
        },
        
        // Project Trigger management state
        showAddProjectTriggerModal: false,
        showDeleteProjectTriggerModal: false,
        showBulkDeleteTriggersModal: false,
        deletingProjectTrigger: null,
        selectedTriggers: [],
        projectTriggersCache: {}, // Cache trigger details by ID
        projectTriggerForm: {
            selectedTriggerIds: []
        },
        triggerSearchQuery: '', // Search query for trigger modal
        
        // VM labeling and selection state
        selectedVMs: [],
        projectLabels: [], // All available labels for current project
        selectedLabels: [], // Labels used for quick filtering
        currentLabelInput: '', // Current label being typed for new VMs
        currentEditLabelInput: '', // Current label being typed for edit VM
        currentBulkLabelInput: '', // Current label being typed for bulk edit
        
        // Network Interface Management
        showNetworkModal: false,
        currentNetworkInterface: null,
        editingNetworkInterface: null,
        isEditingNetworkInterface: false,
        
        showBulkEditModal: false,
        showBulkDeleteModal: false,
        showLabelModal: false,
        bulkEditForm: {
            memory: '',
            cpus: '',
            box: '',
            labels: [],
            network_interfaces: []
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
            await this.loadPlugins();
            await this.loadProvisioners();
            await this.loadTriggers();
        },
        
        // Configuration management
        loadConfiguration() {
            try {
                const savedConfig = localStorage.getItem('vagrantfile-generator-config');
                if (savedConfig) {
                    const config = JSON.parse(savedConfig);
                    this.config = { ...this.config, ...config };
                    // Update API configuration
                    api.setConfig(this.config);
                }
            } catch (error) {
                console.error('Failed to load configuration:', error);
            }
        },
        
        saveConfiguration() {
            try {
                localStorage.setItem('vagrantfile-generator-config', JSON.stringify(this.config));
                // Update API configuration
                api.setConfig(this.config);
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
        
        // Plugin management methods
        async loadPlugins() {
            try {
                const result = await api.getPluginsList();
                this.availablePlugins = result || [];
            } catch (error) {
                console.error('Failed to load plugins:', error);
            }
        },
        
        openAddPluginModal() {
            this.editingPlugin = null;
            this.pluginForm = {
                name: '',
                description: '',
                source_url: '',
                documentation_url: '',
                default_version: '',
                configuration: '',
                is_deprecated: false
            };
            this.showPluginModal = true;
        },
        
        openEditPluginModal(plugin) {
            this.editingPlugin = plugin;
            // Fetch full plugin details
            this.loadPluginForEdit(plugin.id);
            this.showPluginModal = true;
        },
        
        async loadPluginForEdit(pluginId) {
            try {
                const fullPlugin = await api.getPlugin(pluginId);
                this.pluginForm = {
                    name: fullPlugin.name || '',
                    description: fullPlugin.description || '',
                    source_url: fullPlugin.source_url || '',
                    documentation_url: fullPlugin.documentation_url || '',
                    default_version: fullPlugin.default_version || '',
                    configuration: fullPlugin.configuration || '',
                    is_deprecated: fullPlugin.is_deprecated || false
                };
            } catch (error) {
                console.error('Failed to load plugin details:', error);
                // Fallback to summary data
                this.pluginForm = {
                    name: this.editingPlugin.name || '',
                    description: this.editingPlugin.description || '',
                    source_url: '',
                    documentation_url: '',
                    default_version: '',
                    configuration: '',
                    is_deprecated: this.editingPlugin.is_deprecated || false
                };
            }
        },
        
        closePluginModal() {
            this.showPluginModal = false;
            this.editingPlugin = null;
            this.pluginForm = {
                name: '',
                description: '',
                source_url: '',
                documentation_url: '',
                default_version: '',
                configuration: '',
                is_deprecated: false
            };
        },
        
        async savePlugin() {
            try {
                if (!this.pluginForm.name.trim()) {
                    alert('Plugin name is required');
                    return;
                }
                
                const pluginData = {
                    name: this.pluginForm.name.trim(),
                    description: this.pluginForm.description.trim() || null,
                    source_url: this.pluginForm.source_url.trim() || null,
                    documentation_url: this.pluginForm.documentation_url.trim() || null,
                    default_version: this.pluginForm.default_version.trim() || null,
                    configuration: this.pluginForm.configuration.trim() || null,
                    is_deprecated: this.pluginForm.is_deprecated
                };
                
                if (this.editingPlugin) {
                    await api.updatePlugin(this.editingPlugin.id, pluginData);
                } else {
                    await api.createPlugin(pluginData);
                }
                
                await this.loadPlugins();
                this.closePluginModal();
            } catch (error) {
                console.error('Failed to save plugin:', error);
                alert('Failed to save plugin: ' + (error.message || 'Unknown error'));
            }
        },
        
        confirmDeletePlugin(plugin) {
            this.pluginToDelete = plugin;
            this.showDeletePluginConfirmModal = true;
        },
        
        closeDeletePluginModal() {
            this.showDeletePluginConfirmModal = false;
            this.pluginToDelete = null;
        },
        
        async deletePlugin() {
            if (!this.pluginToDelete) return;
            
            try {
                await api.deletePlugin(this.pluginToDelete.id);
                await this.loadPlugins();
                this.closeDeletePluginModal();
            } catch (error) {
                console.error('Failed to delete plugin:', error);
                alert('Failed to delete plugin: ' + (error.message || 'Unknown error'));
            }
        },
        
        // Project Plugin Management
        openAddProjectPluginModal() {
            this.resetProjectPluginForm();
            this.showAddProjectPluginModal = true;
        },
        
        togglePluginForAdd(pluginId) {
            const index = this.projectPluginForm.selectedPluginIds.indexOf(pluginId);
            if (index === -1) {
                this.projectPluginForm.selectedPluginIds.push(pluginId);
            } else {
                this.projectPluginForm.selectedPluginIds.splice(index, 1);
            }
        },
        
        async addProjectPlugins() {
            if (!this.currentProject || this.projectPluginForm.selectedPluginIds.length === 0) return;
            
            try {
                const addedPlugins = [];
                
                // Add each selected plugin
                for (const pluginId of this.projectPluginForm.selectedPluginIds) {
                    const plugin = this.availablePlugins.find(p => p.id === pluginId);
                    if (!plugin) continue;
                    
                    const pluginData = {
                        name: plugin.name,
                        version: plugin.default_version || null,
                        scope: 'global',
                        config: {}
                    };
                    
                    try {
                        const addedPlugin = await api.addPluginToProject(this.currentProject.id, pluginData);
                        if (addedPlugin) {
                            addedPlugins.push(addedPlugin);
                        }
                    } catch (error) {
                        console.error(`Failed to add plugin ${plugin.name}:`, error);
                        // Continue with other plugins
                    }
                }
                
                // Add all successfully added plugins to current project
                if (!this.currentProject.global_plugins) {
                    this.currentProject.global_plugins = [];
                }
                if (addedPlugins.length > 0) {
                    this.currentProject.global_plugins.push(...addedPlugins);
                }
                
                this.syncProjectInList();
                this.showAddProjectPluginModal = false;
                this.resetProjectPluginForm();
                
                // Show appropriate message
                if (addedPlugins.length === 0) {
                    alert('No plugins were added. They may already exist in the project.');
                } else if (addedPlugins.length < this.projectPluginForm.selectedPluginIds.length) {
                    alert(`Successfully added ${addedPlugins.length} of ${this.projectPluginForm.selectedPluginIds.length} plugins. Some plugins may already exist in the project.`);
                } else {
                    this.setSuccess(`${addedPlugins.length} plugin(s) added to project`);
                }
            } catch (error) {
                console.error('Failed to add plugins to project:', error);
                alert('Failed to add plugins: ' + (error.message || 'Unknown error'));
            }
        },
        

        
        openDeleteProjectPluginModal(plugin) {
            this.deletingProjectPlugin = plugin;
            this.showDeleteProjectPluginModal = true;
        },
        
        async deleteProjectPlugin() {
            if (!this.currentProject || !this.deletingProjectPlugin) return;
            
            try {
                await api.removePluginFromProject(this.currentProject.id, this.deletingProjectPlugin.name);
                
                // Remove from current project
                this.currentProject.global_plugins = this.currentProject.global_plugins.filter(
                    p => p.name !== this.deletingProjectPlugin.name
                );
                
                this.syncProjectInList();
                this.showDeleteProjectPluginModal = false;
                this.deletingProjectPlugin = null;
            } catch (error) {
                console.error('Failed to remove plugin from project:', error);
                alert('Failed to remove plugin: ' + (error.message || 'Unknown error'));
            }
        },
        
        openEditProjectPluginModal(pluginName) {
            // Open edit modal for this plugin without changing view
            const plugin = this.availablePlugins.find(p => p.name === pluginName);
            if (plugin) {
                this.openEditPluginModal(plugin);
            }
        },
        
        resetProjectPluginForm() {
            this.projectPluginForm = {
                selectedPluginIds: []
            };
        },
        
        // Plugin Selection Management
        isPluginSelected(pluginName) {
            return this.selectedPlugins.includes(pluginName);
        },
        
        togglePluginSelection(pluginName) {
            const index = this.selectedPlugins.indexOf(pluginName);
            if (index > -1) {
                this.selectedPlugins.splice(index, 1);
            } else {
                this.selectedPlugins.push(pluginName);
            }
        },
        
        selectAllPlugins() {
            if (!this.currentProject || !this.currentProject.global_plugins) return;
            this.selectedPlugins = this.currentProject.global_plugins.map(p => p.name);
        },
        
        clearPluginSelection() {
            this.selectedPlugins = [];
        },
        
        openBulkDeletePluginsModal() {
            if (this.selectedPlugins.length === 0) return;
            this.showBulkDeletePluginsModal = true;
        },
        
        async bulkDeletePlugins() {
            if (!this.currentProject || this.selectedPlugins.length === 0) return;
            
            try {
                // Delete each selected plugin
                const deletePromises = this.selectedPlugins.map(pluginName => 
                    api.removePluginFromProject(this.currentProject.id, pluginName)
                );
                
                await Promise.all(deletePromises);
                
                // Remove from current project
                this.currentProject.global_plugins = this.currentProject.global_plugins.filter(
                    p => !this.selectedPlugins.includes(p.name)
                );
                
                this.syncProjectInList();
                this.showBulkDeletePluginsModal = false;
                this.clearPluginSelection();
            } catch (error) {
                console.error('Failed to bulk delete plugins:', error);
                alert('Failed to delete some plugins: ' + (error.message || 'Unknown error'));
            }
        },
        
        // Provisioner Selection Management
        isProvisionerSelected(provisionerId) {
            return this.selectedProvisioners.includes(provisionerId);
        },
        
        toggleProvisionerSelection(provisionerId) {
            const index = this.selectedProvisioners.indexOf(provisionerId);
            if (index > -1) {
                this.selectedProvisioners.splice(index, 1);
            } else {
                this.selectedProvisioners.push(provisionerId);
            }
        },
        
        selectAllProvisioners() {
            if (!this.currentProject || !this.currentProject.global_provisioners) return;
            this.selectedProvisioners = [...this.currentProject.global_provisioners];
        },
        
        clearProvisionerSelection() {
            this.selectedProvisioners = [];
        },
        
        openBulkDeleteProvisionersModal() {
            if (this.selectedProvisioners.length === 0) return;
            this.showBulkDeleteProvisionersModal = true;
        },
        
        async bulkDeleteProvisioners() {
            if (!this.currentProject || this.selectedProvisioners.length === 0) return;
            
            try {
                // Delete each selected provisioner
                const deletePromises = this.selectedProvisioners.map(provisionerId => 
                    api.removeProvisionerFromProject(this.currentProject.id, provisionerId)
                );
                
                await Promise.all(deletePromises);
                
                // Remove from current project
                this.currentProject.global_provisioners = this.currentProject.global_provisioners.filter(
                    id => !this.selectedProvisioners.includes(id)
                );
                
                this.syncProjectInList();
                this.showBulkDeleteProvisionersModal = false;
                this.clearProvisionerSelection();
                this.setSuccess('Provisioners removed from project');
            } catch (error) {
                console.error('Failed to bulk delete provisioners:', error);
                alert('Failed to delete some provisioners: ' + (error.message || 'Unknown error'));
            }
        },
        
        // Project Provisioner Management
        openAddProjectProvisionerModal() {
            this.showAddProjectProvisionerModal = true;
        },
        
        closeAddProjectProvisionerModal() {
            this.showAddProjectProvisionerModal = false;
        },
        
        toggleProvisionerForAdd(provisionerId) {
            const index = this.projectProvisionerForm.selectedProvisionerIds.indexOf(provisionerId);
            if (index === -1) {
                this.projectProvisionerForm.selectedProvisionerIds.push(provisionerId);
            } else {
                this.projectProvisionerForm.selectedProvisionerIds.splice(index, 1);
            }
        },
        
        async addProjectProvisioners() {
            if (!this.currentProject || this.projectProvisionerForm.selectedProvisionerIds.length === 0) return;
            
            try {
                const addedProvisioners = [];
                
                // Add each selected provisioner to the project
                for (const provisionerId of this.projectProvisionerForm.selectedProvisionerIds) {
                    try {
                        const provisioner = this.availableProvisioners.find(p => p.id === provisionerId);
                        if (!provisioner) continue;
                        
                        // Check if provisioner is already in the project
                        if (this.currentProject.global_provisioners?.includes(provisionerId)) {
                            continue; // Skip if already added
                        }
                        
                        await api.addProvisionerToProject(this.currentProject.id, provisionerId);
                        
                        // Add to current project
                        if (!this.currentProject.global_provisioners) {
                            this.currentProject.global_provisioners = [];
                        }
                        this.currentProject.global_provisioners.push(provisionerId);
                        
                        // Cache the provisioner details
                        this.projectProvisionersCache[provisionerId] = provisioner;
                        
                        addedProvisioners.push(provisioner);
                    } catch (error) {
                        console.error(`Failed to add provisioner ${provisionerId}:`, error);
                    }
                }
                
                this.syncProjectInList();
                
                // Show appropriate message
                if (addedProvisioners.length > 0) {
                    if (addedProvisioners.length < this.projectProvisionerForm.selectedProvisionerIds.length) {
                        alert(`Successfully added ${addedProvisioners.length} of ${this.projectProvisionerForm.selectedProvisionerIds.length} provisioners. Some provisioners may already exist in the project.`);
                    } else {
                        this.setSuccess(`${addedProvisioners.length} provisioner(s) added to project`);
                    }
                }
                
                this.resetProjectProvisionerForm();
                this.showAddProjectProvisionerModal = false;
            } catch (error) {
                console.error('Failed to add provisioners:', error);
                alert('Failed to add provisioners: ' + (error.message || 'Unknown error'));
            }
        },
        
        resetProjectProvisionerForm() {
            this.projectProvisionerForm = {
                selectedProvisionerIds: []
            };
        },
        
        openDeleteProjectProvisionerModal(provisionerId) {
            this.deletingProjectProvisioner = this.projectProvisionersCache[provisionerId];
            this.showDeleteProjectProvisionerModal = true;
        },
        
        async deleteProjectProvisioner() {
            if (!this.currentProject || !this.deletingProjectProvisioner) return;
            
            try {
                await api.removeProvisionerFromProject(this.currentProject.id, this.deletingProjectProvisioner.id);
                
                // Remove from current project
                this.currentProject.global_provisioners = this.currentProject.global_provisioners.filter(
                    id => id !== this.deletingProjectProvisioner.id
                );
                
                this.syncProjectInList();
                this.showDeleteProjectProvisionerModal = false;
                this.deletingProjectProvisioner = null;
                this.setSuccess('Provisioner removed from project');
            } catch (error) {
                console.error('Failed to remove provisioner:', error);
                alert('Failed to remove provisioner: ' + (error.message || 'Unknown error'));
            }
        },
        
        openEditProjectProvisionerModal(provisionerId) {
            // Open edit modal for this provisioner without changing view
            const provisioner = this.projectProvisionersCache[provisionerId];
            if (provisioner) {
                this.openEditProvisionerModal(provisioner);
            }
        },
        
        async addProvisionerToProject(provisionerId) {
            if (!this.currentProject) return;
            
            try {
                await api.addProvisionerToProject(this.currentProject.id, provisionerId);
                
                // Add to current project
                if (!this.currentProject.global_provisioners) {
                    this.currentProject.global_provisioners = [];
                }
                this.currentProject.global_provisioners.push(provisionerId);
                
                // Cache provisioner details
                await this.loadProvisionerDetails(provisionerId);
                
                this.syncProjectInList();
                this.closeAddProjectProvisionerModal();
                this.setSuccess('Provisioner added to project');
            } catch (error) {
                console.error('Failed to add provisioner to project:', error);
                alert('Failed to add provisioner: ' + (error.message || 'Unknown error'));
            }
        },
        
        async loadProvisionerDetails(provisionerId) {
            try {
                const provisioner = await api.getProvisioner(provisionerId);
                this.projectProvisionersCache[provisionerId] = provisioner;
            } catch (error) {
                console.error(`Failed to load provisioner ${provisionerId}:`, error);
            }
        },
        
        async loadProjectProvisioners() {
            if (!this.currentProject || !this.currentProject.global_provisioners) return;
            
            // Load details for all provisioners in the project
            for (const provisionerId of this.currentProject.global_provisioners) {
                if (!this.projectProvisionersCache[provisionerId]) {
                    await this.loadProvisionerDetails(provisionerId);
                }
            }
        },
        
        async loadProjectTriggers() {
            if (!this.currentProject || !this.currentProject.global_triggers) return;
            
            // Load details for all triggers in the project
            for (const triggerId of this.currentProject.global_triggers) {
                if (!this.projectTriggersCache[triggerId]) {
                    await this.loadTriggerDetails(triggerId);
                }
            }
        },
        
        async loadTriggerDetails(triggerId) {
            try {
                const trigger = await api.getTrigger(triggerId);
                this.projectTriggersCache[triggerId] = trigger;
            } catch (error) {
                console.error(`Failed to load trigger ${triggerId}:`, error);
            }
        },
        
        getProvisionerName(provisionerId) {
            const provisioner = this.projectProvisionersCache[provisionerId];
            return provisioner ? provisioner.name : 'Loading...';
        },
        
        getProvisionerType(provisionerId) {
            const provisioner = this.projectProvisionersCache[provisionerId];
            return provisioner ? provisioner.type : '';
        },
        
        getProvisionerDescription(provisionerId) {
            const provisioner = this.projectProvisionersCache[provisionerId];
            return provisioner ? (provisioner.description || 'No description') : '';
        },
        
        // Trigger helper functions
        getTriggerById(triggerId) {
            return this.projectTriggersCache[triggerId] || 
                   this.availableTriggers.find(t => t.id === triggerId);
        },
        
        getTriggerName(triggerId) {
            const trigger = this.projectTriggersCache[triggerId];
            return trigger ? trigger.name : 'Loading...';
        },
        
        getTriggerTiming(triggerId) {
            const trigger = this.projectTriggersCache[triggerId];
            return trigger ? trigger.trigger_config?.timing || trigger.timing || '' : '';
        },
        
        getTriggerStage(triggerId) {
            const trigger = this.projectTriggersCache[triggerId];
            return trigger ? trigger.trigger_config?.stage || trigger.stage || '' : '';
        },
        
        getTriggerDescription(triggerId) {
            const trigger = this.projectTriggersCache[triggerId];
            return trigger ? (trigger.description || 'No description') : '';
        },
        
        openEditProjectTriggerModal(triggerId) {
            const trigger = this.getTriggerById(triggerId);
            if (trigger) {
                this.openEditTriggerModal(trigger);
            }
        },
        
        // Projects
        async loadProjects() {
            this.setLoading(true);
            try {
                // Load projects based on current filter
                const filter = this.projectFilter === 'all' ? null : this.projectFilter;
                const result = await api.getProjects(filter);
                this.projects = result.projects || result;
                
                // Load project and global statistics
                await Promise.all([
                    this.loadProjectStats(),
                    this.loadGlobalStats()
                ]);
                this.clearError();
            } catch (error) {
                this.setError('Failed to load projects: ' + error.message);
            } finally {
                this.setLoading(false);
            }
        },

        async loadProjectStats() {
            try {
                this.projectStats = await api.getProjectStats();
            } catch (error) {
                console.warn('Failed to load project stats:', error);
            }
        },

        async loadGlobalStats() {
            try {
                // Load global resources counts
                const [plugins, provisioners, triggers] = await Promise.all([
                    api.getPlugins().catch(() => []),
                    api.getProvisioners().catch(() => []),
                    api.getTriggers().catch(() => [])
                ]);
                
                this.globalStats = {
                    total_plugins: plugins.length,
                    total_provisioners: provisioners.length,
                    total_triggers: triggers.length
                };
            } catch (error) {
                console.warn('Failed to load global stats:', error);
            }
        },

        setProjectFilter(filter) {
            this.projectFilter = filter;
            this.loadProjects();
        },

        async updateDeploymentStatus(projectId, status) {
            try {
                await api.updateProjectDeploymentStatus(projectId, status);
                
                // Update current project if it's the one being updated
                if (this.currentProject && this.currentProject.id === projectId) {
                    this.currentProject.deployment_status = status;
                }
                
                // Reload projects and stats
                await this.loadProjects();
                this.setSuccess(`Project deployment status updated to ${status}`);
            } catch (error) {
                this.setError('Failed to update deployment status: ' + error.message);
            }
        },

        async createProject() {
            if (!this.validateProjectForm()) return;
            
            this.setLoading(true);
            try {
                const project = await api.createProject(this.newProject);
                this.resetNewProject();
                this.showCreateProjectModal = false;
                this.setSuccess('Project created successfully!');
                
                // Reload projects and stats to ensure proper state update
                await this.loadProjects();
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
                
                // Update current project state if it's being deleted
                if (this.currentProject && this.currentProject.id === projectId) {
                    this.currentProject = null;
                    this.currentView = 'projects';
                }
                
                // Reload projects and stats to ensure proper state update
                await this.loadProjects();
                
                // If no projects exist after deletion, reset filter to 'all'
                if (this.projectStats.total_projects === 0) {
                    this.projectFilter = 'all';
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
                
                // Load project provisioners
                await this.loadProjectProvisioners();
                
                // Load project triggers
                await this.loadProjectTriggers();
                
                // Clear selections
                this.clearVMSelection();
                this.clearPluginSelection();
                
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
                
                // Pre-validate bulk IP creation if needed
                if (count > 1) {
                    const bulkValidationErrors = this.validateBulkIPRanges(count);
                    if (bulkValidationErrors.length > 0) {
                        this.setError(`Bulk creation validation failed: ${bulkValidationErrors.join(', ')}`);
                        return;
                    }
                }
                
                const createdVMs = [];
                
                for (let i = 1; i <= count; i++) {
                    const vmData = { ...this.newVM };
                    
                    // Clean up and increment network interfaces data
                    if (vmData.network_interfaces) {
                        vmData.network_interfaces = vmData.network_interfaces.map(interface => {
                            const cleanInterface = { ...interface };
                            
                            // Remove empty string values that should be null
                            Object.keys(cleanInterface).forEach(key => {
                                if (cleanInterface[key] === '') {
                                    cleanInterface[key] = null;
                                }
                            });
                            
                            // Convert port numbers to integers
                            if (cleanInterface.host_port !== null) {
                                cleanInterface.host_port = parseInt(cleanInterface.host_port) || null;
                            }
                            if (cleanInterface.guest_port !== null) {
                                cleanInterface.guest_port = parseInt(cleanInterface.guest_port) || null;
                            }
                            
                            // Handle IP address incrementing for bulk creation
                            if (count > 1 && cleanInterface.type === 'private_network' && 
                                cleanInterface.ip_assignment === 'static' && cleanInterface.ip_address) {
                                const incrementedIP = VagrantUIHelpers.incrementIP(cleanInterface.ip_address, i - 1);
                                if (incrementedIP) {
                                    cleanInterface.ip_address = incrementedIP;
                                }
                            }
                            
                            return cleanInterface;
                        });
                    }
                    
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
                console.error('CreateVM Error:', error);
                let errorMessage = 'Failed to create VM: ';
                
                if (error && typeof error === 'object') {
                    if (error.message) {
                        errorMessage += error.message;
                    } else {
                        try {
                            errorMessage += JSON.stringify(error);
                        } catch (stringifyError) {
                            errorMessage += 'Unknown error occurred';
                        }
                    }
                } else {
                    errorMessage += String(error);
                }
                
                this.setError(errorMessage);
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
                
                // Clean up network interfaces data
                if (vmData.network_interfaces) {
                    vmData.network_interfaces = vmData.network_interfaces.map(interface => {
                        const cleanInterface = { ...interface };
                        
                        // Remove empty string values that should be null
                        Object.keys(cleanInterface).forEach(key => {
                            if (cleanInterface[key] === '') {
                                cleanInterface[key] = null;
                            }
                        });
                        
                        // Convert port numbers to integers
                        if (cleanInterface.host_port !== null) {
                            cleanInterface.host_port = parseInt(cleanInterface.host_port) || null;
                        }
                        if (cleanInterface.guest_port !== null) {
                            cleanInterface.guest_port = parseInt(cleanInterface.guest_port) || null;
                        }
                        
                        return cleanInterface;
                    });
                }
                
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
                
                this.closeEditVMModal();
                this.setSuccess('VM updated successfully!');
            } catch (error) {
                console.error('UpdateVM Error:', error);
                let errorMessage = 'Failed to update VM: ';
                
                if (error && typeof error === 'object') {
                    if (error.message) {
                        // Try to parse validation errors from the message
                        try {
                            const parsed = JSON.parse(error.message);
                            if (parsed.detail && Array.isArray(parsed.detail)) {
                                const validationErrors = parsed.detail.map(err => err.msg).join(', ');
                                errorMessage += validationErrors;
                            } else {
                                errorMessage += error.message;
                            }
                        } catch (parseError) {
                            errorMessage += error.message;
                        }
                    } else {
                        // If error is an object, try to stringify it properly
                        try {
                            errorMessage += JSON.stringify(error);
                        } catch (stringifyError) {
                            errorMessage += 'Unknown error occurred';
                        }
                    }
                } else {
                    errorMessage += String(error);
                }
                
                this.setError(errorMessage);
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

        validateBulkIPRanges(count) {
            const errors = [];
            
            if (!this.newVM.network_interfaces) {
                return errors;
            }
            
            this.newVM.network_interfaces.forEach((interface, index) => {
                if (interface.type === 'private_network' && 
                    interface.ip_assignment === 'static' && 
                    interface.ip_address) {
                    
                    const validation = VagrantUIHelpers.validateBulkIPCreation(
                        interface.ip_address, 
                        interface.netmask || '255.255.255.0', 
                        count,
                        this
                    );
                    
                    if (!validation.isValid) {
                        validation.errors.forEach(error => {
                            errors.push(`Network interface ${index + 1}: ${error}`);
                        });
                    }
                }
            });
            
            return errors;
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
        closeEditVMModal() { VagrantUIHelpers.closeEditVMModal(this); },
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

        // Network Interface Management
        addNetworkInterface(vmData = null) { return VagrantUIHelpers.addNetworkInterface(this, vmData); },
        removeNetworkInterface(index, vmData = null) { VagrantUIHelpers.removeNetworkInterface(this, index, vmData); },
        async removeNetworkInterfaceFromVM(vmName, interfaceId) { 
            return VagrantUIHelpers.removeNetworkInterfaceFromVM(this, vmName, interfaceId); 
        },
        validateNetworkInterface(interface) { return VagrantUIHelpers.validateNetworkInterface(interface, this); },
        getNetworkTypeDisplay(type) { return VagrantUIHelpers.getNetworkTypeDisplay(type); },
        getNetworkConfigDisplay(interface) { return VagrantUIHelpers.getNetworkConfigDisplay(interface); },

        // Global Provisioner Management
        async loadProvisioners() {
            try {
                const result = await api.getProvisionersList();
                this.availableProvisioners = result || [];
            } catch (error) {
                console.error('Failed to load provisioners:', error);
            }
        },
        
        openAddProvisionerModal() {
            this.editingProvisioner = null;
            this.provisionerForm = {
                name: '',
                description: '',
                shell_config: {
                    script: '',
                    privileged: true,
                    run: 'once',
                    path: ''
                }
            };
            this.showProvisionerModal = true;
        },
        
        openEditProvisionerModal(provisioner) {
            this.editingProvisioner = provisioner;
            this.loadProvisionerForEdit(provisioner.id);
            this.showProvisionerModal = true;
        },
        
        async loadProvisionerForEdit(provisionerId) {
            try {
                const fullProvisioner = await api.getProvisioner(provisionerId);
                this.provisionerForm = {
                    name: fullProvisioner.name || '',
                    description: fullProvisioner.description || '',
                    shell_config: {
                        script: fullProvisioner.shell_config?.script || '',
                        privileged: fullProvisioner.shell_config?.privileged ?? true,
                        run: fullProvisioner.shell_config?.run || 'once',
                        path: fullProvisioner.shell_config?.path || ''
                    }
                };
            } catch (error) {
                console.error('Failed to load provisioner details:', error);
                this.provisionerForm = {
                    name: this.editingProvisioner.name || '',
                    description: this.editingProvisioner.description || '',
                    shell_config: {
                        script: '',
                        privileged: true,
                        run: 'once',
                        path: ''
                    }
                };
            }
        },
        
        closeProvisionerModal() {
            this.showProvisionerModal = false;
            this.editingProvisioner = null;
            this.provisionerForm = {
                name: '',
                description: '',
                shell_config: {
                    script: '',
                    privileged: true,
                    run: 'once',
                    path: ''
                }
            };
        },
        
        async saveProvisioner() {
            try {
                if (!this.provisionerForm.name.trim()) {
                    alert('Provisioner name is required');
                    return;
                }
                
                if (!this.provisionerForm.shell_config.script.trim() && !this.provisionerForm.shell_config.path.trim()) {
                    alert('Either script content or external script path is required');
                    return;
                }
                
                const provisionerData = {
                    name: this.provisionerForm.name.trim(),
                    description: this.provisionerForm.description.trim() || null,
                    type: 'shell',
                    scope: 'global',
                    shell_config: {
                        script: this.provisionerForm.shell_config.script.trim(),
                        privileged: this.provisionerForm.shell_config.privileged,
                        run: this.provisionerForm.shell_config.run,
                        path: this.provisionerForm.shell_config.path.trim() || null
                    }
                };
                
                if (this.editingProvisioner) {
                    await api.updateProvisioner(this.editingProvisioner.id, provisionerData);
                } else {
                    await api.createProvisioner(provisionerData);
                }
                
                await this.loadProvisioners();
                this.closeProvisionerModal();
                this.setSuccess('Provisioner saved successfully');
            } catch (error) {
                console.error('Failed to save provisioner:', error);
                alert('Failed to save provisioner: ' + (error.message || 'Unknown error'));
            }
        },
        
        confirmDeleteProvisioner(provisioner) {
            this.provisionerToDelete = provisioner;
            this.showDeleteProvisionerConfirmModal = true;
        },
        
        closeDeleteProvisionerModal() {
            this.showDeleteProvisionerConfirmModal = false;
            this.provisionerToDelete = null;
        },
        
        async deleteProvisioner() {
            if (!this.provisionerToDelete) return;
            
            try {
                await api.deleteProvisioner(this.provisionerToDelete.id);
                await this.loadProvisioners();
                this.closeDeleteProvisionerModal();
                this.setSuccess('Provisioner deleted successfully');
            } catch (error) {
                console.error('Failed to delete provisioner:', error);
                alert('Failed to delete provisioner: ' + (error.message || 'Unknown error'));
            }
        },

        // Global Trigger Management
        async loadTriggers() {
            try {
                const result = await api.getTriggersList();
                this.availableTriggers = result || [];
            } catch (error) {
                console.error('Failed to load triggers:', error);
            }
        },
        
        openCreateTriggerModal(returnToProjectModal = false) {
            this.editingTrigger = null;
            this.returnToProjectTriggerModal = returnToProjectModal;
            this.triggerForm = {
                id: null,
                name: '',
                description: '',
                executionTarget: 'run',
                trigger_config: {
                    timing: 'after',
                    stage: 'up',
                    run: '',
                    run_remote_inline: '',
                    name: '',
                    info: '',
                    warn: '',
                    on_error: 'continue'
                }
            };
            this.showEditTriggerModal = true;
        },
        
        openEditTriggerModal(trigger) {
            this.editingTrigger = trigger;
            this.loadTriggerForEdit(trigger.id);
            this.showEditTriggerModal = true;
        },
        
        async loadTriggerForEdit(triggerId) {
            try {
                const fullTrigger = await api.getTrigger(triggerId);
                this.triggerForm = {
                    id: fullTrigger.id,
                    name: fullTrigger.name || '',
                    description: fullTrigger.description || '',
                    executionTarget: fullTrigger.trigger_config?.run ? 'run' : 'run_remote',
                    trigger_config: {
                        timing: fullTrigger.trigger_config?.timing || 'after',
                        stage: fullTrigger.trigger_config?.stage || 'up',
                        run: fullTrigger.trigger_config?.run || '',
                        run_remote_inline: fullTrigger.trigger_config?.run_remote_inline || '',
                        name: fullTrigger.trigger_config?.name || '',
                        info: fullTrigger.trigger_config?.info || '',
                        warn: fullTrigger.trigger_config?.warn || '',
                        on_error: fullTrigger.trigger_config?.on_error || 'continue'
                    }
                };
            } catch (error) {
                console.error('Failed to load trigger details:', error);
                this.triggerForm = {
                    id: this.editingTrigger?.id || null,
                    name: this.editingTrigger.name || '',
                    description: this.editingTrigger.description || '',
                    executionTarget: 'run',
                    trigger_config: {
                        timing: 'after',
                        stage: 'up',
                        run: '',
                        run_remote_inline: '',
                        name: '',
                        info: '',
                        warn: '',
                        on_error: 'continue'
                    }
                };
            }
        },
        
        closeEditTriggerModal() {
            this.showEditTriggerModal = false;
            this.editingTrigger = null;
            this.triggerForm = {
                id: null,
                name: '',
                description: '',
                executionTarget: 'run',
                trigger_config: {
                    timing: 'after',
                    stage: 'up',
                    run: '',
                    run_remote_inline: '',
                    name: '',
                    info: '',
                    warn: '',
                    on_error: 'continue'
                }
            };
        },
        
        async createTrigger() {
            try {
                if (!this.triggerForm.name.trim()) {
                    alert('Trigger name is required');
                    return;
                }
                
                const command = this.triggerForm.executionTarget === 'run' 
                    ? this.triggerForm.trigger_config.run.trim()
                    : this.triggerForm.trigger_config.run_remote_inline.trim();
                
                if (!command) {
                    alert('Command is required');
                    return;
                }
                
                const triggerData = {
                    name: this.triggerForm.name.trim(),
                    description: this.triggerForm.description.trim() || null,
                    trigger_config: {
                        timing: this.triggerForm.trigger_config.timing,
                        stage: this.triggerForm.trigger_config.stage,
                        on_error: this.triggerForm.trigger_config.on_error
                    }
                };
                
                // Add execution target
                if (this.triggerForm.executionTarget === 'run') {
                    triggerData.trigger_config.run = command;
                } else {
                    triggerData.trigger_config.run_remote_inline = command;
                }
                
                // Add optional fields if provided
                if (this.triggerForm.trigger_config.name.trim()) {
                    triggerData.trigger_config.name = this.triggerForm.trigger_config.name.trim();
                }
                if (this.triggerForm.trigger_config.info.trim()) {
                    triggerData.trigger_config.info = this.triggerForm.trigger_config.info.trim();
                }
                if (this.triggerForm.trigger_config.warn.trim()) {
                    triggerData.trigger_config.warn = this.triggerForm.trigger_config.warn.trim();
                }
                
                await api.createTrigger(triggerData);
                await this.loadTriggers();
                this.closeEditTriggerModal();
                this.setSuccess('Trigger created successfully');
                
                // If we came from the project trigger modal, reopen it
                if (this.returnToProjectTriggerModal) {
                    this.returnToProjectTriggerModal = false;
                    await this.openAddProjectTriggerModal();
                }
            } catch (error) {
                console.error('Failed to create trigger:', error);
                alert('Failed to create trigger: ' + (error.message || 'Unknown error'));
            }
        },
        
        async updateTrigger() {
            try {
                if (!this.triggerForm.name.trim()) {
                    alert('Trigger name is required');
                    return;
                }
                
                const command = this.triggerForm.executionTarget === 'run' 
                    ? this.triggerForm.trigger_config.run.trim()
                    : this.triggerForm.trigger_config.run_remote_inline.trim();
                
                if (!command) {
                    alert('Command is required');
                    return;
                }
                
                const triggerData = {
                    name: this.triggerForm.name.trim(),
                    description: this.triggerForm.description.trim() || null,
                    trigger_config: {
                        timing: this.triggerForm.trigger_config.timing,
                        stage: this.triggerForm.trigger_config.stage,
                        on_error: this.triggerForm.trigger_config.on_error
                    }
                };
                
                // Add execution target
                if (this.triggerForm.executionTarget === 'run') {
                    triggerData.trigger_config.run = command;
                } else {
                    triggerData.trigger_config.run_remote_inline = command;
                }
                
                // Add optional fields if provided
                if (this.triggerForm.trigger_config.name.trim()) {
                    triggerData.trigger_config.name = this.triggerForm.trigger_config.name.trim();
                }
                if (this.triggerForm.trigger_config.info.trim()) {
                    triggerData.trigger_config.info = this.triggerForm.trigger_config.info.trim();
                }
                if (this.triggerForm.trigger_config.warn.trim()) {
                    triggerData.trigger_config.warn = this.triggerForm.trigger_config.warn.trim();
                }
                
                await api.updateTrigger(this.editingTrigger.id, triggerData);
                await this.loadTriggers();
                this.closeEditTriggerModal();
                this.setSuccess('Trigger updated successfully');
            } catch (error) {
                console.error('Failed to update trigger:', error);
                alert('Failed to update trigger: ' + (error.message || 'Unknown error'));
            }
        },
        
        confirmDeleteTrigger(trigger) {
            this.triggerToDelete = trigger;
            this.showDeleteTriggerConfirmModal = true;
        },
        
        closeDeleteTriggerModal() {
            this.showDeleteTriggerConfirmModal = false;
            this.triggerToDelete = null;
        },
        
        async deleteTrigger() {
            if (!this.triggerToDelete) return;
            
            try {
                await api.deleteTrigger(this.triggerToDelete.id);
                await this.loadTriggers();
                this.closeDeleteTriggerModal();
                this.setSuccess('Trigger deleted successfully');
            } catch (error) {
                console.error('Failed to delete trigger:', error);
                alert('Failed to delete trigger: ' + (error.message || 'Unknown error'));
            }
        },
        
        // Project Trigger Management
        toggleTriggerForAdd(triggerId) {
            const index = this.projectTriggerForm.selectedTriggerIds.indexOf(triggerId);
            if (index > -1) {
                this.projectTriggerForm.selectedTriggerIds.splice(index, 1);
            } else {
                this.projectTriggerForm.selectedTriggerIds.push(triggerId);
            }
        },
        
        isTriggerSelectedForAdd(triggerId) {
            return this.projectTriggerForm.selectedTriggerIds.includes(triggerId);
        },
        
        async openAddProjectTriggerModal() {
            this.projectTriggerForm.selectedTriggerIds = [];
            await this.loadTriggers(); // Ensure we have the latest available triggers
            this.showAddProjectTriggerModal = true;
        },
        
        closeAddProjectTriggerModal() {
            this.showAddProjectTriggerModal = false;
            this.projectTriggerForm.selectedTriggerIds = [];
        },
        
        async addProjectTriggers() {
            if (this.projectTriggerForm.selectedTriggerIds.length === 0) {
                alert('Please select at least one trigger');
                return;
            }
            
            try {
                for (const triggerId of this.projectTriggerForm.selectedTriggerIds) {
                    await api.addTriggerToProject(this.currentProject.id, triggerId);
                }
                
                await this.loadProject(this.currentProject.id);
                this.closeAddProjectTriggerModal();
                this.setSuccess(`${this.projectTriggerForm.selectedTriggerIds.length} trigger(s) added successfully`);
            } catch (error) {
                console.error('Failed to add triggers:', error);
                alert('Failed to add triggers: ' + (error.message || 'Unknown error'));
            }
        },
        
        confirmDeleteProjectTrigger(trigger) {
            this.deletingProjectTrigger = trigger;
            this.showDeleteProjectTriggerModal = true;
        },
        
        closeDeleteProjectTriggerModal() {
            this.showDeleteProjectTriggerModal = false;
            this.deletingProjectTrigger = null;
        },
        
        async removeProjectTrigger() {
            if (!this.deletingProjectTrigger) return;
            
            try {
                await api.removeTriggerFromProject(this.currentProject.id, this.deletingProjectTrigger.id);
                await this.loadProject(this.currentProject.id);
                this.closeDeleteProjectTriggerModal();
                this.setSuccess('Trigger removed from project successfully');
            } catch (error) {
                console.error('Failed to remove trigger:', error);
                alert('Failed to remove trigger: ' + (error.message || 'Unknown error'));
            }
        },
        
        toggleTriggerSelection(triggerId) {
            const index = this.selectedTriggers.indexOf(triggerId);
            if (index > -1) {
                this.selectedTriggers.splice(index, 1);
            } else {
                this.selectedTriggers.push(triggerId);
            }
        },
        
        isTriggerSelected(triggerId) {
            return this.selectedTriggers.includes(triggerId);
        },
        
        selectAllTriggers() {
            if (!this.currentProject || !this.currentProject.global_triggers) return;
            this.selectedTriggers = [...this.currentProject.global_triggers];
        },
        
        clearTriggerSelection() {
            this.selectedTriggers = [];
        },
        
        openBulkDeleteTriggersModal() {
            if (this.selectedTriggers.length === 0) return;
            this.showBulkDeleteTriggersModal = true;
        },
        
        async bulkDeleteTriggers() {
            if (this.selectedTriggers.length === 0) return;
            
            try {
                for (const triggerId of this.selectedTriggers) {
                    await api.removeTriggerFromProject(this.currentProject.id, triggerId);
                }
                
                await this.loadProject(this.currentProject.id);
                this.clearTriggerSelection();
                this.showBulkDeleteTriggersModal = false;
                this.setSuccess(`${this.selectedTriggers.length} trigger(s) removed successfully`);
            } catch (error) {
                console.error('Failed to remove triggers:', error);
                alert('Failed to remove triggers: ' + (error.message || 'Unknown error'));
            }
        },

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