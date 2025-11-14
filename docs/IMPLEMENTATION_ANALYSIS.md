# Implementation Analysis: Proposed Changes

## Date: 2025-11-14

## Proposed Changes

1. **Rewrite boxes to follow the same "model" as other resources** - separate file for each box
2. **Projects are not shared** - logged in user does not see any project they do not own
3. **User can "manage" shared resources within their project**
   - Option A: User can hide shared resources (soft delete - not shown but not deleted)
   - Option B: Global show/hide toggle + button to create physical copy of shared resource

---

## Change 1: Boxes - Separate File Per Box

### Current State

**Storage Format:**
```
backend/data/shared/boxes/boxes.json
{
  "boxes": [
    {"id": "...", "name": "generic/ubuntu2204", ...},
    {"id": "...", "name": "generic/debian12", ...}
  ]
}
```

**Issues:**
- Inconsistent with plugins, provisioners, triggers (which use individual files)
- All boxes loaded/saved together (inefficient for large lists)
- Concurrent writes could corrupt entire boxes collection
- More complex merge logic in `BoxService.list_boxes()`

### Target State

**Storage Format:**
```
backend/data/shared/boxes/
  e724b9a6-88dc-4348-bfe5-554b3d33aa8a.json
  84f3a6d2-f485-473c-a180-527d8fc3d22d.json
  5af90c9a-e8a8-48e9-9dde-265d0bdb962b.json
  ...

backend/data/users/{user-id}/boxes/
  {box-uuid}.json
  {box-uuid}.json
  ...
```

**Each file contains:**
```json
{
  "id": "e724b9a6-88dc-4348-bfe5-554b3d33aa8a",
  "name": "generic/ubuntu2204",
  "description": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
  "provider": "libvirt",
  "version": null,
  "url": null,
  "created_at": "2025-09-25T15:40:00.876903",
  "updated_at": "2025-09-25T15:40:00.876911",
  "is_shared": true,
  "owner_id": null
}
```

### Implementation Steps

#### 1.1 Migration Script
Create one-time migration to split `boxes.json` into individual files:

```python
# backend/scripts/migrate_boxes.py
import json
from pathlib import Path

def migrate_boxes():
    """Migrate boxes.json to individual files."""
    boxes_file = Path("backend/data/shared/boxes/boxes.json")
    
    if not boxes_file.exists():
        print("No boxes.json found, skipping migration")
        return
    
    with open(boxes_file, 'r') as f:
        data = json.load(f)
    
    boxes = data.get("boxes", [])
    
    for box in boxes:
        box_id = box['id']
        output_file = boxes_file.parent / f"{box_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(box, f, indent=2)
        
        print(f"Migrated box: {box['name']} -> {box_id}.json")
    
    # Backup original file
    boxes_file.rename(boxes_file.parent / "boxes.json.backup")
    print(f"Backed up original to boxes.json.backup")
```

#### 1.2 Rewrite BoxService

**Changes to `backend/src/services/box_service.py`:**

```python
class BoxService:
    def __init__(self, base_directory: str = "data", user_id: Optional[str] = None):
        # Remove boxes_file attribute
        # Use file_service for path management
        self.file_service = FileService()
        self.user_id = user_id
        
        if user_id:
            self.boxes_directory = self.file_service.get_user_data_path(user_id, "boxes")
        else:
            self.boxes_directory = self.file_service.get_shared_data_path("boxes")
        
        self.boxes_directory.mkdir(parents=True, exist_ok=True)
    
    def list_boxes(self) -> List[BoxSummary]:
        """List all boxes (shared + user-specific)."""
        boxes = []
        
        # Use merge_resources helper (same as plugins/provisioners/triggers)
        def load_box_summary(file_path: Path) -> dict:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        merged_data = self.file_service.merge_resources(
            user_id=self.user_id,
            resource_type="boxes",
            loader_func=load_box_summary
        )
        
        # Convert to BoxSummary instances
        for data in merged_data:
            boxes.append(BoxSummary(**data))
        
        return boxes
    
    def get_box(self, box_id: str) -> Box:
        """Get a specific box by ID."""
        # Try user directory first
        if self.user_id:
            user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
            if user_file.exists():
                with open(user_file, 'r') as f:
                    return Box(**json.load(f))
        
        # Try shared directory
        shared_file = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
        if shared_file.exists():
            with open(shared_file, 'r') as f:
                return Box(**json.load(f))
        
        raise BoxServiceError(f"Box {box_id} not found")
    
    def create_box(self, box_data: BoxCreate) -> Box:
        """Create a new box."""
        box_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        box = Box(
            id=box_id,
            name=box_data.name,
            description=box_data.description,
            provider=box_data.provider,
            version=box_data.version,
            url=box_data.url,
            created_at=now,
            updated_at=now
        )
        
        # Save to user directory if in public mode
        if self.user_id:
            file_path = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
        else:
            file_path = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(box.dict(), f, indent=2)
        
        return box
    
    def update_box(self, box_id: str, box_data: BoxUpdate) -> Box:
        """Update an existing box."""
        # Prevent editing shared resources in public mode
        if self.user_id:
            user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
            if not user_file.exists():
                raise BoxServiceError("Cannot edit shared resources")
            file_path = user_file
        else:
            file_path = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
        
        # Load existing box
        with open(file_path, 'r') as f:
            box_dict = json.load(f)
        
        # Update fields
        update_data = box_data.dict(exclude_unset=True)
        box_dict.update(update_data)
        box_dict['updated_at'] = datetime.now().isoformat()
        
        # Save
        with open(file_path, 'w') as f:
            json.dump(box_dict, f, indent=2)
        
        return Box(**box_dict)
    
    def delete_box(self, box_id: str) -> bool:
        """Delete a box."""
        # Prevent deleting shared resources in public mode
        if self.user_id:
            user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
            if not user_file.exists():
                raise BoxServiceError("Cannot delete shared resources")
            user_file.unlink()
        else:
            file_path = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
            file_path.unlink()
        
        return True
```

**Remove:**
- `_initialize_default_boxes()` method
- `_load_boxes()` method
- `_save_boxes()` method
- All references to `self.boxes_file`

#### 1.3 Update FileService

No changes needed - `merge_resources()` already supports any resource type with `.json` files.

#### 1.4 Frontend Changes

**Minimal/None** - Frontend uses API endpoints which abstract storage format.

### Complexity Assessment

**Effort:** LOW-MEDIUM  
**Risk:** LOW  
**Benefits:**
- ✅ Consistency across all resource types
- ✅ Better performance (load only needed boxes)
- ✅ Simpler merge logic (reuses existing helper)
- ✅ Safer concurrent access
- ✅ Easier debugging (one file per resource)

**Drawbacks:**
- One-time migration script needed
- More files in filesystem (not a real issue)

**Recommendation:** ✅ **IMPLEMENT** - This is a solid architectural improvement with minimal risk.

---

## Change 2: Projects Are Not Shared

### Current State

**Project Loading Logic** (`project_service.py` line 286+):
```python
def list_projects(self) -> List[ProjectSummary]:
    """List all projects (merged shared + user-specific)."""
    
    # Merge shared and user resources
    merged_data = file_service.merge_resources(
        user_id=self.user_id,
        resource_type="projects",
        loader_func=load_project_summary
    )
```

**Issues:**
- Projects in `/data/shared/projects/` are shown to all users
- Users see template/example projects they didn't create
- Confusing UX - which project is mine?

### Target State

**Project Loading Logic:**
```python
def list_projects(self) -> List[ProjectSummary]:
    """List user's own projects only (no shared projects)."""
    
    # Only load from user directory
    if not self.user_id:
        # Self-hosted mode: load from shared directory
        return load_from_shared_directory()
    
    # Public mode: load ONLY from user directory
    return load_from_user_directory(self.user_id)
```

**Storage:**
- `/data/shared/projects/` - Only for self-hosted mode or templates (not visible in public mode)
- `/data/users/{user-id}/projects/` - User's own projects

### Implementation Steps

#### 2.1 Modify ProjectService.list_projects()

```python
def list_projects(self) -> List[ProjectSummary]:
    """
    List projects.
    - Public mode: Only user's own projects
    - Self-hosted mode: Projects from shared directory
    """
    projects = []
    file_service = FileService()
    
    if self.user_id:
        # PUBLIC MODE: Only load user's projects
        user_dir = file_service.get_user_data_path(self.user_id, "projects")
        if not user_dir.exists():
            return []
        
        for file_path in user_dir.glob("*.json"):
            if file_path.name.endswith('.json'):
                try:
                    data = load_project_summary(file_path)
                    data['is_shared'] = False
                    data['owner_id'] = self.user_id
                    projects.append(ProjectSummary(**data))
                except Exception as e:
                    print(f"Error loading project {file_path}: {e}")
    else:
        # SELF-HOSTED MODE: Load from shared directory
        shared_dir = file_service.get_shared_data_path("projects")
        if not shared_dir.exists():
            return []
        
        for file_path in shared_dir.glob("*.json"):
            if file_path.name.endswith('.json'):
                try:
                    data = load_project_summary(file_path)
                    data['is_shared'] = False  # In self-hosted, no concept of shared
                    data['owner_id'] = None
                    projects.append(ProjectSummary(**data))
                except Exception as e:
                    print(f"Error loading project {file_path}: {e}")
    
    return projects
```

#### 2.2 Modify ProjectService._load_project_from_file()

Remove the fallback to shared directory:

```python
def _load_project_from_file(self, project_id: UUID) -> Project:
    """Load a project from its JSON file."""
    file_path = self._get_project_file_path(project_id)
    
    # REMOVE THIS BLOCK:
    # if not file_path.exists() and self.user_id:
    #     # Check shared directory
    #     file_service = FileService()
    #     shared_path = file_service.get_shared_data_path("projects") / f"{project_id}.json"
    #     if shared_path.exists():
    #         file_path = shared_path
    
    if not file_path.exists():
        raise ProjectNotFoundError(f"Project {project_id} not found")
    
    # ... rest of method unchanged
```

#### 2.3 Update Frontend (Optional)

Remove any "Shared" badge logic for projects if it exists.

### Complexity Assessment

**Effort:** LOW  
**Risk:** LOW  
**Benefits:**
- ✅ Clearer UX - users only see their own projects
- ✅ Better privacy - no accidental access to other projects
- ✅ Simpler logic - no merge needed
- ✅ Removes confusion about template/example projects

**Drawbacks:**
- Cannot share example projects with users
- Could be addressed with "Import Template" feature later

**Recommendation:** ✅ **IMPLEMENT** - Simple change with clear UX improvement.

---

## Change 3: User Can "Manage" Shared Resources

### Option A: Hide/Unhide Shared Resources (Soft Delete)

#### Concept

User can hide specific shared resources from their view without deleting them.

**Storage:**
```
backend/data/users/{user-id}/preferences/
  hidden_plugins.json      -> ["plugin-id-1", "plugin-id-2"]
  hidden_provisioners.json -> ["prov-id-1"]
  hidden_triggers.json     -> ["trigger-id-1"]
  hidden_boxes.json        -> ["box-id-1", "box-id-2"]
```

**API Operations:**
- `POST /api/plugins/{id}/hide` - Hide shared plugin from user's view
- `POST /api/plugins/{id}/unhide` - Show hidden plugin again
- `GET /api/plugins` - Returns only non-hidden plugins

**Backend Logic:**
```python
class PluginService:
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.file_service = FileService()
        
        # Load hidden resources list
        if user_id:
            self.hidden_plugins = self._load_hidden_list()
        else:
            self.hidden_plugins = []
    
    def _load_hidden_list(self) -> List[str]:
        """Load list of hidden plugin IDs for this user."""
        prefs_dir = self.file_service.get_user_data_path(self.user_id, "preferences")
        hidden_file = prefs_dir / "hidden_plugins.json"
        
        if not hidden_file.exists():
            return []
        
        with open(hidden_file, 'r') as f:
            return json.load(f)
    
    def _save_hidden_list(self):
        """Save hidden plugins list."""
        prefs_dir = self.file_service.get_user_data_path(self.user_id, "preferences")
        prefs_dir.mkdir(parents=True, exist_ok=True)
        hidden_file = prefs_dir / "hidden_plugins.json"
        
        with open(hidden_file, 'w') as f:
            json.dump(self.hidden_plugins, f, indent=2)
    
    def list_plugins(self) -> List[PluginSummary]:
        """List plugins, excluding hidden ones."""
        all_plugins = self._load_all_plugins()  # Shared + user
        
        if not self.user_id:
            return all_plugins
        
        # Filter out hidden shared resources
        visible_plugins = [
            p for p in all_plugins
            if not (p.is_shared and p.id in self.hidden_plugins)
        ]
        
        return visible_plugins
    
    def hide_plugin(self, plugin_id: str) -> bool:
        """Hide a shared plugin."""
        # Verify it's a shared plugin
        plugin = self.get_plugin(plugin_id)
        if not plugin.is_shared:
            raise PluginServiceError("Cannot hide user-owned resources")
        
        if plugin_id not in self.hidden_plugins:
            self.hidden_plugins.append(plugin_id)
            self._save_hidden_list()
        
        return True
    
    def unhide_plugin(self, plugin_id: str) -> bool:
        """Unhide a shared plugin."""
        if plugin_id in self.hidden_plugins:
            self.hidden_plugins.remove(plugin_id)
            self._save_hidden_list()
        
        return True
    
    def list_hidden_plugins(self) -> List[PluginSummary]:
        """List all hidden plugins (for management UI)."""
        all_plugins = self._load_all_plugins()
        
        hidden = [
            p for p in all_plugins
            if p.is_shared and p.id in self.hidden_plugins
        ]
        
        return hidden
```

**Frontend Changes:**

Add "Hide" button next to shared resources:
```html
<!-- Settings page - Plugin card -->
<div x-show="plugin.is_shared">
  <button @click="hidePlugin(plugin.id)">
    👁️‍🗨️ Hide
  </button>
</div>

<!-- New "Hidden Resources" section -->
<div x-show="hiddenPlugins.length > 0">
  <h3>Hidden Shared Plugins</h3>
  <div x-for="plugin in hiddenPlugins">
    <span x-text="plugin.name"></span>
    <button @click="unhidePlugin(plugin.id)">
      👁️ Show
    </button>
  </div>
</div>
```

**API Endpoints:**
```python
@router.post("/plugins/{plugin_id}/hide")
async def hide_plugin(plugin_id: str, service: PluginService = Depends(get_service)):
    service.hide_plugin(plugin_id)
    return {"message": "Plugin hidden"}

@router.post("/plugins/{plugin_id}/unhide")
async def unhide_plugin(plugin_id: str, service: PluginService = Depends(get_service)):
    service.unhide_plugin(plugin_id)
    return {"message": "Plugin shown"}

@router.get("/plugins/hidden")
async def list_hidden_plugins(service: PluginService = Depends(get_service)):
    return service.list_hidden_plugins()
```

#### Option A: Complexity Assessment

**Effort:** MEDIUM  
**Components to Change:**
- Backend: 4 services (plugins, provisioners, triggers, boxes)
- Backend: New preference storage system
- Backend: 12 new API endpoints (3 per resource type)
- Frontend: Hide/unhide buttons
- Frontend: Hidden resources management UI

**Pros:**
- ✅ Non-destructive - user can always unhide
- ✅ Preserves shared resources exactly as-is
- ✅ Simple mental model: "I don't want to see this"
- ✅ Reversible action
- ✅ No data duplication

**Cons:**
- ❌ Hidden resources list could grow large
- ❌ Requires new preference storage mechanism
- ❌ Additional API endpoints for each resource type
- ❌ More complex list logic (filter hidden)
- ❌ Two places to manage resources (visible + hidden)
- ❌ Doesn't solve "I want my own version" use case

---

### Option B: Global Toggle + Copy Shared Resource

#### Concept

**Two separate features:**

1. **Global toggle to show/hide ALL shared resources**
   - Single toggle in Settings: "Show shared resources"
   - Stored in user preferences: `{"show_shared_resources": true}`
   - When false, all shared resources filtered out from lists

2. **"Copy to My Resources" button**
   - Creates physical copy of shared resource in user directory
   - User can then edit/customize their copy
   - Original shared resource unaffected

**Storage:**
```
backend/data/users/{user-id}/preferences/
  settings.json -> {"show_shared_resources": true}

backend/data/users/{user-id}/plugins/
  {copied-plugin-id}.json  # Physical copy, is_shared=false
```

**Backend Logic:**

```python
class PluginService:
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.file_service = FileService()
        self.show_shared = self._load_show_shared_preference()
    
    def _load_show_shared_preference(self) -> bool:
        """Load user's preference for showing shared resources."""
        if not self.user_id:
            return True  # Self-hosted mode: always show
        
        prefs_dir = self.file_service.get_user_data_path(self.user_id, "preferences")
        settings_file = prefs_dir / "settings.json"
        
        if not settings_file.exists():
            return True  # Default: show shared resources
        
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            return settings.get("show_shared_resources", True)
    
    def set_show_shared_preference(self, show: bool) -> bool:
        """Set user's preference for showing shared resources."""
        prefs_dir = self.file_service.get_user_data_path(self.user_id, "preferences")
        prefs_dir.mkdir(parents=True, exist_ok=True)
        settings_file = prefs_dir / "settings.json"
        
        # Load existing settings
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Update preference
        settings["show_shared_resources"] = show
        
        # Save
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        self.show_shared = show
        return True
    
    def list_plugins(self) -> List[PluginSummary]:
        """List plugins, respecting show_shared preference."""
        all_plugins = self._load_all_plugins()  # Shared + user
        
        if not self.user_id or self.show_shared:
            return all_plugins
        
        # Filter out shared resources
        user_plugins_only = [
            p for p in all_plugins
            if not p.is_shared
        ]
        
        return user_plugins_only
    
    def copy_shared_plugin(self, plugin_id: str) -> Plugin:
        """
        Create a copy of a shared plugin in user's directory.
        User can then edit/customize their copy.
        """
        # Load shared plugin
        shared_file = self.file_service.get_shared_data_path("plugins") / f"{plugin_id}.json"
        
        if not shared_file.exists():
            raise PluginServiceError(f"Shared plugin {plugin_id} not found")
        
        with open(shared_file, 'r') as f:
            plugin_data = json.load(f)
        
        # Generate new ID for the copy
        new_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Create copy with new metadata
        plugin_copy = {
            **plugin_data,
            "id": new_id,
            "name": f"{plugin_data['name']} (Copy)",  # Indicate it's a copy
            "is_shared": False,
            "owner_id": self.user_id,
            "created_at": now,
            "updated_at": now
        }
        
        # Save to user directory
        user_file = self.file_service.get_user_data_path(self.user_id, "plugins") / f"{new_id}.json"
        with open(user_file, 'w') as f:
            json.dump(plugin_copy, f, indent=2)
        
        return Plugin(**plugin_copy)
```

**API Endpoints:**

```python
# Global preference
@router.get("/preferences/show-shared")
async def get_show_shared_preference(user_id: str = Depends(get_current_user)):
    # Return preference for ALL resource types
    plugin_service = PluginService(user_id)
    return {"show_shared_resources": plugin_service.show_shared}

@router.put("/preferences/show-shared")
async def set_show_shared_preference(
    show: bool,
    user_id: str = Depends(get_current_user)
):
    # Update preference (affects all resource types)
    plugin_service = PluginService(user_id)
    plugin_service.set_show_shared_preference(show)
    return {"message": "Preference updated"}

# Copy shared resource
@router.post("/plugins/{plugin_id}/copy")
async def copy_shared_plugin(
    plugin_id: str,
    service: PluginService = Depends(get_service)
):
    copied_plugin = service.copy_shared_plugin(plugin_id)
    return copied_plugin

@router.post("/provisioners/{provisioner_id}/copy")
async def copy_shared_provisioner(...):
    # Same pattern

@router.post("/triggers/{trigger_id}/copy")
async def copy_shared_trigger(...):
    # Same pattern

@router.post("/boxes/{box_id}/copy")
async def copy_shared_box(...):
    # Same pattern
```

**Frontend Changes:**

```html
<!-- Settings page - Global toggle -->
<div class="settings-header">
  <label>
    <input type="checkbox" x-model="showSharedResources" 
           @change="updateShowSharedPreference()">
    Show shared resources
  </label>
</div>

<!-- Plugin card - Copy button (only on shared resources) -->
<div x-show="plugin.is_shared && showSharedResources">
  <button @click="copySharedPlugin(plugin.id)">
    📋 Copy to My Resources
  </button>
</div>

<!-- Alpine.js -->
<script>
Alpine.data('settingsData', () => ({
    showSharedResources: true,
    
    async init() {
        // Load preference
        const resp = await api.get('/api/preferences/show-shared');
        this.showSharedResources = resp.show_shared_resources;
        
        // Load resources based on preference
        await this.loadAllResources();
    },
    
    async updateShowSharedPreference() {
        await api.put('/api/preferences/show-shared', {
            show: this.showSharedResources
        });
        
        // Reload resources
        await this.loadAllResources();
    },
    
    async copySharedPlugin(pluginId) {
        const copied = await api.post(`/api/plugins/${pluginId}/copy`);
        
        // Add to list
        this.plugins.push(copied);
        
        // Show success message
        alert(`Plugin copied! You can now edit "${copied.name}"`);
    }
}));
</script>
```

#### Option B: Complexity Assessment

**Effort:** MEDIUM-LOW  
**Components to Change:**
- Backend: Preference storage (shared across all resource types)
- Backend: Copy methods in 4 services
- Backend: 6 API endpoints (2 for preferences + 4 for copy)
- Frontend: Global toggle switch
- Frontend: Copy buttons on shared resources

**Pros:**
- ✅ Simple mental model: "Show/hide all" + "Copy this one"
- ✅ Single preference affects all resource types
- ✅ Copy creates independent editable resource
- ✅ Solves "I want my own version" use case
- ✅ Fewer API endpoints than Option A
- ✅ No need to track individual hidden items
- ✅ Clean separation: shared (read-only) vs mine (editable)

**Cons:**
- ❌ All-or-nothing visibility (can't hide specific resources)
- ❌ Creates data duplication (copies)
- ❌ Copied resources might diverge from originals
- ❌ User needs to manually update their copies if shared resource changes

---

## Comparison: Option A vs Option B

| Aspect | Option A: Hide/Unhide | Option B: Global Toggle + Copy |
|--------|----------------------|-------------------------------|
| **Granularity** | Per-resource | All or nothing |
| **Complexity** | Higher | Lower |
| **API Endpoints** | 12 new endpoints | 6 new endpoints |
| **Storage** | Hidden lists per resource type | Single preference + copies |
| **Reversibility** | Fully reversible | Copy is permanent |
| **Editability** | Shared resources remain read-only | Copies are fully editable |
| **Data Duplication** | None | Yes (copies) |
| **Mental Model** | "Hide what I don't need" | "Show all or mine only" + "Make it mine" |
| **Use Case Fit** | "Too many shared resources" | "I want to customize a shared resource" |
| **Implementation Effort** | Medium | Medium-Low |

---

## Recommendations

### Change 1: Boxes to Individual Files
**Recommendation: ✅ IMPLEMENT**

- Clear architectural improvement
- Low risk, low effort
- Consistency across all resource types
- Better performance and maintainability

**Priority: HIGH**

---

### Change 2: Projects Not Shared
**Recommendation: ✅ IMPLEMENT**

- Simple change with clear UX benefit
- Better privacy and clarity
- Low risk, low effort
- Can add "Import Template" feature later if needed

**Priority: HIGH**

---

### Change 3: Manage Shared Resources
**Recommendation: ⚠️ OPTION B (with modifications)**

**Rationale:**

1. **Simpler implementation** - Single global preference, fewer endpoints
2. **Better UX** - Clear mental model: "shared (read-only)" vs "mine (editable)"
3. **Solves real use case** - Users can customize shared resources
4. **Cleaner code** - No need to track hidden lists per resource type

**Suggested Hybrid Approach:**

Implement **Option B** but with a **"favorite/star" system** for shared resources:

```python
# User preferences
{
  "show_shared_resources": true,
  "favorite_plugins": ["plugin-id-1", "plugin-id-2"],
  "favorite_provisioners": ["prov-id-1"]
}
```

**Frontend:**
- Global toggle: "Show shared resources" (default: true)
- Star icon on shared resources to mark favorites
- When toggle is OFF: Show ONLY favorites (not all shared resources)
- When toggle is ON: Show all shared resources (favorites shown first)

This gives:
- ✅ All-or-nothing simplicity
- ✅ Granular control via favorites
- ✅ Simple implementation (favorites list + copy functionality)
- ✅ Best of both worlds

**Priority: MEDIUM** (after Changes 1 & 2)

---

## Implementation Order

1. **Change 1: Boxes to individual files** (1-2 days)
   - Write migration script
   - Rewrite BoxService
   - Test thoroughly
   - Deploy

2. **Change 2: Projects not shared** (1 day)
   - Modify ProjectService.list_projects()
   - Remove shared project fallback logic
   - Test
   - Deploy

3. **Change 3: Hybrid Option B** (3-4 days)
   - Implement global show/hide toggle
   - Add copy functionality for all resource types
   - Add favorite/star system
   - Frontend UI for toggle, copy buttons, favorites
   - Test
   - Deploy

**Total Estimated Time: 5-7 days**

---

## Migration Path

### For Existing Users

1. **Boxes migration**: Automatic on server restart (script runs once)
2. **Projects**: No migration needed (existing projects stay in user directories)
3. **Preferences**: Default settings work for existing users (show_shared=true)

### Testing Checklist

- [ ] Boxes load correctly from individual files
- [ ] Box CRUD operations work
- [ ] Projects list shows only user's projects in public mode
- [ ] Projects list shows shared projects in self-hosted mode
- [ ] Global toggle filters shared resources correctly
- [ ] Copy button creates editable copy
- [ ] Favorite system works
- [ ] Performance is acceptable with many resources

---

## Potential Issues & Mitigations

### Issue 1: Migration Data Loss
**Risk**: Boxes migration script fails, data lost  
**Mitigation**: 
- Backup original `boxes.json` to `.backup`
- Test migration on copy first
- Rollback plan documented

### Issue 2: User Confusion (Global Toggle)
**Risk**: Users don't understand why shared resources disappeared  
**Mitigation**:
- Clear toggle label: "Show shared resources (plugins, boxes, etc.)"
- Tooltip explaining what it does
- Default to ON (show shared resources)

### Issue 3: Copied Resources Diverge
**Risk**: Shared resource updated, user's copy outdated  
**Mitigation**:
- Show "Updated" indicator on shared resources
- Optional: "Sync from shared" button to update copies
- Documentation explaining copy behavior

### Issue 4: Performance with Many Favorites
**Risk**: Loading favorites lists on every request  
**Mitigation**:
- Cache preferences in memory
- Load once per service instance
- Invalidate cache on preference update

---

## Alternative Considerations

### Alternative: Tags/Categories Instead of Hide/Favorite

Instead of hiding/favoriting, use tags:
- Shared resources have tags: "web-server", "database", "security"
- Users filter by tags
- More flexible than binary hide/show

**Pros:**
- More powerful filtering
- Better discovery

**Cons:**
- Requires tagging all shared resources
- More complex UI
- Doesn't solve "too many resources" problem

**Decision:** Not recommended for initial implementation. Consider for v2.

---

## Conclusion

**Implement all three changes in order:**

1. ✅ **Boxes to individual files** - Architectural cleanup, high value
2. ✅ **Projects not shared** - UX improvement, simple change
3. ✅ **Hybrid Option B** - Global toggle + copy + favorites for best UX

This provides a clean, consistent, and user-friendly resource management system with minimal complexity and maximum flexibility.
