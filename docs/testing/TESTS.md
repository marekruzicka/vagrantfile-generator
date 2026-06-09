# User-Based Test Plan

This document defines end-to-end tests from a user's point of view. Tests should interact with the running application through a browser only (for example with Playwright), not by calling internal code directly.

## Scope and Assumptions

- Application under test: Vagrantfile Generator web UI.
- Primary URL examples:
  - Self-hosted/local: `http://localhost:8080` or `http://localhost:5173`
  - Public deployment: deployed hostname such as `http://vgf.i.glide.sk`
- User tests may validate generated Vagrantfile text, visible UI state, notifications, browser redirects, and persistence after reload/re-login.
- API calls may be observed in DevTools/network logs, but test actions should be performed through the UI.
- Public-mode authentication tests require configured Mailgun and/or OAuth providers.

## 1. Authentication and Deployment Modes

### 1.1 Self-hosted mode has no login gate
**Given** the app runs in self-hosted mode or with `DEPLOYMENT_MODE` unset  
**When** a user opens the application URL  
**Then** the Projects page is shown without a login page.

### 1.2 Public mode redirects unauthenticated users to login
**Given** the app runs in public mode  
**When** an unauthenticated user opens the application URL  
**Then** the Login page is shown with email OTP input and Google/GitHub/GitLab buttons.

### 1.3 Email OTP login happy path
**Given** public mode with email OTP configured  
**When** the user enters a valid email, clicks “Send Login Code”, receives the code, and submits it  
**Then** the user is redirected to the main Projects page and can use the app.

### 1.4 Email OTP validation and rate-limit UX
Test invalid email, incorrect OTP, expired OTP, repeated OTP requests, and resend behavior. The user should receive clear errors and should not gain access until a valid code is provided.

### 1.5 OAuth login providers
For Google, GitHub, and GitLab where configured: clicking “Continue with …” should redirect to the provider, complete consent/login, return to the app, and show the Projects page as an authenticated user.

### 1.6 Session persistence and logout
After login, reload the page and reopen the browser within the session lifetime; the user should remain logged in. After logout or token expiry, opening the app should show the login page again.

## 2. Projects Dashboard

### 2.1 Empty first-run experience
**Given** the user has no projects  
**When** they open the Projects page  
**Then** the empty state explains the create-project workflow and shows “Create Your First Project”.

### 2.2 Create project
Create a project with name and description. Verify it appears immediately as a project card with Draft status and correct stats.

### 2.3 Project list stats and filters
With multiple Draft and Ready projects, verify dashboard stat cards and filters: All, Draft, Ready. Empty filtered states should explain that no projects match the selected filter.

### 2.4 Open project detail
Click a project card. Verify the detail page shows project name, description, VM count, status badge, and sections for Plugins, Provisioners, Triggers, and VMs.

### 2.5 Delete draft project
Delete a Draft project from the dashboard and confirm it disappears after confirmation. Verify canceling the confirmation leaves the project intact.

### 2.6 Ready project protection
Mark a project Ready. Verify it is visually highlighted/marked Ready and destructive or editing actions are disabled/hidden where expected. Switch back to Draft and verify editing resumes.

## 3. Virtual Machines

### 3.1 Add a single VM
In a Draft project, add a VM with name, box, hostname, memory, CPUs, and labels. Verify the VM card displays the configuration and the project VM count updates.

### 3.2 Required-field and resource validation
Try creating/editing a VM with missing name/box, invalid memory, invalid CPU count, or duplicate VM name. Verify inline validation and no invalid VM is saved.

### 3.3 Bulk create VMs
Set Count greater than 1. Verify the previewed names use the expected suffix pattern and all VMs are created with unique names and shared base settings.

### 3.4 Edit VM
Edit VM name, box, hostname, memory, CPUs, labels, and networks. Save and verify values persist after page reload.

### 3.5 Delete VM
Delete a VM and verify the card and VM count update. Canceling delete should leave the VM unchanged.

### 3.6 VM labels and selection
Create VMs with labels. Use label quick selection and manual checkboxes to select VMs. Verify selection counters, select-all, clear-selection, and label-based selection behavior.

### 3.7 Bulk edit VMs
Select multiple VMs and bulk-edit memory, CPUs, box, labels, and network interfaces. Verify all selected VMs are updated and unselected VMs are unchanged.

### 3.8 Bulk delete VMs
Select multiple VMs, bulk delete, confirm, and verify only selected VMs are removed.

## 4. Networking

### 4.1 Private network with DHCP
Add a private network interface using DHCP. Verify the VM card and generated Vagrantfile reflect a private network without static IP.

### 4.2 Private network with static IP and netmask
Add a private network with static IP and netmask. Verify validation accepts private ranges and generated Vagrantfile includes IP and netmask.

### 4.3 Public network
Add a public network with and without bridge interface. Verify display and generated Vagrantfile are correct.

### 4.4 Port forwarding
Add forwarded port mappings with host port, guest port, and TCP/UDP protocol. Verify invalid port ranges are rejected and valid mappings appear in generated output.

### 4.5 Bulk IP incrementing
Bulk-create or bulk-edit multiple VMs with a static base IP. Verify subsequent VMs receive incremented IP addresses and out-of-range IP warnings are shown when applicable.

### 4.6 Public IP validation setting
With “Allow public IPs in private networks” disabled, try a public static IP in private network and verify validation error. Enable the setting and verify the same IP is accepted.

## 5. Global Settings: Boxes

### 5.1 View box catalog
Open Settings → Vagrant Boxes. Verify boxes list with name, provider, description, version/URL where available, count badge, and refresh button.

### 5.2 Create box
Add a box with name, description, provider, optional version, and optional URL. Verify it appears in Settings and in VM box dropdowns.

### 5.3 Edit box
Edit a user-owned box and verify updated values persist after refresh.

### 5.4 Delete box
Delete a user-owned box and verify it is removed from Settings and no longer appears in VM creation dropdowns.

### 5.5 Duplicate/invalid box validation
Attempt duplicate names or invalid required fields. Verify the user sees a clear error and the invalid box is not saved.

## 6. Global Settings: Plugins

### 6.1 View plugin catalog
Open Settings → Plugins. Verify plugin cards show name, description, default version, source/documentation info where available, and Active/Deprecated status.

### 6.2 Create plugin
Add a plugin with name, description, source URL, documentation URL, default version, configuration, and deprecated flag. Verify it appears in Settings and project plugin selection.

### 6.3 Edit plugin
Edit plugin metadata and deprecated status. Verify changes appear in Settings and on projects using the plugin.

### 6.4 Delete plugin
Delete a user-owned plugin and verify it is removed from project selection. If already assigned to a project, verify the app handles the missing/deleted plugin gracefully.

### 6.5 Plugin version validation
Test common version formats and invalid values. Verify accepted versions are saved and invalid versions show errors.

## 7. Project Plugins

### 7.1 Add plugins to project
From Project Detail → Plugins, open Add Plugin, select one or multiple plugins, and save. Verify plugin cards appear on the project.

### 7.2 Add-plugin filtering
Verify the Add Plugin modal only shows plugins not already assigned to the project, and shows a helpful empty state when all plugins are already added.

### 7.3 Edit project plugin
Edit a plugin from Project Detail. Verify version/configuration changes save and generated Vagrantfile includes plugin installation/version details.

### 7.4 Remove project plugin
Remove one plugin from a project. Verify it disappears from the project but remains available globally in Settings.

### 7.5 Bulk remove project plugins
Select multiple project plugins, use Bulk Delete, confirm, and verify selected plugins are removed.

## 8. Global Settings: Provisioners

### 8.1 View provisioner catalog
Open Settings → Provisioners. Verify provisioner cards show name, description, type, privilege, run mode, and script/path summary.

### 8.2 Create shell provisioner
Create a shell provisioner with inline script or path, privileged true/false, and run mode once/always/never as available. Verify it appears in Settings and project selection.

### 8.3 Edit provisioner
Edit script, path, privilege, and run mode. Verify updates persist and are reflected in generated Vagrantfile for projects using it.

### 8.4 Delete provisioner
Delete a user-owned provisioner and verify it is removed from Settings and project selection.

## 9. Project Provisioners

### 9.1 Add provisioners to project
From Project Detail → Provisioners, select one or multiple provisioners and add them. Verify project provisioner cards appear.

### 9.2 Add-provisioner filtering
Verify only provisioners not already assigned are offered, with a useful empty state when none are available.

### 9.3 Remove and bulk remove project provisioners
Remove one provisioner and then bulk-remove several. Verify global provisioner templates remain available in Settings.

## 10. Global Settings: Triggers

### 10.1 View trigger catalog
Open Settings → Triggers. Verify trigger cards show name, description, timing, stage, execution target, and on-error behavior.

### 10.2 Create host trigger
Create a trigger with timing, stage, host `run` command, info/warn text, and on-error option. Verify it appears in Settings and project selection.

### 10.3 Create remote trigger
Create a trigger using remote inline command. Verify validation requires a command for the selected target and does not require the hidden command field.

### 10.4 Edit trigger
Edit timing, stage, target command, messages, and on-error behavior. Verify changes persist.

### 10.5 Delete trigger
Delete a user-owned trigger and verify it disappears from Settings and project selection.

## 11. Project Triggers

### 11.1 Add triggers to project
From Project Detail → Triggers, select one or multiple triggers and add them. Verify trigger cards appear on the project.

### 11.2 Search and filtering in trigger modal
Use trigger search in the Add Triggers modal. Verify matching triggers are shown and non-matching triggers are hidden.

### 11.3 Remove and bulk remove project triggers
Remove a single trigger and bulk-remove selected triggers. Verify templates remain available in Settings.

## 12. Shared Resources and Multi-User Isolation

### 12.1 Shared resource visual indicators
In public mode with shared resources, verify shared boxes/plugins/provisioners/triggers/projects have amber visual styling and a “Shared” badge.

### 12.2 Shared resources are read-only
For shared resources, verify edit/delete buttons are hidden or disabled. Attempts to modify via visible UI paths should fail gracefully with permission feedback.

### 12.3 Copy shared resource to personal resource
Use “Copy to My Resources” on a shared box/plugin/provisioner/trigger. Verify a personal editable copy appears, without modifying the original shared item.

### 12.4 Favorite shared resources
Star/unstar shared resources. Verify favorite state persists after reload and is independent per resource type.

### 12.5 Hide/show shared resources
Toggle Shared Resources visibility in Settings. Verify shared items hide/show across boxes, plugins, provisioners, and triggers while personal items remain visible.

### 12.6 Two-user data isolation
Login as Alice and create projects/resources. Login as Bob in a separate session and verify Bob cannot see Alice's personal projects/resources, but both users can see shared resources.

### 12.7 Shared resource usage in projects
Add shared resources to a personal project. Verify the project can use them and generated Vagrantfile includes them, while the original shared resources remain read-only.

## 13. Generated Vagrantfile

### 13.1 Generate simple Vagrantfile
Create a project with one VM and generate/preview the Vagrantfile. Verify syntax includes `Vagrant.configure`, VM name, box, hostname, memory, and CPU settings.

### 13.2 Generate multi-VM Vagrantfile
Create multiple VMs with different resources and networks. Verify each VM is represented correctly.

### 13.3 Generate with plugins
Add plugins with versions. Verify plugin installation code appears before/appropriately outside the Vagrant configuration block and includes version constraints where set.

### 13.4 Generate with provisioners
Add shell provisioners. Verify generated Ruby includes expected shell provisioner blocks, privilege settings, run mode, inline scripts, or paths.

### 13.5 Generate with triggers
Add host and remote triggers. Verify timing, stage, messages, commands, and on-error behavior appear correctly.

### 13.6 Copy/download generated content
Use the copy-to-clipboard action in the generated Vagrantfile preview. Verify clipboard content matches the displayed Vagrantfile.

### 13.7 Generation validation
Attempt to generate a Vagrantfile for a project with no VMs or invalid configuration. Verify the user receives a clear error and no invalid output is presented as ready.

## 14. Global Application Settings

### 14.1 Network validation settings persistence
Change max CPUs, max memory, min memory, memory step, and public-IP allowance where exposed. Reload the page and verify settings persist and affect VM forms/validation.

### 14.2 Collapsible sections
On Project Detail and Settings, collapse and expand Plugins, Provisioners, Triggers, VMs, Boxes, and other sections. Verify content hides/shows and controls in collapsed sections are not accidentally actionable.

### 14.3 Refresh actions
Use refresh buttons for resources. Verify lists reload without duplicating entries or losing user selections unexpectedly.

## 15. Footer, Documentation, and Error UX

### 15.1 Footer links
Click footer links for changelog/documentation. Verify internal markdown opens in a readable modal and external links open in a new tab.

### 15.2 Notifications
For successful create/edit/delete/copy operations, verify success notifications are shown. For validation/API errors, verify error notifications are clear and dismissible.

### 15.3 API/backend unavailable state
Stop or block the backend while the frontend is open. Verify the app shows a usable error state and recovers after backend availability returns and the user refreshes/retries.

### 15.4 Not-found/error page
Navigate to an invalid app route or cause a handled application error. Verify a user-friendly error page/component is displayed.

## 16. Responsiveness and Browser Compatibility

### 16.1 Desktop layout
Verify Projects, Project Detail, Settings grids, modals, and generated Vagrantfile preview are usable at common desktop widths.

### 16.2 Tablet layout
Verify cards, filters, section headers, and modals remain usable on tablet-sized viewports.

### 16.3 Mobile layout
Verify login, project list, VM forms, settings cards, modals, and action buttons are accessible on mobile widths without horizontal scrolling or hidden required actions.

### 16.4 Keyboard accessibility smoke test
Use Tab/Shift+Tab/Enter/Escape through login, main navigation, forms, modals, and confirmations. Verify focus is visible and modal close/submit controls are reachable.

## 17. Suggested Smoke Test Set

Run this smaller set after each deployment:

1. Open app and authenticate if public mode.
2. Create a project.
3. Add one box in Settings if no boxes exist.
4. Add one VM with private network and forwarded port.
5. Add one plugin, one provisioner, and one trigger to Settings.
6. Assign plugin/provisioner/trigger to the project.
7. Generate Vagrantfile and verify it contains VM, network, plugin, provisioner, and trigger configuration.
8. Mark project Ready and verify editing/destructive controls are locked.
9. Return project to Draft and delete the project.
10. In public mode, verify shared resource badge/read-only behavior and logout.
