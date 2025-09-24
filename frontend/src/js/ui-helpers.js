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
        
        // Convert memory to number for proper comparison
        const memoryValue = parseInt(vm.memory) || 0;
        if (memoryValue < app.config.minMemoryMB) {
            app.validationErrors.memory = `Memory must be at least ${app.config.minMemoryMB} MB`;
        } else if (memoryValue > app.config.maxMemoryMB) {
            app.validationErrors.memory = `Memory cannot exceed ${app.config.maxMemoryMB} MB (${app.config.maxMemoryMB / 1024} GB)`;
        }
        
        // Convert cpus to number for proper comparison
        const cpusValue = parseInt(vm.cpus) || 0;
        if (cpusValue < 1) {
            app.validationErrors.cpus = 'Must have at least 1 CPU';
        } else if (cpusValue > app.config.maxCpus) {
            app.validationErrors.cpus = `Cannot exceed ${app.config.maxCpus} CPUs`;
        }
        
        // Validate network interfaces
        if (vm.network_interfaces && vm.network_interfaces.length > 0) {
            const networkErrors = {};
            vm.network_interfaces.forEach((interface, index) => {
                const interfaceErrors = this.validateNetworkInterface(interface, app, vm.network_interfaces, index);
                if (Object.keys(interfaceErrors).length > 0) {
                    networkErrors[index] = interfaceErrors;
                }
            });
            
            if (Object.keys(networkErrors).length > 0) {
                app.validationErrors.network_interfaces = networkErrors;
            }
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

    // Network Interface Management
    addNetworkInterface(app, vmData = null) {
        const vm = vmData || app.newVM;
        const newInterface = {
            id: this.generateId(),
            type: 'private_network',
            ip_assignment: 'dhcp',
            ip_address: '',
            netmask: '255.255.255.0',
            bridge: '',
            host_port: '',
            guest_port: '',
            protocol: 'tcp'
        };
        
        if (!vm.network_interfaces) {
            vm.network_interfaces = [];
        }
        vm.network_interfaces.push(newInterface);
        return newInterface;
    },
    
    removeNetworkInterface(app, index, vmData = null) {
        const vm = vmData || app.newVM;
        if (vm.network_interfaces && vm.network_interfaces[index]) {
            vm.network_interfaces.splice(index, 1);
        }
    },
    
    async removeNetworkInterfaceFromVM(app, vmName, interfaceId) {
        if (!app.currentProject) return;
        
        try {
            await api.deleteNetworkInterface(app.currentProject.id, vmName, interfaceId);
            
            // Update local data
            const vm = app.currentProject.vms.find(v => v.name === vmName);
            if (vm && vm.network_interfaces) {
                vm.network_interfaces = vm.network_interfaces.filter(ni => ni.id !== interfaceId);
            }
            
            app.setSuccess('Network interface removed successfully');
        } catch (error) {
            app.setError(`Failed to remove network interface: ${error.message}`);
        }
    },

    validateNetworkInterface(interface, app = null, allInterfaces = null, currentIndex = null) {
        const errors = {};
        
        if (interface.type === 'forwarded_port') {
            if (!interface.host_port || interface.host_port < 1 || interface.host_port > 65535) {
                errors.host_port = 'Host port must be between 1 and 65535';
            }
            if (!interface.guest_port || interface.guest_port < 1 || interface.guest_port > 65535) {
                errors.guest_port = 'Guest port must be between 1 and 65535';
            }
        } else if (interface.type === 'private_network' && interface.ip_assignment === 'static') {
            if (!interface.ip_address) {
                errors.ip_address = 'IP address is required for static assignment';
            } else {
                const ipValidation = this.validateIP(interface.ip_address, app);
                if (!ipValidation.isValid) {
                    errors.ip_address = ipValidation.error;
                } else if (allInterfaces && interface.ip_address) {
                    // Check for duplicate IP addresses within the same VM
                    const duplicateFound = allInterfaces.some((otherInterface, index) => {
                        return index !== currentIndex && 
                               otherInterface.type === 'private_network' && 
                               otherInterface.ip_assignment === 'static' && 
                               otherInterface.ip_address === interface.ip_address;
                    });
                    
                    if (duplicateFound) {
                        errors.ip_address = `IP address ${interface.ip_address} is already used by another network interface`;
                    }
                }
            }
        } else if (interface.type === 'public_network' && interface.bridge && !interface.bridge.trim()) {
            errors.bridge = 'Bridge name cannot be empty if specified';
        }
        
        return errors;
    },

    validateIP(ip, app = null) {
        // Basic IP format validation
        const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        
        if (!ipPattern.test(ip)) {
            return { isValid: false, error: 'Invalid IP address format' };
        }
        
        // Check for .1 addresses (typically network gateway)
        if (ip.endsWith('.1')) {
            return { isValid: false, error: 'IP addresses ending with .1 are not allowed (typically reserved for network gateway)' };
        }
        
        // Check private network ranges if the setting is disabled (default behavior)
        const allowPublicIPs = app && app.config && app.config.allowPublicIPsInPrivateNetworks;
        
        if (!allowPublicIPs) {
            // Additional validation for reserved ranges
            const parts = ip.split('.').map(Number);
            
            // Check for private network ranges validity
            if (parts[0] === 192 && parts[1] === 168) {
                // 192.168.x.x is valid private range
            } else if (parts[0] === 10) {
                // 10.x.x.x is valid private range  
            } else if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) {
                // 172.16-31.x.x is valid private range
            } else {
                return { isValid: false, error: 'IP address should be in a private network range (192.168.x.x, 10.x.x.x, or 172.16-31.x.x). Enable "Allow public IPs in private networks" in Settings to use other ranges.' };
            }
        }
        
        return { isValid: true };
    },

    // Backward compatibility
    isValidIP(ip, app = null) {
        return this.validateIP(ip, app).isValid;
    },

    // IP address increment utilities for bulk VM creation
    incrementIP(ip, increment = 1) {
        const parts = ip.split('.').map(Number);
        let carry = increment;
        
        // Start from the last octet and work backwards
        for (let i = 3; i >= 0 && carry > 0; i--) {
            parts[i] += carry;
            if (parts[i] > 255) {
                carry = Math.floor(parts[i] / 256);
                parts[i] = parts[i] % 256;
            } else {
                carry = 0;
            }
        }
        
        // If there's still carry, the IP range overflowed
        if (carry > 0) {
            return null; // Invalid IP
        }
        
        return parts.join('.');
    },

    calculateNetworkRange(ip, netmask) {
        const ipParts = ip.split('.').map(Number);
        const maskParts = netmask.split('.').map(Number);
        
        // Calculate network address
        const networkParts = ipParts.map((part, index) => part & maskParts[index]);
        
        // Calculate broadcast address
        const broadcastParts = ipParts.map((part, index) => part | (255 - maskParts[index]));
        
        // Calculate total available addresses (excluding network and broadcast)
        let totalAddresses = 1;
        for (let i = 0; i < 4; i++) {
            totalAddresses *= (256 - maskParts[i]);
        }
        
        return {
            network: networkParts.join('.'),
            broadcast: broadcastParts.join('.'),
            totalAddresses: totalAddresses - 2, // Exclude network and broadcast addresses
            usableStart: this.incrementIP(networkParts.join('.'), 1),
            usableEnd: this.incrementIP(broadcastParts.join('.'), -1)
        };
    },

    validateBulkIPCreation(baseIP, netmask, count, app = null) {
        const errors = [];
        
        // Validate base IP
        const ipValidation = this.validateIP(baseIP, app);
        if (!ipValidation.isValid) {
            errors.push(`Base IP address invalid: ${ipValidation.error}`);
            return { isValid: false, errors };
        }
        
        // Calculate network range
        const range = this.calculateNetworkRange(baseIP, netmask || '255.255.255.0');
        
        // Check if we have enough addresses
        if (count > range.totalAddresses) {
            errors.push(`Not enough IP addresses in network range. Need ${count} addresses, but only ${range.totalAddresses} are available in ${range.network}/${netmask}`);
        }
        
        // Check if the base IP + count would exceed the network range
        const lastIP = this.incrementIP(baseIP, count - 1);
        if (!lastIP) {
            errors.push(`IP range would overflow beyond valid IPv4 addresses`);
        } else {
            // Verify last IP is within the network range
            const lastIPParts = lastIP.split('.').map(Number);
            const broadcastParts = range.broadcast.split('.').map(Number);
            
            for (let i = 0; i < 4; i++) {
                if (lastIPParts[i] > broadcastParts[i]) {
                    errors.push(`IP range would exceed network boundary. Last IP ${lastIP} exceeds broadcast address ${range.broadcast}`);
                    break;
                }
            }
            
            // Check for .1 addresses in the range
            for (let i = 0; i < count; i++) {
                const testIP = this.incrementIP(baseIP, i);
                if (testIP && testIP.endsWith('.1')) {
                    errors.push(`IP ${testIP} (VM ${i + 1}) would end with .1, which is not allowed (typically reserved for network gateway)`);
                }
            }
        }
        
        return {
            isValid: errors.length === 0,
            errors,
            range
        };
    },

    generateId() {
        return 'ni_' + Math.random().toString(36).substr(2, 9);
    },

    getNetworkTypeDisplay(type) {
        const types = {
            'private_network': 'Private Network',
            'public_network': 'Public Network',
            'forwarded_port': 'Port Forwarding'
        };
        return types[type] || type;
    },

    getNetworkConfigDisplay(interface) {
        if (interface.type === 'forwarded_port') {
            return `${interface.host_port} → ${interface.guest_port} (${interface.protocol.toUpperCase()})`;
        } else if (interface.type === 'private_network') {
            if (interface.ip_assignment === 'static' && interface.ip_address) {
                return `Static: ${interface.ip_address}`;
            } else {
                return 'DHCP';
            }
        } else if (interface.type === 'public_network') {
            return interface.bridge ? `Bridge: ${interface.bridge}` : 'Auto-select';
        }
        return 'Unknown';
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
            private_networks: [],
            network_interfaces: []
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
        // Ensure network_interfaces is always an array
        if (!app.editingVM.network_interfaces || !Array.isArray(app.editingVM.network_interfaces)) {
            app.editingVM.network_interfaces = [];
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
            private_networks: [],
            network_interfaces: []
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