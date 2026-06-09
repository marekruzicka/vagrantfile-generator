# Changelog

## 🚀 Version 2.0.0 - Multi-User Support & Authentication

**Date:** November 18, 2025

### ✨ Major Features

#### **Dual Deployment Modes**

The application now supports two deployment modes controlled by the `DEPLOYMENT_MODE` environment variable:

- **Self-Hosted Mode** (default): No authentication required, maintains backward compatibility with existing single-user installations. All data stored in `/data/shared/` with unrestricted access.
- **Public Mode**: Full multi-user support with authentication, data isolation, and permission management. Perfect for running as a public service with multiple users.

#### **Hybrid Authentication System**

Public mode supports multiple authentication methods:

- **Email OTP (One-Time Password)**: Users receive a 6-digit code via email (Mailgun integration)
  - Codes valid for 15 minutes
  - Rate limited to 5 requests per hour per email
  - No external OAuth app registration required
- **Social Login (OIDC/OAuth)**: Authenticate using existing accounts
  - Google OAuth integration
  - GitHub OAuth integration
  - GitLab OAuth integration (supports self-hosted instances)
  - Single-click login experience

#### **Complete Data Isolation**

In public mode, users have private workspaces with secure data separation:

- **User-Specific Storage**: Personal resources stored in `/data/users/{user-id}/` directories
- **Shared Resources**: System-provided resources (boxes, plugins, provisioners, triggers) available to all users as read-only templates
- **Permission Enforcement**: Service-layer permission checks prevent unauthorized access
- **Visual Indicators**: UI clearly distinguishes between shared (read-only) and personal (editable) resources with amber borders and badges

### 🏗️ Architecture & Infrastructure

#### **New Backend Services**

- **AuthenticationService**: JWT-based session management with 24-hour token validity
- **OTPService**: One-time password generation, delivery, and verification
- **OIDCService**: OpenID Connect integration for social login providers
- **UserService**: User profile management and persistence
- **PermissionService**: Access control enforcement for multi-user scenarios
- **RateLimitService**: Token bucket algorithm for OTP request rate limiting
- **PreferenceService**: User preferences for shared resources visibility and favorites

#### **Authentication Middleware**

- Automatic authentication enforcement in public mode
- Transparent pass-through in self-hosted mode
- JWT token validation on protected endpoints
- User context injection for all authenticated requests

#### **File Storage Architecture**

```
data/
├── shared/              # System resources (read-only in public mode)
│   ├── boxes/
│   ├── plugins/
│   ├── provisioners/
│   ├── triggers/
│   └── projects/        # Self-hosted mode only
├── users/               # Public mode user data
│   └── {user-id}/
│       ├── boxes/
│       ├── plugins/
│       ├── provisioners/
│       ├── triggers/
│       ├── projects/
│       └── preferences/
└── auth/                # Authentication data
    ├── otp-requests.json
    └── rate-limits.json
```

### 🎨 UI/UX Improvements

#### **Login Experience**

- Clean, modern login page with multiple authentication options
- Real-time email validation
- Clear error messages and feedback
- Automatic session restoration (24-hour validity)
- Redirect to requested page after authentication

#### **Resource Management**

- **Shared Resource Indicators**: Amber borders and "Shared" badges for read-only resources
- **Smart Button Controls**: Edit/delete buttons hidden for shared resources
- **Favorites System**: Star important shared resources to keep them visible
- **Global Toggle**: Hide/show all shared resources with a single switch
- **Copy to Customize**: Create editable personal copies of shared resources

#### **Settings Page Enhancements**

- Shared resources visibility control at the top of Settings page
- Visual distinction between read-only and editable resources
- Star/favorite buttons for quick access to frequently used shared resources
- Copy buttons to create personal editable versions of shared resources

### 🔒 Security Features

#### **Session Management**

- Cryptographically secure JWT tokens (HS256 algorithm)
- User IDs generated as UUID v4 (prevents enumeration attacks)
- HttpOnly recommendations for production deployments
- Automatic session expiration after 24 hours
- Secure token validation on every API request

#### **Rate Limiting**

- OTP request limiting: 5 requests per hour per email address
- Token bucket algorithm with file-based persistence
- Prevents abuse and spam attacks
- Automatic cleanup of expired rate limit records

#### **Permission Model**

| Operation  | Self-Hosted Mode | Public Mode (Shared) | Public Mode (Personal) |
| ---------- | ---------------- | -------------------- | ---------------------- |
| **Read**   | ✅ Full access   | ✅ Read-only         | ✅ Full access         |
| **Create** | ✅ Full access   | ❌ Blocked           | ✅ Full access         |
| **Update** | ✅ Full access   | ❌ Blocked           | ✅ Full access         |
| **Delete** | ✅ Full access   | ❌ Blocked           | ✅ Full access         |
| **Copy**   | N/A              | ✅ Allowed           | N/A                    |

### 📧 Email Integration

#### **Mailgun Support**

- Professional email delivery for OTP codes
- Configurable sender address and domain
- Template-based email formatting
- Delivery tracking and error handling
- Required configuration:
  - `MAILGUN_API_KEY`: Your Mailgun API key
  - `MAILGUN_DOMAIN`: Your verified domain
  - `MAILGUN_FROM_EMAIL`: Sender email address

### 🔧 Configuration

#### **Required Environment Variables**

**For Public Mode:**

```bash
# Deployment
DEPLOYMENT_MODE=public

# JWT Security
JWT_SECRET=your-secret-key-min-32-chars

# URLs
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Email OTP (required)
MAILGUN_API_KEY=key-xxxxx
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com

# Optional: Social Login
OIDC_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
OIDC_GITHUB_CLIENT_ID=Iv1.xxxxx
OIDC_GITHUB_CLIENT_SECRET=xxxxx
OIDC_GITLAB_CLIENT_ID=xxxxx
OIDC_GITLAB_CLIENT_SECRET=xxxxx
OIDC_GITLAB_URL=https://gitlab.com  # Optional, for self-hosted GitLab
```

**For Self-Hosted Mode (backward compatible):**

```bash
# No configuration required - works out of the box
# Optionally set explicitly:
DEPLOYMENT_MODE=self-hosted
```

### 🎯 API Changes

#### **New Endpoints**

**Authentication:**

- `POST /api/auth/otp/request` - Request OTP code
- `POST /api/auth/otp/verify` - Verify OTP code
- `GET /api/auth/oidc/{provider}` - Initiate OIDC flow
- `GET /api/auth/callback/{provider}` - Handle OIDC callback
- `GET /api/auth/me` - Get current user profile
- `GET /api/config/deployment` - Get deployment mode

**Preferences:**

- `GET /api/config/preferences` - Get user preferences
- `PUT /api/config/preferences` - Update preferences
- `GET /api/config/preferences/show-shared` - Get visibility toggle
- `PUT /api/config/preferences/show-shared` - Update visibility
- `POST /api/config/preferences/favorites/{type}/add` - Add favorite
- `POST /api/config/preferences/favorites/{type}/remove` - Remove favorite

**Resource Copying:**

- `POST /api/boxes/{id}/copy` - Copy shared box
- `POST /api/plugins/{id}/copy` - Copy shared plugin
- `POST /api/provisioners/{id}/copy` - Copy shared provisioner
- `POST /api/triggers/{id}/copy` - Copy shared trigger

#### **Response Changes**

All resource endpoints now include ownership metadata in public mode:

```json
{
  "id": "uuid",
  "name": "Resource Name",
  "is_shared": true, // New field
  "owner_id": null // New field (null for shared resources)
  // ... other fields
}
```

### 📦 Database Schema

#### **New Models**

- **UserProfile**: User information (ID, email, name, provider, timestamps)
- **UserPreferences**: User settings (show_shared, favorite lists)
- **OTPRequest**: Temporary OTP codes with expiration
- **RateLimit**: Request tracking for rate limiting
- **Session**: JWT token data and user context

#### **Enhanced Models**

All resource models now include:

- `is_shared`: Boolean flag (true for shared resources)
- `owner_id`: UUID of owner (null for shared resources)
- `source_id`: Reference to original shared resource (for copied resources)

### 🧪 Testing & Quality

#### **Test Coverage**

- Unit tests for authentication services
- Integration tests for multi-user scenarios
- Permission enforcement validation
- Rate limiting verification
- Session management tests
- Email delivery mocking for testing

#### **Backward Compatibility**

- ✅ Existing self-hosted installations work without changes
- ✅ Default mode remains self-hosted (no auth required)
- ✅ Data migration not required for existing users
- ✅ All existing features work identically in self-hosted mode

### 📚 Documentation

New documentation added:

- `docs/AUTHENTICATION.md` - Complete authentication guide
- `docs/SHARED_RESOURCES.md` - Multi-user resource management
- `docs/setup/SETUP_OIDC.md` - OAuth provider configuration
- `docs/setup/SETUP_EMAIL_OTP.md` - Mailgun configuration
- Updated `README.md` with deployment mode instructions

### 🔄 Migration Guide

#### **Upgrading from v1.x to v2.0**

**For Self-Hosted Users:**

1. Pull latest image or update compose file
2. Restart services
3. No configuration changes needed - works exactly as before

**For Public Deployment:**

1. Set `DEPLOYMENT_MODE=public`
2. Configure JWT secret and URLs
3. Set up Mailgun for email OTP
4. Optionally configure OAuth providers
5. Restart services
6. Existing data in `/data/shared/` becomes read-only shared resources

### 🐛 Bug Fixes

- Fixed concurrent write issues with file-based storage using file locking
- Improved error handling for authentication failures
- Enhanced validation for email addresses and OTP codes
- Fixed CORS issues in multi-origin deployments
- Improved session token validation error messages

### ⚡ Performance Improvements

- Optimized resource listing to efficiently merge shared and user resources
- Implemented in-memory caching for OTP and rate limit data with file persistence
- Reduced database queries with smart session token validation
- Improved file I/O with atomic write operations

### 🎨 Visual Changes

- New login page with modern design
- Amber borders and badges for shared resources
- Star icons for favorite resources
- Copy icons for duplicating shared resources
- Toggle switch for shared resources visibility
- Improved empty states and loading indicators

### ⚠️ Breaking Changes

**None for existing users** - The default self-hosted mode maintains full backward compatibility.

For new public deployments, note:

- Authentication is required (cannot be disabled in public mode)
- Mailgun API key is required for email OTP functionality
- JWT secret must be configured for session security

### 🙏 Acknowledgments

This major release enables Vagrantfile Generator to serve both private teams and public users with the same codebase, maintaining simplicity while adding enterprise-grade multi-user capabilities.

---

## Version 1.12.2

**Date:** November 12, 2025

### 🐛 Bug Fixes

- **Fixed copy-to-clipboard button**: Added the missing javascript to actually copy to content of the generated Vagrantfile to clipboard.

### 🔧 Run app as non-root user

- **Update Dockerfiles to run as appuser**: Updated "prod" version of apps (both frontend, and backend) to run as non-root.
  Dev version of frontend was not changed to keep possible troubleshooting simple. There is only single version of backend, so it is running as non-root also in dev.

---

## Version 1.12.1

**Date:** October 4, 2025

### 🎨 UI / UX Improvements

- **Add example user data**: Added bunch of boxes, few plugins, triggers, and provisioners to streamline your inital experience.

---

## Version 1.12.0

**Date:** October 4, 2025

### 🎨 UI / UX Improvements

- **Standardized "Add Triggers to Project" modal styling**: Updated the Add Triggers modal to match the look-and-feel of the Plugins and Provisioners multi-select modals. Changes include unified icon sizing, item list container, typography, badge styles, and consistent hover/selection behavior to improve visual parity across project-level add-modals.

### 🐛 Bug Fixes

- **Fixed trigger creation from Project Detail**: Resolved an HTML5 validation issue that prevented creating a new trigger when launched from the Project Detail "Add Triggers to Project" modal. The command textareas now use conditional `required` bindings so only the visible input is validated.

### 🔧 Multi env container configuration

**Dev:**

- Browser loads assets from Vite dev server (localhost:5173), which can proxy /api to backend via Vite proxy.
- CORS is often handled by Vite proxy so backend sees requests from Vite (same origin), reducing CORS errors.
- The runtime config can point to localhost backend or the proxied /api base; env separation (internal vs browser API URLs) prevents accidental cross-origin calls.
- Backend Process: uvicorn with --reload (single process, auto-reload for code changes).
  - `uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload`

**Prod:**

- Browser loads static files from Nginx (FE_LISTEN_URL hostname).
- Nginx proxies /api to backend (single origin as far as browser sees it) — backend receives requests from nginx proxied path, and CORS remains simple because the browser origin is the FE_LISTEN_URL.
- Nginx rejects unknown hostnames via the default_server 444.
- Backend Process: gunicorn with Uvicorn worker class (multiple workers).
  - `gunicorn -k uvicorn.workers.UvicornWorker src.main:app -b 0.0.0.0:8000 --workers 4`

---

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
