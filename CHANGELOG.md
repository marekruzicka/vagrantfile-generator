# Changelog

## 🚀 Version 1.9.0 - Provisioner Management System
**Date:** October 2, 2025

### ✨ New Features
- **Global Provisioner Management**: Add and configure Vagrant provisioners for your projects
  - Manage shell provisioners through the Settings page
  - Add, edit, and delete provisioner configurations
  - Configure shell scripts, privilege levels, and run modes (once/always)
  - Support for inline scripts and script paths
  - View provisioner descriptions and details

- **Project-Level Provisioner Configuration**: Assign provisioners to individual projects
  - Add multiple provisioners to any project from the project detail page
  - Multiselect modal with checkbox-based selection for adding multiple provisioners at once
  - Visual provisioner cards showing name, type, and description
  - Bulk selection and deletion of provisioners
  - Edit provisioners directly from the project detail page
  - Smart filtering: only shows provisioners not yet added to the project
  - Simple empty state when no provisioners are configured
  - Provisioners are organized in the Settings page, separate from plugins

- **Enhanced Plugin Management**: Improved plugin workflow and UX
  - **Smart Filtering**: Plugin modal now only shows plugins not yet added to the project
  - **Edit from Project Detail**: Edit plugins directly from the project detail page without navigating away
  - **Improved Error Handling**: Better feedback when plugins already exist or fail to add
  - **Empty States**: Clear messages when all plugins are added or none are available
  - **Context-Aware Modals**: Edit modals stay on the current page instead of navigating to Settings

- **Enhanced Vagrantfile Generation**: Generated Vagrantfiles now include provisioner configurations
  - Provisioners are automatically added to the Vagrant configuration
  - Proper Ruby syntax with shell script blocks
  - Support for privileged and non-privileged execution
  - Run mode configuration (once/always)

### 🎨 UI/UX Improvements
- **Consistent Modal Design**: Plugin and provisioner modals now have the same look and feel
- **Multiselect Capability**: Both plugins and provisioners support selecting multiple items at once
- **Better Visual Feedback**: Selected items are highlighted with blue rings
- **Green Action Buttons**: Primary actions (Add Plugin, Add Provisioner) now use green buttons for consistency
- **Hover-Based Actions**: Edit and delete buttons appear on hover for cleaner interface
- **Selection Counters**: Real-time feedback showing how many items are selected
- **Bulk Operations**: Select All, Clear Selection, and Bulk Delete buttons for efficient management

### 🐛 Bug Fixes
- Fixed plugin addition error when plugins already exist in project
- Fixed provisioner modal displaying only provisioners not yet in the project
- Fixed edit modals navigating away from current page
- Improved error messages for better user feedback
- Fixed selection state persistence across modal operations

---

## 🚀 Version 1.8.0 - Plugin Management System
**Date:** October 1, 2025

### ✨ New Features
- **Global Plugin Management**: Add and configure Vagrant plugins for your projects
  - Manage plugins through the Settings page
  - Add, edit, and delete plugin configurations
  - Set default versions and mark deprecated plugins
  - View plugin descriptions and details

- **Project-Level Plugin Configuration**: Assign plugins to individual projects
  - Add multiple plugins to any project from the project detail page
  - Visual plugin cards showing name, version, and status
  - Bulk selection and deletion of plugins
  - Active/Deprecated status badges for easy identification
  - Simple empty state when no plugins are configured

- **Enhanced Vagrantfile Generation**: Generated Vagrantfiles now include plugin configurations
  - Plugins are automatically added to the Vagrant configuration
  - Version constraints are respected
  - Proper Ruby syntax with color-coded highlighting in preview modal

- **Improved Code Display**: Vagrantfile preview now features professional syntax highlighting
  - Ruby syntax highlighting with multiple colors
  - Better readability with dark theme
  - Clear distinction between comments, keywords, and strings

### � Bug Fixes
- Fixed plugin status display to correctly show Active/Deprecated state
- Fixed version validation to accept various semantic version formats (including 'v' prefix)
- Improved plugin state synchronization when adding or removing plugins

---

## 🚀 Version 1.7.0 - Dynamic Footer & Documentation
**Date:** September 25, 2025

### ✨ New Features
- **Configurable Footer**: View changelog, documentation, and external links from the footer
  - Click footer links to view content in a modal window
  - External links open in new tabs automatically
  - Markdown documents displayed with proper formatting

- **Modal Content System**: View documentation and release notes without leaving the app
  - Responsive modals that work on all screen sizes
  - Markdown support for rich text formatting
  - Clean, readable typography

### � Bug Fixes
- Fixed header duplication in markdown documents
- Improved code block styling in documentation
- Enhanced link rendering with better visual feedback

---

## 🏗️ Version 1.6.0 - Improved Project Management
**Date:** December 20, 2024

### ✨ Improvements
- **Better Project List Updates**: Projects now appear immediately when created or deleted
- **Smarter Filtering**: The app correctly shows different messages when no projects exist vs. when filters exclude all projects
- **Cleaner Project Headers**: VM counts, status badges, and action buttons are now properly positioned

### 🐛 Bug Fixes
- Fixed project creation - new projects appear instantly without refreshing
- Fixed project deletion - app shows welcome screen when all projects are deleted
- Fixed empty state messages to be more accurate and helpful
- Fixed project detail page layout issues

---

## 🏗️ Version 1.5.0 - Performance & Code Organization
**Date:** September 24, 2025

### ✨ Improvements
- **Faster Loading**: Application loads more quickly with optimized code structure
- **Better Responsiveness**: Smoother interactions and modal displays
- **Improved Reliability**: More stable application with better error handling

### 🐛 Bug Fixes
- Fixed VM count display accuracy across the application
- Fixed modal overlapping and display issues
- Improved empty state messages and filter UI
- Fixed project statistics calculations

---

## 🏗️ Version 1.4.0 - Network Interface Validation
**Date:** September 24, 2025

### 🐛 Bug Fixes
- **Better Error Messages**: Clear error messages now appear when network interface configuration is invalid
- **Fixed Validation Issues**: Invalid changes are properly rejected and don't appear on VM cards
- **Improved IP Address Validation**: Visual feedback (red borders) when IP addresses are invalid
- **Port Forwarding Validation**: Better error handling for host and guest port configurations

---

## 🚀 Version 1.3.0 - Network Configuration Enhancements  
**Date:** September 24, 2025

### ✨ New Features
- **Netmask Support**: Configure custom netmasks for network interfaces
- **Better Network Display**: VM cards now show full network configuration including netmask (e.g., "Static: 192.168.1.100/255.255.255.128")
- **Complete Vagrantfiles**: Generated Vagrantfiles now include netmask settings when specified

### � Bug Fixes  
- Fixed netmask values not appearing in generated Vagrantfiles
- Fixed network configuration display on VM cards

---

## 🚀 Version 1.2.0 - Configuration Improvements
**Date:** September 24, 2025

### ✨ Improvements
- **Simplified Setup**: Easier configuration with streamlined docker-compose setup
- **Better Network Validation**: More flexible network configuration options

### 🐛 Bug Fixes
- Fixed API connection issues
- Fixed host access problems
- Improved configuration documentation

---

## 📦 Version 1.1.0 - Box Management
**Date:** September 23, 2025

### ✨ New Features
- **Box Management**: Add, edit, and delete Vagrant boxes through the Settings page
- **Visual Box Cards**: See all your configured boxes at a glance
- **Box Details**: Configure box versions, custom URLs, and providers (libvirt, VirtualBox, VMware, Hyper-V)
- **Smart Validation**: Prevents duplicate box names and validates all fields

### 🐛 Bug Fixes
- Fixed box dropdown showing "[object Object]" - now displays readable box names
- Fixed Settings page loading issues
- Fixed editing of optional fields (version and URL)

---

## 🚀 Version 1.0.0 - Initial Release
**Date:** September 23, 2025

### ✨ Features
- **Project Management**: Create, edit, and delete Vagrant projects
- **Virtual Machine Configuration**: Add and configure multiple VMs per project
- **Network Setup**: Configure network interfaces with static or DHCP addresses
- **Vagrantfile Generation**: Generate ready-to-use Vagrantfiles from your configurations
- **Status Management**: Track project status (Draft/Ready)

### 🐛 Bug Fixes
- Fixed project deletion not working
- Fixed VM count always showing "0"
- Fixed VM counts not updating after changes
- Improved delete confirmations with clear messages
- Added success/error notifications for all operations
- Better visual feedback during loading

---

## 📋 Summary

Vagrantfile Generator is a web-based GUI tool for creating and managing Vagrant development environments. It provides an intuitive interface for:

- **Managing Projects**: Organize your Vagrant environments into projects
- **Configuring Virtual Machines**: Set up multiple VMs with custom resources, networking, and providers
- **Plugin Management**: Configure and apply Vagrant plugins globally or per-project
- **Box Management**: Add and manage Vagrant boxes with version control
- **Network Configuration**: Set up complex network topologies with static IPs, DHCP, and port forwarding
- **Vagrantfile Generation**: Automatically generate production-ready Vagrantfiles with syntax highlighting

Each release focuses on improving usability, fixing bugs, and adding features based on user needs.