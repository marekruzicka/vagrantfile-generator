# User-Based Test Plan

This document defines end-to-end tests from a user's point of view. Tests should interact with the running application through a browser only (for example with Playwright), not by calling internal code directly.

## Implementation Status

**Implemented:** 54 of 64 subsections — **~84%**

| Section | Status | Spec file |
|---|---|---|
| 1. Authentication | ❌ 0/6 | *auth.setup.ts (setup only, no UX tests)* |
| 2. Projects Dashboard | ✅ 6/6 | `projects-dashboard.spec.ts` |
| 3. Virtual Machines | ✅ 8/8 | `vms.spec.ts` |
| 4. Networking | ✅ 6/6 | `networking.spec.ts` |
| 5. Global Settings: Boxes | ✅ 5/5 | `settings-boxes.spec.ts` |
| 6. Global Settings: Plugins | ⚠️ 4/5 | `settings-plugins.spec.ts` |
| 7. Project Plugins | ✅ 5/5 | `project-plugins.spec.ts` |
| 8. Global Settings: Provisioners | ✅ 4/4 | `settings-provisioners.spec.ts` |
| 9. Project Provisioners | ✅ 3/3 | `project-provisioners.spec.ts` |
| 10. Global Settings: Triggers | ✅ 5/5 | `settings-triggers.spec.ts` |
| 11. Project Triggers | ✅ 3/3 | `project-triggers.spec.ts` |
| 12. Shared Resources | ✅ 7/7 | `shared-resources.spec.ts` |
| 13. Generated Vagrantfile | ✅ 7/7 | `generated-vagrantfile.spec.ts` |
| 14. Global Application Settings | ✅ 3/3 | `application-settings.spec.ts` |
| 15. Footer / Error UX | ❌ 0/4 | *not started* |
| 16. Responsiveness | ❌ 0/4 | *not started* |
| 17. Smoke Test | ❌ 0/1 | *not started* |

Legend:
- ✅ fully covered by E2E tests
- ⚠️ partially covered — see per-subsection notes
- ❌ not yet implemented

## Scope and Assumptions

- Application under test: Vagrantfile Generator web UI.
- Primary URL examples:
  - Self-hosted/local: `http://localhost:8080` / `http://localhost:5173`
  - Public deployment: deployed hostname such as `http://vgf.i.glide.sk`
- User tests may validate generated Vagrantfile text, visible UI state, notifications, browser redirects, and persistence after reload/re-login.
- API calls may be observed in DevTools/network logs, but test actions should be performed through the UI.
- Public-mode authentication tests require configured Mailgun and/or OAuth providers.
- E2E tests live under `frontend/tests/e2e/`. Run selectively per spec file:

  ```bash
  E2E_BASE_URL=https://vgf.i.glide.sk:443 \
  E2E_USER_EMAIL=test@glide.sk \
  E2E_USER_EMAIL_2=test1@glide.sk \
  E2E_USER_OTP=123456 \
  npx playwright test tests/e2e/vms.spec.ts
  ```

- Full suite:

  ```bash
  E2E_BASE_URL=https://vgf.i.glide.sk:443 \
  E2E_USER_EMAIL=test@glide.sk \
  E2E_USER_EMAIL_2=test1@glide.sk \
  E2E_USER_OTP=123456 \
  npm run test:e2e
  ```

## 1. Authentication and Deployment Modes

> Status: ❌ not implemented (only auth-setup for other tests, no UX coverage)

### 1.1 Self-hosted mode has no login gate ❌
**Given** the app runs in self-hosted mode or with `DEPLOYMENT_MODE` unset  
**When** a user opens the application URL  
**Then** the Projects page is shown without a login page.

### 1.2 Public mode redirects unauthenticated users to login ❌
**Given** the app runs in public mode  
**When** an unauthenticated user opens the application URL  
**Then** the Login page is shown with email OTP input and Google/GitHub/GitLab buttons.

### 1.3 Email OTP login happy path ❌
**Given** public mode with email OTP configured  
**When** the user enters a valid email, clicks "Send Login Code", receives the code, and submits it  
**Then** the user is redirected to the main Projects page and can use the app.

### 1.4 Email OTP validation and rate-limit UX ❌
Test invalid email, incorrect OTP, expired OTP, repeated OTP requests, and resend behavior. The user should receive clear errors and should not gain access until a valid code is provided.

### 1.5 OAuth login providers ❌
For Google, GitHub, and GitLab where configured: clicking "Continue with …" should redirect to the provider, complete consent/login, return to the app, and show the Projects page as an authenticated user.

### 1.6 Session persistence and logout ❌
After login, reload the page and reopen the browser within the session lifetime; the user should remain logged in. After logout or token expiry, opening the app should show the login page again.

## 2. Projects Dashboard

> Status: ✅ fully covered — `projects-dashboard.spec.ts`

### 2.1 Empty first-run experience ✅
**Given** the user has no projects  
**When** they open the Projects page  
**Then** the empty state explains the create-project workflow and shows "Create Your First Project".

> Note: test is skipped automatically when the target environment already has projects.

### 2.2 Create project ✅
Create a project with name and description. Verify it appears immediately as a project card with Draft status and correct stats.

### 2.3 Project list stats and filters ✅
With multiple Draft and Ready projects, verify dashboard stat cards and filters: All, Draft, Ready. Empty filtered states should explain that no projects match the selected filter.

### 2.4 Open project detail ✅
Click a project card. Verify the detail page shows project name, description, VM count, status badge, and sections for Plugins, Provisioners, Triggers, and VMs.

### 2.5 Delete draft project ✅
Delete a Draft project from the dashboard and confirm it disappears after confirmation. Verify canceling the confirmation leaves the project intact.

### 2.6 Ready project protection ✅
Mark a project Ready. Verify it is visually highlighted/marked Ready and destructive or editing actions are disabled/hidden where expected. Switch back to Draft and verify editing resumes.

## 3. Virtual Machines

> Status: ✅ fully covered — `vms.spec.ts`

### 3.1 Add a single VM ✅
In a Draft project, add a VM with name, box, hostname, memory, CPUs, and labels. Verify the VM card displays the configuration and the project VM count updates.

### 3.2 Required-field and resource validation ✅
Try creating a VM with missing name, invalid memory, or invalid CPU count. Verify inline validation and no invalid VM is saved.

### 3.3 Bulk create VMs ✅
Set Count greater than 1. Verify the previewed names use the expected suffix pattern and all VMs are created with unique names and shared base settings.

### 3.4 Edit VM ✅
Edit VM name, box, hostname, memory, CPUs, labels, and network. Save and verify values persist after page reload. Re-navigate to project detail after reload.

### 3.5 Delete VM ✅
Delete a VM and verify the card and VM count update. Canceling delete leaves the VM unchanged.

### 3.6 VM labels and selection ✅
Create VMs with labels. Use label quick selection and manual checkboxes to select VMs. Verify selection counters, select-all, clear-selection, and label-based selection behavior.

### 3.7 Bulk edit VMs ✅
Select multiple VMs and bulk-edit memory and CPUs. Verify all selected VMs are updated and unselected VMs are unchanged.

### 3.8 Bulk delete VMs ✅
Select multiple VMs, bulk delete, confirm, and verify only selected VMs are removed.

## 4. Networking

> Status: ✅ fully covered — `networking.spec.ts`

### 4.1 Private network with DHCP ✅
Add a private network interface using DHCP. Verify the VM card and generated Vagrantfile reflect a private network without static IP.

### 4.2 Private network with static IP and netmask ✅
Add a private network with static IP and netmask. Verify validation accepts private ranges and generated Vagrantfile includes IP and netmask.

### 4.3 Public network ✅
Add a public network with bridge interface. Verify display and generated Vagrantfile are correct.

### 4.4 Port forwarding ✅
Add forwarded port mappings with host port, guest port, and TCP protocol. Verify valid mappings appear in generated output.

### 4.5 Bulk IP incrementing ✅
Bulk-create multiple VMs with a static base IP. Verify subsequent VMs receive incremented IP addresses.

### 4.6 Public IP validation setting ✅
With "Allow public IPs in private networks" disabled, try a public static IP in private network and verify the form validation catches it. Enable the setting and verify the same IP is accepted.

## 5. Global Settings: Boxes

> Status: ✅ fully covered — `settings-boxes.spec.ts`

### 5.1 View box catalog ✅
Open Settings → Vagrant Boxes. Verify boxes list with name, provider, description, and refresh button.

### 5.2 Create box ✅
Add a box with name, description, provider, and optional version. Verify it appears in Settings.

### 5.3 Edit box ✅
Edit a user-owned box description. Verify updated values persist after refresh.

### 5.4 Delete box ✅
Delete a user-owned box and verify it is removed from Settings.

### 5.5 Duplicate/invalid box validation ✅
Attempt to submit an empty form. Verify the modal stays open.

## 6. Global Settings: Plugins

> Status: ⚠️ mostly covered — `settings-plugins.spec.ts`
>
> Missing: broad version-format validation (6.5 only covers empty submission).

### 6.1 View plugin catalog ✅
Open Settings → Plugins. Verify plugin cards show name, description, default version, and Active/Deprecated status.

### 6.2 Create plugin ✅
Add a plugin with name, description, source URL, documentation URL, default version, configuration, and deprecated flag. Verify it appears in Settings.

### 6.3 Edit plugin ✅
Edit plugin metadata and deprecated status. Verify changes persist after refresh.

### 6.4 Delete plugin ✅
Delete a user-owned plugin and verify it is removed from Settings.

### 6.5 Plugin version validation ⚠️
Test common version formats and invalid values. Verify accepted versions are saved and invalid versions show errors.

> Currently only tests that an empty form submission keeps the modal open. Missing: matrix of accepted (`1.0.0`, `~> 2.0`, `>= 3.0, < 4.0`) and rejected (`abc`, `***`) version strings.

## 7. Project Plugins

> Status: ✅ fully covered — `project-plugins.spec.ts`

### 7.1 Add plugins to project ✅
From Project Detail → Plugins, open Add Plugin, select a plugin, and save. Verify plugin cards appear on the project.

### 7.2 Add-plugin filtering ✅
Verify the Add Plugin modal only shows plugins not already assigned to the project, hiding already-assigned items.

### 7.3 Edit project plugin ✅
Edit a plugin from Project Detail. Verify version changes save and generated Vagrantfile includes the updated version.

### 7.4 Remove project plugin ✅
Remove one plugin from a project. Verify it disappears from the project but remains available globally in Settings.

### 7.5 Bulk remove project plugins ✅
Select multiple project plugins, use Bulk Delete, confirm, and verify selected plugins are removed.

## 8. Global Settings: Provisioners

> Status: ✅ fully covered — `settings-provisioners.spec.ts`

### 8.1 View provisioner catalog ✅
Open Settings → Provisioners. Verify provisioner cards show name, description, type, and run mode.

### 8.2 Create shell provisioner ✅
Create a shell provisioner with inline script, privilege, and run mode. Verify it appears in Settings.

### 8.3 Edit provisioner ✅
Edit script, path, privilege, and run mode. Verify description updates persist.

### 8.4 Delete provisioner ✅
Delete a user-owned provisioner and verify it is removed from Settings.

## 9. Project Provisioners

> Status: ✅ fully covered — `project-provisioners.spec.ts`

### 9.1 Add provisioners to project ✅
From Project Detail → Provisioners, select a provisioner and add it. Verify project provisioner cards appear and generated Vagrantfile includes it.

### 9.2 Add-provisioner filtering ✅
Verify only provisioners not already assigned are offered, with a useful empty state when all are added.

### 9.3 Remove and bulk remove project provisioners ✅
Remove one provisioner and then bulk-remove several. Verify global provisioner templates remain available in Settings.

## 10. Global Settings: Triggers

> Status: ✅ fully covered — `settings-triggers.spec.ts`

### 10.1 View trigger catalog ✅
Open Settings → Triggers. Verify trigger cards show name, description, timing, and stage.

### 10.2 Create host trigger ✅
Create a trigger with timing, stage, host `run` command, and description. Verify it appears in Settings.

### 10.3 Create remote trigger ✅
Create a trigger using remote inline command. Verify it accepts the remote-run textarea and saves successfully.

### 10.4 Edit trigger ✅
Edit trigger description and command. Verify updates persist.

### 10.5 Delete trigger ✅
Delete a user-owned trigger and verify it disappears from Settings.

## 11. Project Triggers

> Status: ✅ fully covered — `project-triggers.spec.ts`

### 11.1 Add triggers to project ✅
From Project Detail → Triggers, select trigger(s) and add them. Verify trigger cards appear on the project and generated Vagrantfile includes them.

### 11.2 Search and filtering in trigger modal ✅
Use trigger search in the Add Triggers modal. Verify matching triggers are shown and non-matching triggers are hidden.

### 11.3 Remove and bulk remove project triggers ✅
Remove a single trigger and bulk-remove selected triggers. Verify templates remain available in Settings.

## 12. Shared Resources and Multi-User Isolation

> Status: ✅ fully covered — `shared-resources.spec.ts`
>
> Several subsections skip when no shared resources are available in the environment.

### 12.1 Shared resource visual indicators ✅
In public mode with shared resources, verify shared boxes have a "Shared" badge. Test skips when no shared resources are available.

### 12.2 Shared resources are read-only ✅
For shared resources, verify the Shared badge is visible with amber styling and tooltip explaining the resource cannot be edited or deleted. Verify the copy-to-my-resources button is visible.

### 12.3 Copy shared resource to personal resource ✅
Use "Copy to My Resources" on a shared box. Verify a success toast appears.

### 12.4 Favorite shared resources ✅
Star/unstar shared resources. Verify the button toggles.

### 12.5 Hide/show shared resources ✅
Toggle Shared Resources visibility in Settings. Verify the label changes between "Showing" and "Hidden".

### 12.6 Two-user data isolation ✅
Login as Alice. Create a project and a private plugin. Login as Bob. Verify Bob cannot see Alice's project or private plugin. Alice cannot see Bob's project.

> Uses `E2E_USER_EMAIL`, `E2E_USER_EMAIL_2`, `E2E_USER_OTP` (and optionally `E2E_USER_OTP_2`).

### 12.7 Shared resource usage in projects ✅
Add a shared box to a project. Verify the project can use it and generated Vagrantfile includes it.

## 13. Generated Vagrantfile

> Status: ✅ fully covered — `generated-vagrantfile.spec.ts`

### 13.1 Generate simple Vagrantfile ✅
Create a project with one VM and generate/preview the Vagrantfile. Verify syntax includes `Vagrant.configure`, VM name, box, hostname, memory, and CPU settings.

### 13.2 Generate multi-VM Vagrantfile ✅
Create multiple VMs with different resources. Verify each VM is represented correctly.

### 13.3 Generate with plugins ✅
Add a plugin with version. Verify the generated Vagrantfile includes plugin name and version constraint.

### 13.4 Generate with provisioners ✅
Add a shell provisioner. Verify the generated Vagrantfile includes the provisioner script.

### 13.5 Generate with triggers ✅
Add a trigger. Verify the generated Vagrantfile includes the trigger command.

### 13.6 Copy/download generated content ✅
Copy-to-clipboard verified against displayed Vagrantfile text. Download verified for correct filename (`Vagrantfile`) and content.

### 13.7 Generation validation ✅
Attempt to generate a Vagrantfile for a project with no VMs. Verify the generate button is hidden.

## 14. Global Application Settings

> Status: ✅ fully covered — `application-settings.spec.ts`

### 14.1 Network validation settings persistence ✅
Change max CPUs, max memory, min memory, memory step, and public-IP allowance. Reload the page and verify settings persist. Verify max CPU limit is reflected in VM creation form.

### 14.2 Collapsible sections ✅
On Project Detail and Settings, collapse and expand VMs and Vagrant Boxes sections. Verify controls hide and show.

### 14.3 Refresh actions ✅
Use refresh buttons for boxes. Verify controls remain usable afterward.

## 15. Footer, Documentation, and Error UX

> Status: ❌ not implemented

### 15.1 Footer links ❌
Click footer links for changelog/documentation. Verify internal markdown opens in a readable modal and external links open in a new tab.

### 15.2 Notifications ❌
For successful create/edit/delete/copy operations, verify success notifications are shown. For validation/API errors, verify error notifications are clear and dismissible.

### 15.3 API/backend unavailable state ❌
Stop or block the backend while the frontend is open. Verify the app shows a usable error state and recovers after backend availability returns and the user refreshes/retries.

### 15.4 Not-found/error page ❌
Navigate to an invalid app route or cause a handled application error. Verify a user-friendly error page/component is displayed.

## 16. Responsiveness and Browser Compatibility

> Status: ❌ not implemented

### 16.1 Desktop layout ❌
Verify Projects, Project Detail, Settings grids, modals, and generated Vagrantfile preview are usable at common desktop widths.

### 16.2 Tablet layout ❌
Verify cards, filters, section headers, and modals remain usable on tablet-sized viewports.

### 16.3 Mobile layout ❌
Verify login, project list, VM forms, settings cards, modals, and action buttons are accessible on mobile widths without horizontal scrolling or hidden required actions.

### 16.4 Keyboard accessibility smoke test ❌
Use Tab/Shift+Tab/Enter/Escape through login, main navigation, forms, modals, and confirmations. Verify focus is visible and modal close/submit controls are reachable.

## 17. Suggested Smoke Test Set

> Status: ❌ not implemented

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
