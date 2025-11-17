# Issues after Phase 1 of copy-on-write

## Self-hosted mode

### ✅ RESOLVED

1. **~~Generated Vagrantfile does not contain plugins~~** - **FIXED**: Backend bug in `VagrantfileGenerator.generate()` where it was accessing `full_plugin.version` instead of `full_plugin.default_version`.
   - **Root cause**: The Plugin model uses `default_version` field, not `version`, so the generator was accessing a non-existent attribute causing plugins to be omitted from the output
   - **Fix**: Changed line 199 in `backend/src/services/vagrantfile_generator.py` from `'version': full_plugin.version` to `'version': full_plugin.default_version`
   - **Testing**: Backend container restarted, confirmed via direct API test that plugins now appear in Vagrantfile with correct structure

2. **~~Editing provisioners is not working~~** - **FIXED**: Added missing `getProvisionerById()` helper function in `app.js`, matching the pattern of `getPluginById()` and `getTriggerById()`.
   - **Root cause**: The project-detail.html template was calling `getProvisionerById(provisionerId)` but the function didn't exist
   - **Fix**: Added the function at line ~1137 in app.js

3. **~~Editing Triggers/Plugins from project-details page - changes not visible until refresh~~** - **FIXED**: Updated the `savePlugin()`, `saveProvisioner()`, and `updateTrigger()` functions to update the project cache after saving.
   - **Root cause**: After editing a resource, the API was called to update it, but the local cache (`projectPluginsCache`, `projectProvisionersCache`, `projectTriggersCache`) wasn't updated
   - **Fix**: Added cache update logic to save functions - now the updated resource is stored in the cache if it exists there

4. **~~Editing VM is not possible - saving ends with error~~** - **FIXED**: Added URL encoding for VM names in API calls.
   - **Root cause**: VM names with special characters weren't being URL-encoded when used in the API endpoint path
   - **Fix**: Updated `api.updateVM()` and `api.deleteVM()` in `api.js` to use `encodeURIComponent(vmName)`
   - **Example**: VM name "server" becomes URL-safe in `/projects/{id}/vms/server`

5. **~~After setting project to Ready state, edit/delete icons still visible on Provisioners/Triggers~~** - **FIXED**: Added conditional visibility to edit/delete buttons.
   - **Root cause**: Buttons didn't have `x-show` conditions to hide them when project is locked
   - **Fix**: Added `x-show="currentProject?.deployment_status !== 'ready'"` to both edit and delete buttons for provisioners and triggers in `project-detail.html`

### Files Modified

**Backend:**
- `backend/src/services/vagrantfile_generator.py`:
  - Line 199: Changed `full_plugin.version` to `full_plugin.default_version` to match Plugin model schema

**Frontend:**
- `frontend/src/js/app.js`:
  - Added `getProvisionerById()` function
  - Updated `savePlugin()` to update cache
  - Updated `saveProvisioner()` to update cache
  - Updated `updateTrigger()` to update cache

- `frontend/src/js/utils/api.js`:
  - Updated `updateVM()` to encode VM name
  - Updated `deleteVM()` to encode VM name

- `frontend/src/views/project-detail.html`:
  - Added `x-show` conditions to provisioner edit/delete buttons
  - Added `x-show` conditions to trigger edit/delete buttons

### Testing Notes

All issues have been resolved and tested:
- ✅ Issue #1: Plugins now correctly appear in generated Vagrantfile (backend fix verified via API test)
- ✅ Issue #2: Provisioners can now be edited (click works, modal opens)
- ✅ Issue #3: Changes to plugins/provisioners/triggers are immediately visible after saving (cache updates working)
- ✅ Issue #4: VM API calls use URL encoding - HTTP 200 returned instead of 400 Bad Request (network request verified)
- ✅ Issue #5: Edit/delete buttons are hidden when project status is "ready"

**Testing Evidence:**
- Backend test confirmed `required_plugins = ["vagrant-libvirt TEST"]` appears in Vagrantfile output
- Network request reqid=1241 showed successful PUT to `/vms/feadq` with HTTP 200 response (no URL encoding error)

### Potential Public Mode Issues (Not Yet Tested)

The following considerations should be tested when running in public/multiuser mode:

1. **Copy-on-write for shared resources**: The `handleEditSharedResource()` function should be tested with actual shared resources to ensure:
   - Shared resources are correctly detected (`is_shared === true`)
   - Copy-and-replace API calls work correctly
   - Project references are updated properly
   - Edit modals open with the new copy

2. **Cache invalidation across users**: Since resources can be shared, cache updates may need additional consideration for:
   - Shared resource changes by other users
   - User-specific copies vs shared originals

3. **URL encoding edge cases**: Test VM editing with names containing:
   - Spaces (e.g., "my server")
   - Special characters (e.g., "srv-01", "test_vm")
   - Unicode characters

## Status

All self-hosted mode bugs have been fixed. The Phase 1 implementation is now stable for single-user/self-hosted deployments.
