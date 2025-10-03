# Changelog

## Version 1.11.0
**Date:** October 3, 2025

### ✨ New Features
- **Bulk Edit — add network configuration**: You can now add full network interface configurations when bulk editing VMs. The Bulk Edit modal lets you add private/public networks and port forwarding entries that will be applied to all selected VMs. Supported fields include IP assignment (DHCP or static), IP address, netmask, bridge interface, and host/guest ports for forwarded ports.

### 🎨 UI / UX Improvements
- **Bulk Edit VMs modal restyle**: Unified the Bulk Edit modal UI with the Bulk Create modal. The modal now uses a white background, a blue info notification showing the number and names of VMs being edited, and VM name badges for clearer context.
- **Network Interface UX parity**: The Bulk Edit network interface form now matches the single-VM creation/edit flows (consistent inputs for private/public network options and port forwarding), including clearer controls for adding/removing interfaces.
- **Form behavior fixes**: Added `novalidate` to forms where necessary and cleaned up stray markup that previously broke modal layouts.

### 🐛 Bug Fixes
- **Network interface validation**: Backend/front-end validation was hardened by deleting unused optional fields instead of setting them to null, preventing spurious validation errors for network interface payloads.
- **Bulk Edit reliability**: Fixed remaining Bulk Edit issues — box selection now uses a dropdown populated from configured boxes, form validation issues resolved, and markup fixes to ensure the modal renders and submits reliably.

### 🔧 Technical Notes
- The bulk-edit network feature reuses existing utilities for IP handling. An optional IP incrementing helper is available and used when applying a base static IP across multiple VMs, but the primary new feature is the ability to add network interfaces in bulk — IP incrementing is an implementation detail, not the headline feature.

---

## Version 1.10.3
**Date:** October 3, 2025

### 🐛 Bug Fixes
- **Fixed Bulk Edit VMs - Box selection**: Replaced the free-form box input in the Bulk Edit VMs modal with a dropdown menu populated from configured boxes. This fixes cases where bulk edits failed or applied invalid box names; selecting a box now applies the value to all selected VMs.

---

## Version 1.10.2 - Trigger bulk-delete & modal fixes
**Date:** October 3, 2025

### 🐛 Bug Fixes
- **Fixed Bulk Delete for Triggers on Project Detail page**: Resolved an issue where the Bulk Delete confirmation modal invoked a non-existent handler, preventing the removal of selected triggers. The modal now calls the existing `bulkDeleteTriggers()` method which removes the selected triggers and refreshes the project view.
- **Fixed Delete Modal Positioning**: The trigger delete / bulk-delete modals opened too high on some viewports. Updated modal markup to use the shared `modal-overlay` / `modal-content` pattern so modals are centered and consistent with other confirmation dialogs.

### 🎨 UI/UX Improvements
- Standardized bulk-delete modal layout to match other bulk-delete dialogs (plugins/provisioners): improved spacing, iconography and action layout for a clearer confirmation flow.
- Improved user feedback: the UI closes the modal on success and shows a success notification indicating how many triggers were removed.

### 🔧 Technical Notes
- Files changed (frontend): `frontend/src/modals/bulk-delete-triggers.html`, minor JS wiring to use existing `bulkDeleteTriggers()` method. No backend API changes required.

---

## Version 1.10.1 - Plugin Handling Fix
**Date:** October 3, 2025

### 🐛 Bug Fixes
- **Fixed Critical Plugin Installation Bug**: Resolved "Invalid type provided for `plugins`" error in generated Vagrantfiles
  - Moved plugin installation code outside `Vagrant.configure("2")` block where it belongs
  - Replaced invalid `config.vagrant.plugins = [...]` assignment with proper Ruby plugin installation loop
  - Added support for `--plugin-version` flag when specific plugin versions are configured
  - Implemented error handling for failed plugin installations with user feedback
  - Plugin installation now occurs before Vagrant configuration parsing as required

### 🔧 Technical Improvements
- **Enhanced Vagrantfile Template**: Improved plugin handling with proper Ruby syntax and command construction
- **Better Error Handling**: Added fallback messaging when plugin installation fails
- **Version Support**: Full support for plugin version constraints in generated Vagrantfiles

---

## 🎨 Version 1.10.0 - UI/UX Improvements & Collapsible Sections
**Date:** October 3, 2025

### ✨ New Features
- **Collapsible Sections**: Improved content organization and navigation
  - All major sections (Plugins, Provisioners, Triggers, VMs) can now be collapsed/expanded
  - Toggle sections by clicking either the chevron icon or the section name
  - Smooth expand/collapse transitions with visual feedback
  - State management ensures sections remember their open/closed state during session
  - Consistent chevron indicators that rotate 180° when collapsed
  - Available on both Project Detail and Settings pages (8 collapsible sections total)

- **Enhanced Main Page Layout**: More compact and efficient use of screen space
  - Reduced header padding and spacing for less whitespace
  - Added global statistics cards showing total Plugins, Provisioners, and Triggers
  - Implemented 6-column responsive grid layout for statistics cards
  - Cards automatically adjust to 2 columns on mobile, 3 on tablet, 6 on desktop
  - All stat cards unified with consistent 134px height without secondary text
  - "Ready to Deploy" card repositioned to the end for better visual flow

- **Improved Visual Design**: Consistent styling and better user feedback
  - Standardized chevron sizes across all sections (w-5 h-5)
  - Color-matched gradient icons from Settings page to main dashboard
  - Added hover effects on section titles with cursor pointer feedback
  - Consistent button styling and positioning across modals
  - Enhanced empty state messages with appropriate icons

### 🎨 UI/UX Improvements
- **Better Interaction Design**: More intuitive and accessible controls
  - Section headers are now fully clickable, not just the chevron buttons
  - Hover states provide clear visual feedback on interactive elements
  - Reduced visual clutter by removing unnecessary subtitle text from cards
  - Progressive disclosure pattern improves navigation with large datasets

- **Modal Enhancements**: Standardized and improved modal experiences
  - Trigger modal now uses checkmark icon instead of plus sign (consistent with other modals)
  - Enhanced empty states with X icons for better visual communication
  - Improved button consistency across all modals

- **Responsive Grid System**: Optimal display across all device sizes
  - Mobile: 2-column grid for compact display
  - Tablet: 3-column grid for balanced layout
  - Desktop: 6-column grid for maximum information density
  - All cards maintain equal height for clean visual alignment

### 🐛 Bug Fixes
- Fixed inconsistent chevron sizes between sections
- Standardized icon styling across Project Detail and Settings pages
- Improved spacing consistency throughout the application
- Fixed card alignment issues in statistics grid

---

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