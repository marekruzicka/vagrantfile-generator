// Vagrantfile GUI Generator - Main Application Logic
import Alpine from 'alpinejs'
import { VagrantAPI } from './services/api.js'

// Initialize API client
const api = new VagrantAPI()

// Main application state and methods
function vagrantApp() {
  return {
    // State
    projects: [],
    currentProject: null,
    currentView: 'projects', // projects, project-detail
    isLoading: false,
    error: null,
    
    // Modal states
    showCreateProjectModal: false,
    showCreateVMModal: false,
    showVagrantfileModal: false,
    showDeleteConfirmModal: false,
    deleteTarget: null,
    
    // Form data
    newProject: {
      name: '',
      description: ''
    },
    newVM: {
      name: '',
      box: 'ubuntu/jammy64',
      memory: 1024,
      cpus: 1,
      forwarded_ports: [],
      synced_folders: [],
      private_networks: []
    },
    
    // Generated Vagrantfile content
    vagrantfileContent: '',
    
    // Initialization
    async init() {
      await this.loadProjects()
    },
    
    // Project Management
    async loadProjects() {
      this.setLoading(true)
      try {
        this.projects = await api.getProjects()
        this.clearError()
      } catch (error) {
        this.setError('Failed to load projects: ' + error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    async createProject() {
      if (!this.newProject.name) {
        this.setError('Project name is required')
        return
      }
      
      this.setLoading(true)
      try {
        const project = await api.createProject(this.newProject)
        this.projects.push(project)
        this.resetNewProject()
        this.showCreateProjectModal = false
        this.clearError()
      } catch (error) {
        this.setError('Failed to create project: ' + error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    async deleteProject(projectId) {
      this.setLoading(true)
      try {
        await api.deleteProject(projectId)
        this.projects = this.projects.filter(p => p.id !== projectId)
        if (this.currentProject && this.currentProject.id === projectId) {
          this.currentProject = null
          this.currentView = 'projects'
        }
        this.clearError()
      } catch (error) {
        this.setError('Failed to delete project: ' + error.message)
      } finally {
        this.setLoading(false)
        this.showDeleteConfirmModal = false
        this.deleteTarget = null
      }
    },
    
    async loadProject(projectId) {
      this.setLoading(true)
      try {
        this.currentProject = await api.getProject(projectId)
        this.currentView = 'project-detail'
        this.clearError()
      } catch (error) {
        this.setError('Failed to load project: ' + error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    // VM Management
    async createVM() {
      if (!this.newVM.name || !this.currentProject) {
        this.setError('VM name is required')
        return
      }
      
      this.setLoading(true)
      try {
        const vm = await api.createVM(this.currentProject.id, this.newVM)
        this.currentProject.vms.push(vm)
        this.resetNewVM()
        this.showCreateVMModal = false
        this.clearError()
      } catch (error) {
        this.setError('Failed to create VM: ' + error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    async deleteVM(vmId) {
      this.setLoading(true)
      try {
        await api.deleteVM(this.currentProject.id, vmId)
        this.currentProject.vms = this.currentProject.vms.filter(vm => vm.id !== vmId)
        this.clearError()
      } catch (error) {
        this.setError('Failed to delete VM: ' + error.message)
      } finally {
        this.setLoading(false)
        this.showDeleteConfirmModal = false
        this.deleteTarget = null
      }
    },
    
    // Vagrantfile Generation
    async generateVagrantfile() {
      if (!this.currentProject) return
      
      this.setLoading(true)
      try {
        const response = await api.generateVagrantfile(this.currentProject.id)
        this.vagrantfileContent = response.content
        this.showVagrantfileModal = true
        this.clearError()
      } catch (error) {
        this.setError('Failed to generate Vagrantfile: ' + error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    async downloadVagrantfile() {
      if (!this.currentProject) return
      
      try {
        await api.downloadVagrantfile(this.currentProject.id)
        this.clearError()
      } catch (error) {
        this.setError('Failed to download Vagrantfile: ' + error.message)
      }
    },
    
    // Port Management
    addForwardedPort() {
      this.newVM.forwarded_ports.push({
        guest: '',
        host: '',
        protocol: 'tcp'
      })
    },
    
    removeForwardedPort(index) {
      this.newVM.forwarded_ports.splice(index, 1)
    },
    
    // Synced Folder Management
    addSyncedFolder() {
      this.newVM.synced_folders.push({
        host_path: '',
        guest_path: '',
        type: 'virtualbox'
      })
    },
    
    removeSyncedFolder(index) {
      this.newVM.synced_folders.splice(index, 1)
    },
    
    // Network Management
    addPrivateNetwork() {
      this.newVM.private_networks.push({
        ip: '',
        netmask: '255.255.255.0'
      })
    },
    
    removePrivateNetwork(index) {
      this.newVM.private_networks.splice(index, 1)
    },
    
    // Modal Management
    openCreateProjectModal() {
      this.resetNewProject()
      this.showCreateProjectModal = true
    },
    
    openCreateVMModal() {
      this.resetNewVM()
      this.showCreateVMModal = true
    },
    
    openDeleteConfirmModal(target, type) {
      this.deleteTarget = { ...target, type }
      this.showDeleteConfirmModal = true
    },
    
    closeDeleteConfirmModal() {
      this.showDeleteConfirmModal = false
      this.deleteTarget = null
    },
    
    async confirmDelete() {
      if (!this.deleteTarget) return
      
      if (this.deleteTarget.type === 'project') {
        await this.deleteProject(this.deleteTarget.id)
      } else if (this.deleteTarget.type === 'vm') {
        await this.deleteVM(this.deleteTarget.id)
      }
    },
    
    // View Management
    showProjects() {
      this.currentView = 'projects'
      this.currentProject = null
    },
    
    // Form Helpers
    resetNewProject() {
      this.newProject = {
        name: '',
        description: ''
      }
    },
    
    resetNewVM() {
      this.newVM = {
        name: '',
        box: 'ubuntu/jammy64',
        memory: 1024,
        cpus: 1,
        forwarded_ports: [],
        synced_folders: [],
        private_networks: []
      }
    },
    
    // Utility Methods
    setLoading(loading) {
      this.isLoading = loading
    },
    
    setError(error) {
      this.error = error
      console.error('Application error:', error)
    },
    
    clearError() {
      this.error = null
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString()
    },
    
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied to clipboard')
      }).catch(err => {
        console.error('Failed to copy to clipboard:', err)
      })
    }
  }
}

// Make vagrantApp available globally before Alpine starts
window.vagrantApp = vagrantApp

// Make Alpine available globally
window.Alpine = Alpine

// Start Alpine.js
Alpine.start()

console.log('Vagrantfile GUI Generator initialized')