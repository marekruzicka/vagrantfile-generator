# Shared Resources in Public Mode

## Overview

The Vagrantfile Generator supports two deployment modes:
- **Self-hosted mode** (`user_id=None`): Single-user, all resources are editable
- **Public mode** (`user_id` set): Multi-user, with shared read-only resources

This document describes how shared resources work in **public mode**.

## Resource Storage Structure

```
backend/data/
├── shared/              # Read-only resources for all users
│   ├── boxes/
│   │   └── boxes.json
│   ├── plugins/
│   │   └── *.json
│   ├── provisioners/
│   │   └── *.json
│   ├── triggers/
│   │   └── *.json
│   └── projects/
│       └── *.json
└── users/               # User-specific writable resources
    └── {user-id}/
        ├── boxes/
        │   └── boxes.json
        ├── plugins/
        │   └── *.json
        ├── provisioners/
        │   └── *.json
        ├── triggers/
        │   └── *.json
        └── projects/
            └── */
```

## Resource Metadata

All resources include two ownership fields:

- **`is_shared`**: `boolean`
  - `true` = Shared resource (read-only in public mode)
  - `false` = User-owned resource (editable)
  
- **`owner_id`**: `string | null`
  - `null` = Shared resource
  - `{user-id}` = Owned by specific user

## Backend Implementation

### Service Layer Logic

Each service (`PluginService`, `BoxService`, `GlobalProvisionerService`, `GlobalTriggerService`) follows this pattern:

#### 1. **List/Get Operations** (Read)
```python
def list_resources(self) -> List[ResourceSummary]:
    resources = []
    
    # Load shared resources first
    shared_resources = load_from_shared_directory()
    for resource in shared_resources:
        resource.is_shared = (self.user_id is not None)  # True in public mode
        resource.owner_id = None
        resources.append(resource)
    
    # Load user-specific resources (if in public mode)
    if self.user_id:
        user_resources = load_from_user_directory(self.user_id)
        for resource in user_resources:
            resource.is_shared = False
            resource.owner_id = self.user_id
            resources.append(resource)
    
    return resources
```

#### 2. **Create Operations** (Write)
```python
def create_resource(self, data: ResourceCreate) -> Resource:
    # Always save to user directory in public mode
    if self.user_id:
        save_to_user_directory(self.user_id, resource)
    else:
        # Self-hosted mode: save to shared directory
        save_to_shared_directory(resource)
```

#### 3. **Update/Delete Operations** (Write)
```python
def update_resource(self, resource_id: str, data: ResourceUpdate) -> Resource:
    # Prevent editing shared resources in public mode
    if self.user_id:
        user_file = get_user_file_path(self.user_id, resource_id)
        if not user_file.exists():
            raise ServiceError("Cannot edit shared resources")
    
    # Proceed with update only if resource is in user directory
    return perform_update(resource_id, data)

def delete_resource(self, resource_id: str) -> bool:
    # Prevent deleting shared resources in public mode
    if self.user_id:
        user_file = get_user_file_path(self.user_id, resource_id)
        if not user_file.exists():
            raise ServiceError("Cannot delete shared resources")
    
    # Proceed with deletion only if resource is in user directory
    return perform_delete(resource_id)
```

### API Layer Protection

Additional validation at the API endpoint level:

```python
@router.put("/resources/{resource_id}")
async def update_resource(
    resource_id: str,
    data: ResourceUpdate,
    service: ResourceService = Depends(get_service)
):
    # Double-check shared resource protection
    if service.user_id:
        shared_path = get_shared_path(resource_id)
        if shared_path.exists():
            raise HTTPException(
                status_code=403,
                detail="Cannot modify shared resource"
            )
    
    return service.update_resource(resource_id, data)
```

## Frontend Implementation

### Visual Distinction

Shared resources are visually distinguished with:

1. **Amber border and background**:
   ```html
   :class="resource.is_shared ? 'border-amber-200 bg-amber-50/20' : ''"
   ```

2. **"Shared" badge** with lock icon:
   ```html
   <span x-show="resource.is_shared" class="shared-resource-badge">
     🔒 Shared
   </span>
   ```

### Action Button Control

Edit and Delete buttons are hidden for shared resources:

```html
<!-- Edit Button -->
<button x-show="!resource.is_shared" @click="editResource(resource)">
  Edit
</button>

<!-- Delete Button -->
<button x-show="!resource.is_shared" @click="deleteResource(resource.id)">
  Delete
</button>
```

### Alpine.js Data Binding

```javascript
Alpine.data('settingsData', () => ({
    plugins: [],
    provisioners: [],
    triggers: [],
    boxes: [],
    
    async loadPlugins() {
        const response = await api.get('/api/plugins');
        // API returns: [{ id, name, is_shared, owner_id, ... }, ...]
        this.plugins = response;
    }
}));
```

## Resource Types

### 1. Plugins
- **Storage**: Individual JSON files (`{plugin-id}.json`)
- **Shared**: Common Vagrant plugins (vagrant-libvirt, vagrant-hostmanager, etc.)
- **User**: Custom or user-added plugins

### 2. Boxes
- **Storage**: Single `boxes.json` file with structure `{"boxes": [...]}`
- **Shared**: Common base images (Ubuntu, Debian, RHEL, etc.)
- **User**: Custom box images

### 3. Global Provisioners
- **Storage**: Individual JSON files (`{provisioner-id}.json`)
- **Shared**: Common provisioning scripts (apt update, yum update, etc.)
- **User**: Custom provisioning scripts

### 4. Global Triggers
- **Storage**: Individual JSON files (`{trigger-id}.json`)
- **Shared**: Common triggers (RHC registration, logging, etc.)
- **User**: Custom triggers

### 5. Projects
- **Storage**: Directory per project with `project.json`
- **Shared**: Example/template projects (read-only)
- **User**: User-created projects (editable)

## Security Model

### Defense in Depth

1. **Backend Validation (Primary)**:
   - Service layer checks file ownership before write operations
   - Prevents modification of files outside user directory
   - Returns error if attempting to edit/delete shared resources

2. **API Validation (Secondary)**:
   - Additional checks at endpoint level
   - HTTP 403 Forbidden for shared resource modifications

3. **Frontend Controls (UX)**:
   - Hides edit/delete buttons for shared resources
   - Visual distinction prevents user confusion
   - Not relied upon for security (client-side can be bypassed)

### Permission Matrix

| Operation | Self-hosted Mode | Public Mode (Shared) | Public Mode (User-owned) |
|-----------|------------------|----------------------|--------------------------|
| **Read** | ✅ All resources | ✅ Read-only | ✅ Full access |
| **Create** | ✅ Save to shared | ❌ Not allowed | ✅ Save to user dir |
| **Update** | ✅ All resources | ❌ Blocked by backend | ✅ User resources only |
| **Delete** | ✅ All resources | ❌ Blocked by backend | ✅ User resources only |
| **Use in Projects** | ✅ All resources | ✅ Can reference | ✅ Can reference |

## Example Scenarios

### Scenario 1: User views Settings page
1. Frontend loads resources via API: `GET /api/plugins`
2. Backend `PluginService.list_plugins()`:
   - Loads 4 shared plugins from `/data/shared/plugins/`
   - Sets `is_shared=true`, `owner_id=null`
   - Loads 0 user plugins from `/data/users/{user-id}/plugins/`
   - Returns merged list: 4 resources
3. Frontend displays:
   - 4 plugins with "🔒 Shared" badge
   - Amber border/background
   - No edit/delete buttons

### Scenario 2: User creates new plugin
1. User clicks "Add Plugin" → fills form → saves
2. Frontend: `POST /api/plugins` with plugin data
3. Backend `PluginService.create_plugin()`:
   - Generates new UUID
   - Saves to `/data/users/{user-id}/plugins/{uuid}.json`
   - Returns plugin with `is_shared=false`, `owner_id={user-id}`
4. Frontend refreshes list:
   - Shows 5 plugins (4 shared + 1 user-owned)
   - User's plugin has edit/delete buttons visible

### Scenario 3: User attempts to delete shared plugin
**Via UI** (prevented):
- Delete button is hidden (`x-show="!plugin.is_shared"`)
- User cannot click it

**Via API** (blocked):
```bash
curl -X DELETE http://localhost:8000/api/plugins/{shared-plugin-id} \
  -H "Authorization: Bearer $TOKEN"

# Response: 400 Bad Request
# {"detail": "Cannot delete shared resources"}
```

### Scenario 4: User uses shared plugin in project
1. User creates/edits project
2. Opens "Add Plugin" dialog
3. Sees all plugins (shared + owned)
4. Selects shared plugin "vagrant-libvirt"
5. Plugin is added to project configuration
6. Project references shared plugin by ID
7. ✅ Works correctly - shared resources can be used (read), not modified

## Data Model Classes

### Backend Models

```python
# Full model with all fields
class Plugin(BaseModel):
    id: str
    name: str
    description: Optional[str]
    # ... other fields ...
    is_shared: Optional[bool] = False
    owner_id: Optional[str] = None

# Summary model for list views
class PluginSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    default_version: Optional[str]
    is_deprecated: bool = False
    is_shared: Optional[bool] = False  # Added for public mode
    owner_id: Optional[str] = None     # Added for public mode
```

Similar structure for:
- `Box` / `BoxSummary`
- `GlobalProvisioner` / `GlobalProvisionerSummary`
- `GlobalTrigger` / `GlobalTriggerSummary`
- `Project` / `ProjectSummary`

## Error Handling

### Backend Errors

```python
# Attempting to edit shared resource
raise PluginServiceError("Cannot edit shared resources")
raise BoxServiceError("Cannot edit shared resources")
raise ProvisionerServiceError("Cannot edit shared resources")
raise TriggerServiceError("Cannot delete shared resources")
```

### API Errors

```json
{
  "status_code": 403,
  "detail": "Cannot modify shared resource - shared resources are read-only"
}
```

## Testing

### Manual Testing Checklist

- [ ] Shared resources display with amber border/background
- [ ] Shared resources show "🔒 Shared" badge
- [ ] Edit/delete buttons hidden for shared resources
- [ ] Backend returns 403/400 when attempting to modify shared resources via API
- [ ] User can create new private resources
- [ ] User can edit/delete own resources
- [ ] User can use shared resources in projects (read-only)
- [ ] Shared resources appear in selection dropdowns
- [ ] Project export includes shared resource references correctly

### API Testing

```bash
# Get JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/email \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","otp":"123456"}' \
  | jq -r '.access_token')

# Test 1: List plugins (should show is_shared field)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/plugins | jq '.[0] | {name, is_shared, owner_id}'

# Expected output for shared plugin:
# {
#   "name": "vagrant-libvirt",
#   "is_shared": true,
#   "owner_id": null
# }

# Test 2: Attempt to delete shared plugin (should fail)
SHARED_PLUGIN_ID=$(curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/plugins | jq -r '.[0].id')

curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/plugins/$SHARED_PLUGIN_ID"

# Expected: 400 Bad Request with error message

# Test 3: Create user plugin (should succeed)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  http://localhost:8000/api/plugins \
  -d '{"name":"my-plugin","description":"My custom plugin"}'

# Expected: 201 Created with is_shared=false, owner_id={user-id}
```

## Migration Notes

### From Self-hosted to Public Mode

When migrating from self-hosted to public mode:

1. Move existing resources to `/data/shared/` directory
2. Set `is_shared: true` and `owner_id: null` in resource files
3. User-created resources will be in `/data/users/{user-id}/`
4. No data loss - all resources remain accessible

### Adding New Shared Resources

To add new shared resources (as admin):

1. Create resource JSON in `/data/shared/{resource-type}/`
2. Set appropriate metadata (`is_shared: true`, `owner_id: null`)
3. Restart backend or reload resources
4. All users will see the new shared resource

## Known Limitations

1. **Boxes Display Issue**: Boxes list currently shows "0 boxes available" in frontend despite backend returning correct data. This is a separate Alpine.js/frontend issue unrelated to is_shared functionality.

2. **No Admin UI**: Currently no web UI for managing shared resources. Shared resources must be added directly to `/data/shared/` directories.

3. **No Resource Versioning**: Shared resources cannot be versioned. Updates affect all users immediately.

4. **No Fine-grained Permissions**: All shared resources are read-only for all users. No role-based access control (RBAC).

## Future Enhancements

- [ ] Admin UI for managing shared resources
- [ ] Resource versioning and rollback
- [ ] Role-based access control (read-only, contributor, admin)
- [ ] Resource approval workflow (users submit, admin approves)
- [ ] Resource categories/tags for better organization
- [ ] Resource usage statistics
- [ ] Bulk import/export of shared resources
