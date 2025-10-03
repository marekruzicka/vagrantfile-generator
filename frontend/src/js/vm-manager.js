// VM selection, labeling, and bulk operations
const VagrantVMManager = {
    // VM Selection and Grouping
    toggleVMSelection(app, vmName) {
        const index = app.selectedVMs.indexOf(vmName);
        if (index === -1) {
            app.selectedVMs.push(vmName);
        } else {
            app.selectedVMs.splice(index, 1);
        }
    },
    
    isVMSelected(app, vmName) {
        return app.selectedVMs.includes(vmName);
    },
    
    selectAllVMs(app) {
        app.selectedVMs = app.currentProject?.vms?.map(vm => vm.name) || [];
    },
    
    clearVMSelection(app) {
        app.selectedVMs = [];
    },
    
    getSelectedVMs(app) {
        return app.currentProject?.vms?.filter(vm => app.selectedVMs.includes(vm.name)) || [];
    },
    
    selectVMsByLabel(app, label) {
        if (!app.currentProject) return;
        
        const vmsWithLabel = app.currentProject.vms.filter(vm => 
            vm.labels && Array.isArray(vm.labels) && vm.labels.includes(label)
        );
        
        const vmNames = vmsWithLabel.map(vm => vm.name);
        // Toggle selection - if all VMs with this label are already selected, deselect them
        const allSelected = vmNames.every(name => app.selectedVMs.includes(name));
        
        if (allSelected) {
            app.selectedVMs = app.selectedVMs.filter(name => !vmNames.includes(name));
        } else {
            // Add unselected VMs with this label
            vmNames.forEach(name => {
                if (!app.selectedVMs.includes(name)) {
                    app.selectedVMs.push(name);
                }
            });
        }
    },
    
    isLabelFullySelected(app, label) {
        if (!app.currentProject) return false;
        
        const vmsWithLabel = app.currentProject.vms.filter(vm => 
            vm.labels && Array.isArray(vm.labels) && vm.labels.includes(label)
        );
        
        return vmsWithLabel.length > 0 && 
               vmsWithLabel.every(vm => app.selectedVMs.includes(vm.name));
    },
    
    getVMCountByLabel(app, label) {
        if (!app.currentProject) return 0;
        
        return app.currentProject.vms.filter(vm => 
            vm.labels && Array.isArray(vm.labels) && vm.labels.includes(label)
        ).length;
    },
    
    openBulkEditModal(app) {
        if (app.selectedVMs.length === 0) {
            app.setError('Please select at least one VM to edit');
            return;
        }
        app.showBulkEditModal = true;
    },
    
    openBulkDeleteModal(app) {
        if (app.selectedVMs.length === 0) {
            app.setError('Please select at least one VM to delete');
            return;
        }
        app.showBulkDeleteModal = true;
    },
    
    async bulkDeleteVMs(app) {
        const selectedVMs = VagrantVMManager.getSelectedVMs(app);
        
        app.setLoading(true);
        try {
            const promises = selectedVMs.map(vm => 
                api.deleteVM(app.currentProject.id, vm.name)
            );
            
            await Promise.all(promises);
            
            // Remove deleted VMs from current project
            const deletedNames = selectedVMs.map(vm => vm.name);
            app.currentProject.vms = app.currentProject.vms.filter(vm => 
                !deletedNames.includes(vm.name)
            );
            
            // Update project labels
            VagrantVMManager.updateProjectLabels(app);
            
            VagrantUIHelpers.syncProjectInList(app);
            VagrantVMManager.clearVMSelection(app);
            app.showBulkDeleteModal = false;
            
            app.setSuccess(`${selectedVMs.length} VMs deleted successfully!`);
        } catch (error) {
            app.setError('Failed to delete VMs: ' + error.message);
        } finally {
            app.setLoading(false);
        }
    },
    
    async bulkUpdateVMs(app, updates) {
        const selectedVMs = VagrantVMManager.getSelectedVMs(app);
        
        app.setLoading(true);
        try {
            const promises = selectedVMs.map((vm, vmIndex) => {
                const vmData = { ...vm };
                
                // Apply updates, but only for fields that have values
                if (updates.memory && updates.memory.toString().trim()) {
                    vmData.memory = parseInt(updates.memory);
                }
                if (updates.cpus && updates.cpus.toString().trim()) {
                    vmData.cpus = parseInt(updates.cpus);
                }
                if (updates.box && updates.box.trim()) {
                    vmData.box = updates.box;
                }
                
                // Handle labels - merge new labels with existing ones
                if (updates.labels && updates.labels.length > 0) {
                    const existingLabels = vmData.labels || [];
                    const newLabels = [...new Set([...existingLabels, ...updates.labels])]; // Remove duplicates
                    vmData.labels = newLabels;
                }
                
                // Handle network interfaces - add new interfaces to existing ones
                if (updates.network_interfaces && updates.network_interfaces.length > 0) {
                    const existingInterfaces = vmData.network_interfaces || [];
                    // Create new interfaces with unique IDs for each VM and sanitize based on type
                    const newInterfaces = updates.network_interfaces.map(iface => {
                        const sanitized = {
                            ...iface,
                            id: VagrantUIHelpers.generateId() // Generate unique ID for each interface
                        };
                        
                        // Sanitize fields based on network type - delete unused fields entirely
                        if (sanitized.type === 'private_network') {
                            // Private networks don't use bridge, host_port, guest_port, protocol
                            delete sanitized.bridge;
                            delete sanitized.host_port;
                            delete sanitized.guest_port;
                            delete sanitized.protocol;
                            // Convert empty strings to null for optional fields
                            if (sanitized.ip_address === '') sanitized.ip_address = null;
                            if (sanitized.netmask === '') sanitized.netmask = null;
                            
                            // Handle IP address incrementing for bulk edit (same logic as bulk creation)
                            if (selectedVMs.length > 1 && sanitized.ip_assignment === 'static' && sanitized.ip_address) {
                                const incrementedIP = VagrantUIHelpers.incrementIP(sanitized.ip_address, vmIndex);
                                if (incrementedIP) {
                                    sanitized.ip_address = incrementedIP;
                                }
                            }
                        } else if (sanitized.type === 'public_network') {
                            // Public networks only use bridge (optional) - delete all other fields
                            delete sanitized.host_port;
                            delete sanitized.guest_port;
                            delete sanitized.ip_address;
                            delete sanitized.netmask;
                            delete sanitized.ip_assignment;
                            delete sanitized.protocol;
                            // Convert empty string bridge to null (optional field)
                            if (sanitized.bridge === '') delete sanitized.bridge;
                        } else if (sanitized.type === 'forwarded_port') {
                            // Forwarded ports don't use bridge, ip_address, netmask, ip_assignment
                            delete sanitized.bridge;
                            delete sanitized.ip_address;
                            delete sanitized.netmask;
                            delete sanitized.ip_assignment;
                            // Ensure ports are integers or null
                            sanitized.host_port = sanitized.host_port ? parseInt(sanitized.host_port) : null;
                            sanitized.guest_port = sanitized.guest_port ? parseInt(sanitized.guest_port) : null;
                            // Ensure protocol is set (default to tcp)
                            if (!sanitized.protocol || sanitized.protocol === '') sanitized.protocol = 'tcp';
                        }
                        
                        return sanitized;
                    });
                    vmData.network_interfaces = [...existingInterfaces, ...newInterfaces];
                }
                
                delete vmData.originalName;
                return api.updateVM(app.currentProject.id, vm.name, vmData);
            });
            
            await Promise.all(promises);
            await app.loadProject(app.currentProject.id);
            
            // Update project labels
            VagrantVMManager.updateProjectLabels(app);
            
            VagrantVMManager.clearVMSelection(app);
            app.showBulkEditModal = false;
            
            // Reset bulk edit form
            app.bulkEditForm = {
                memory: '',
                cpus: '',
                box: '',
                labels: [],
                network_interfaces: []
            };
            
            app.setSuccess(`${selectedVMs.length} VMs updated successfully!`);
        } catch (error) {
            app.setError('Failed to update VMs: ' + error.message);
        } finally {
            app.setLoading(false);
        }
    },
    
    getVMGroup(app, vmName) {
        return app.vmGroups?.find(group => group.vmNames.includes(vmName));
    },
    
    // Label management methods
    addLabel(app) {
        if (!app.currentLabelInput || !app.currentLabelInput.trim()) return;
        
        const label = app.currentLabelInput.trim();
        if (!app.newVM.labels) {
            app.newVM.labels = [];
        }
        
        if (!app.newVM.labels.includes(label)) {
            app.newVM.labels.push(label);
        }
        
        app.currentLabelInput = '';
    },
    
    removeLabel(app, index) {
        if (app.newVM.labels && index >= 0 && index < app.newVM.labels.length) {
            app.newVM.labels.splice(index, 1);
        }
    },
    
    toggleLabel(app, label) {
        if (!app.newVM.labels) {
            app.newVM.labels = [];
        }
        
        const index = app.newVM.labels.indexOf(label);
        if (index > -1) {
            app.newVM.labels.splice(index, 1);
        } else {
            app.newVM.labels.push(label);
        }
    },
    
    // Edit VM label management methods
    addEditLabel(app) {
        if (!app.currentEditLabelInput || !app.currentEditLabelInput.trim()) return;
        
        const label = app.currentEditLabelInput.trim();
        if (!app.editingVM.labels) {
            app.editingVM.labels = [];
        }
        
        if (!app.editingVM.labels.includes(label)) {
            app.editingVM.labels.push(label);
        }
        
        app.currentEditLabelInput = '';
    },
    
    removeEditLabel(app, index) {
        if (app.editingVM.labels && index >= 0 && index < app.editingVM.labels.length) {
            app.editingVM.labels.splice(index, 1);
        }
    },
    
    toggleEditLabel(app, label) {
        if (!app.editingVM.labels) {
            app.editingVM.labels = [];
        }
        
        const index = app.editingVM.labels.indexOf(label);
        if (index > -1) {
            app.editingVM.labels.splice(index, 1);
        } else {
            app.editingVM.labels.push(label);
        }
    },
    
    // Bulk edit label management methods
    addBulkLabel(app) {
        if (!app.currentBulkLabelInput || !app.currentBulkLabelInput.trim()) return;
        
        const label = app.currentBulkLabelInput.trim();
        if (!app.bulkEditForm.labels) {
            app.bulkEditForm.labels = [];
        }
        
        if (!app.bulkEditForm.labels.includes(label)) {
            app.bulkEditForm.labels.push(label);
        }
        
        app.currentBulkLabelInput = '';
    },
    
    removeBulkLabel(app, index) {
        if (app.bulkEditForm.labels && index >= 0 && index < app.bulkEditForm.labels.length) {
            app.bulkEditForm.labels.splice(index, 1);
        }
    },
    
    toggleBulkLabel(app, label) {
        if (!app.bulkEditForm.labels) {
            app.bulkEditForm.labels = [];
        }
        
        const index = app.bulkEditForm.labels.indexOf(label);
        if (index > -1) {
            app.bulkEditForm.labels.splice(index, 1);
        } else {
            app.bulkEditForm.labels.push(label);
        }
    },

    // Update project labels list
    updateProjectLabels(app) {
        if (!app.currentProject) return;
        
        const allLabels = new Set();
        app.currentProject.vms.forEach(vm => {
            if (vm.labels && Array.isArray(vm.labels)) {
                vm.labels.forEach(label => allLabels.add(label));
            }
        });
        
        app.projectLabels = Array.from(allLabels).sort();
    }
};

// Make VM manager available globally
window.VagrantVMManager = VagrantVMManager;