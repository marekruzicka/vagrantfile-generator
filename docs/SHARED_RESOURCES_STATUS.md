# Shared Resources Management - Implementation Status

**Date:** November 14, 2025  
**Branch:** 001-multiuser-auth  
**Feature:** Change 3 - Hybrid Shared Resources Management (Option B + Favorites)

## Overview

This document describes the current implementation status of the hybrid shared resources management system, which provides users with control over visibility and customization of shared resources (plugins, provisioners, triggers, boxes) in multi-user mode.

## Backend Implementation ✅ COMPLETE

### Architecture

The backend implements a **hybrid approach** combining:
1. **Global toggle** - Show/hide ALL shared resources with a single preference
2. **Favorites system** - Mark specific shared resources to remain visible even when hidden
3. **Copy functionality** - Create editable user-owned copies of shared resources

### Core Components

#### 1. PreferenceService (NEW)
**File:** `backend/src/services/preference_service.py`

**Purpose:** Manages user preferences and favorites

**Data Model:**
```python
class UserPreferences(BaseModel):
    show_shared_resources: bool = True
    favorite_plugins: List[str] = Field(default_factory=list)
    favorite_provisioners: List[str] = Field(default_factory=list)
    favorite_triggers: List[str] = Field(default_factory=list)
    favorite_boxes: List[str] = Field(default_factory=list)
```

**Storage Location:** `/data/users/{user-id}/preferences/settings.json`

**Methods:**
- `get_preferences()` - Retrieve all user preferences
- `update_preferences(preferences)` - Save preferences
- `get_show_shared_resources()` - Get global toggle state
- `set_show_shared_resources(show)` - Update global toggle
- `get_favorites(resource_type)` - Get list of favorite IDs for a resource type
- `add_favorite(resource_type, resource_id)` - Add resource to favorites
- `remove_favorite(resource_type, resource_id)` - Remove from favorites
- `is_favorite(resource_type, resource_id)` - Check favorite status

**Status:** ✅ Fully implemented and tested

#### 2. Updated Resource Services

All four resource services have been updated with consistent functionality:

**Files:**
- `backend/src/services/plugin_service.py`
- `backend/src/services/global_provisioner_service.py`
- `backend/src/services/global_trigger_service.py`
- `backend/src/services/box_service.py`

**Changes Applied:**

1. **Constructor Enhancement:**
   ```python
   def __init__(self, base_directory: str = "data", user_id: Optional[str] = None, 
                show_shared: Optional[bool] = None)
   ```
   - Added `show_shared` parameter for testing overrides
   - Loads preference from PreferenceService by default

2. **Smart Filtering Logic:**
   ```python
   # Show resource if: NOT shared OR show_shared=True OR is_favorite
   if resource.is_shared and not self.show_shared and resource.id not in favorite_ids:
       continue
   ```

3. **Copy Methods:**
   - `copy_shared_plugin(plugin_id)` → Creates user-owned copy
   - `copy_shared_provisioner(provisioner_id)` → Creates user-owned copy
   - `copy_shared_trigger(trigger_id)` → Creates user-owned copy
   - `copy_shared_box(box_id)` → Creates user-owned copy

   **Copy Behavior:**
   - Generates new UUID for the copy
   - Appends " (Copy)" to the name
   - Sets `is_shared=False` and `owner_id=user_id`
   - Saves to user's directory
   - User can edit/delete their copy

**Status:** ✅ Fully implemented across all 4 services

#### 3. API Endpoints (NEW)

**File:** `backend/src/api/config.py`

**Preference Endpoints:**
```
GET  /api/config/preferences
PUT  /api/config/preferences
GET  /api/config/preferences/show-shared
PUT  /api/config/preferences/show-shared
```

**Favorites Endpoints:**
```
GET  /api/config/preferences/favorites/{type}
POST /api/config/preferences/favorites/{type}/add
POST /api/config/preferences/favorites/{type}/remove
GET  /api/config/preferences/favorites/{type}/check/{id}
```
Where `{type}` is: `plugins`, `provisioners`, `triggers`, or `boxes`

**Copy Endpoints:**
```
POST /api/plugins/{id}/copy
POST /api/provisioners/{id}/copy
POST /api/triggers/{id}/copy
POST /api/boxes/{id}/copy
```

**Authentication:** All endpoints require valid JWT token (blocked in self-hosted mode)

**Status:** ✅ All 12 endpoints implemented and tested

#### 4. Model Updates

Updated summary models to include ownership fields:

**Files Updated:**
- `backend/src/models/plugin.py` - PluginSummary
- `backend/src/models/box.py` - Box and BoxSummary
- `backend/src/models/global_provisioner.py` - GlobalProvisionerSummary
- `backend/src/models/global_trigger.py` - GlobalTriggerSummary

**Fields Added:**
```python
is_shared: Optional[bool] = Field(default=False)
owner_id: Optional[str] = Field(default=None)
```

**Status:** ✅ Complete

### Testing Results ✅

Comprehensive testing performed via direct Python execution in container:

#### State 1: Show All (show_shared=True)
```
Plugins:      7 total (4 shared + 3 user)
Provisioners: 4 total (3 shared + 1 user)
Triggers:     3 total (2 shared + 1 user)
Boxes:        8 total (5 shared + 3 user)
```

#### State 2: Hide Shared (show_shared=False, no favorites)
```
Plugins:      3 total (0 shared + 3 user)
Provisioners: 1 total (0 shared + 1 user)
Triggers:     1 total (0 shared + 1 user)
Boxes:        3 total (0 shared + 3 user)
```

#### State 3: Hide Shared WITH Favorites
```
Plugins:      5 total (2 shared ⭐ + 3 user)
Provisioners: 2 total (1 shared ⭐ + 1 user)
Triggers:     1 total (0 shared + 1 user)
Boxes:        3 total (0 shared + 3 user)
```

**Key Insight:** Favorites remain visible even when show_shared=False ✅

**Copy Functionality Tested:**
- ✅ Plugin copy: Created "vagrant-hostmanager (Copy)" with new ID
- ✅ Provisioner copy: Created "APT update (Copy)"
- ✅ Trigger copy: Created "RHC Connect (Copy)"
- ✅ Box copy: Created "generic/rhel9 (Copy)"
- ✅ All copies have is_shared=False, owner_id=user_id
- ✅ Copies are editable by user

**API Security Tested:**
- ✅ Cannot edit shared resources (403/400 errors)
- ✅ Cannot delete shared resources (403/400 errors)
- ✅ Copy blocked in self-hosted mode
- ✅ All endpoints require authentication

## Frontend Implementation ⚠️ INCOMPLETE

### Current Status

Only **minimal visual distinction** has been implemented for boxes:

**File:** `frontend/src/index.html` (Boxes section only)

**What Works:**
```html
<!-- Amber border/background for shared boxes -->
:class="box.is_shared ? 'border-amber-200 bg-amber-50/20' : ''"

<!-- "Shared" badge display -->
<span x-show="box.is_shared" class="shared-resource-badge">
    🔒 Shared
</span>

<!-- Hide edit/delete buttons for shared boxes -->
<div x-show="!box.is_shared" class="flex space-x-1">
    <!-- Edit/Delete buttons -->
</div>
```

### Missing Frontend Features ❌

The following features are **NOT implemented** in the frontend:

1. **❌ Global Toggle UI**
   - No settings switch to show/hide all shared resources
   - Users cannot control the show_shared_resources preference

2. **❌ Favorites/Star Buttons**
   - No star icons on shared resources
   - Users cannot mark favorites from UI
   - No visual indication of favorited status

3. **❌ Copy Buttons**
   - No "Copy to My Resources" buttons on shared resources
   - Users cannot create editable copies from UI

4. **❌ API Integration**
   - No calls to new preference endpoints
   - No calls to favorites endpoints
   - No calls to copy endpoints

5. **❌ Complete Visual Distinction**
   - Only boxes have the amber border/badge
   - Plugins, provisioners, and triggers lack visual distinction

6. **❌ Dynamic Filtering**
   - Lists don't update when preferences change
   - No real-time reflection of favorite status

## Required Frontend Work

### 1. Settings Page Toggle

Add global show/hide control at the top of Settings view:

```html
<div class="bg-white rounded-lg shadow-sm p-6 mb-6">
    <div class="flex items-center justify-between">
        <div>
            <h3 class="text-lg font-semibold">Shared Resources</h3>
            <p class="text-sm text-gray-500">
                Control visibility of shared plugins, boxes, provisioners, and triggers
            </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" 
                   x-model="showSharedResources" 
                   @change="updateShowSharedPreference()"
                   class="sr-only peer">
            <div class="toggle-switch"></div>
            <span x-text="showSharedResources ? 'Showing' : 'Hidden'"></span>
        </label>
    </div>
</div>
```

### 2. Star and Copy Buttons

Add to each resource card (plugins, provisioners, triggers, boxes):

```html
<!-- Star button (for favorites) -->
<button x-show="resource.is_shared"
        @click="toggleFavorite('plugins', resource.id)"
        :class="isFavorite('plugins', resource.id) ? 'text-yellow-500' : 'text-gray-400'"
        class="p-2 hover:text-yellow-500">
    <svg class="w-5 h-5" :fill="isFavorite('plugins', resource.id) ? 'currentColor' : 'none'">
        <!-- Star icon SVG -->
    </svg>
</button>

<!-- Copy button -->
<button x-show="resource.is_shared && showSharedResources"
        @click="copySharedResource('plugins', resource.id)"
        class="p-2 text-gray-400 hover:text-blue-600"
        title="Copy to My Resources">
    <svg class="w-5 h-5">
        <!-- Copy icon SVG -->
    </svg>
</button>
```

### 3. Alpine.js Data & Methods

Add to settings component (likely in `js/app.js`):

```javascript
Alpine.data('settingsData', () => ({
    showSharedResources: true,
    favorites: {
        plugins: [],
        provisioners: [],
        triggers: [],
        boxes: []
    },
    
    async init() {
        await this.loadPreferences();
        await this.loadFavorites();
        await this.loadAllResources();
    },
    
    async loadPreferences() {
        const response = await api.get('/api/config/preferences/show-shared');
        this.showSharedResources = response.show_shared_resources;
    },
    
    async loadFavorites() {
        const types = ['plugins', 'provisioners', 'triggers', 'boxes'];
        for (const type of types) {
            const response = await api.get(`/api/config/preferences/favorites/${type}`);
            this.favorites[type] = response.favorites || [];
        }
    },
    
    async updateShowSharedPreference() {
        await api.put('/api/config/preferences/show-shared', {
            show_shared_resources: this.showSharedResources
        });
        await this.loadAllResources(); // Reload to reflect changes
    },
    
    isFavorite(type, resourceId) {
        return this.favorites[type].includes(resourceId);
    },
    
    async toggleFavorite(type, resourceId) {
        const isFav = this.isFavorite(type, resourceId);
        const action = isFav ? 'remove' : 'add';
        
        await api.post(`/api/config/preferences/favorites/${type}/${action}`, {
            resource_id: resourceId
        });
        
        // Update local state
        if (isFav) {
            this.favorites[type] = this.favorites[type].filter(id => id !== resourceId);
        } else {
            this.favorites[type].push(resourceId);
        }
        
        await this.loadAllResources(); // Reload to reflect favorite filtering
    },
    
    async copySharedResource(type, resourceId) {
        const copiedResource = await api.post(`/api/${type}/${resourceId}/copy`);
        this[type].push(copiedResource); // Add to local list
        this.showNotification(`Resource copied! You can now edit "${copiedResource.name}"`);
    }
}));
```

### 4. Apply Visual Distinction to All Resources

Extend the amber border/badge pattern from boxes to:
- Plugins section
- Provisioners section
- Triggers section

## Related Changes Implemented

### Change 2: Projects Not Shared ✅ COMPLETE

**File:** `backend/src/services/project_service.py`

**Modification:** `list_projects()` method now:
- **Public mode** (user_id set): Only shows user's own projects
- **Self-hosted mode** (user_id=None): Shows projects from shared directory
- No longer merges shared and user projects in public mode

**Benefit:** Clearer UX, better privacy, no confusion about template projects

**Status:** ✅ Complete

### Change 1: Boxes Migration Script ✅ PREPARED

**File:** `backend/scripts/migrate_boxes.py`

**Purpose:** Prepare for migrating boxes from single `boxes.json` to individual files

**Status:** ✅ Script created, not yet executed

**Note:** This change is **not included** in the current commit but is prepared for future implementation.

## Documentation

### Created Documents

1. **docs/IMPLEMENTATION_ANALYSIS.md** ✅
   - Complete analysis of all 3 proposed changes
   - Detailed comparison of Option A vs Option B
   - Implementation recommendations
   - Migration path and testing checklist

2. **docs/SHARED_RESOURCES.md** ✅
   - Guide to shared resources in public mode
   - Backend implementation details
   - Frontend patterns (aspirational - not yet implemented)
   - Security model and permission matrix
   - Testing checklist

3. **docs/SHARED_RESOURCES_STATUS.md** ✅ (This document)
   - Current implementation status
   - What's complete vs incomplete
   - Required frontend work

## Infrastructure Updates

### Container Configuration

**File:** `compose-prod.yml`

**Changes:**
- Simplified to use `.env` file for all environment variables
- Enabled backend data persistence with named volume
- Removed redundant environment variable declarations

**Status:** ✅ Complete

## Summary

### What's Working ✅

- ✅ Backend API fully implemented (12 new endpoints)
- ✅ PreferenceService with all CRUD operations
- ✅ Smart filtering across all 4 resource services
- ✅ Copy functionality for all resource types
- ✅ Favorites management for all resource types
- ✅ All backend features tested and verified
- ✅ Projects not shared in public mode
- ✅ Complete documentation

### What's Missing ❌

- ❌ Frontend global toggle UI
- ❌ Frontend star/favorite buttons
- ❌ Frontend copy buttons
- ❌ Frontend API integration
- ❌ Visual distinction for plugins/provisioners/triggers (only boxes done)
- ❌ Dynamic list updates based on preferences

### Next Steps

1. **Immediate Priority:** Implement frontend UI components
   - Add global toggle to Settings page
   - Add star buttons to all resource cards
   - Add copy buttons to all shared resources
   - Integrate with backend APIs

2. **Secondary Priority:** Apply visual distinction
   - Extend amber border/badge pattern to all resource types
   - Ensure consistent UX across plugins, provisioners, triggers, boxes

3. **Testing:** End-to-end user flow testing
   - Toggle shared resources visibility
   - Mark/unmark favorites
   - Copy shared resources and verify editability
   - Verify favorites remain visible when shared hidden

## Commit Status

**Ready to Commit:** ✅ Backend implementation complete

**Commit Message:**
```
feat: implement hybrid shared resources management (Option B + favorites)

Backend implementation complete with 12 new API endpoints, preference
service, smart filtering, and copy functionality across all 4 resource
types. Frontend implementation pending.
```

**Files Staged:**
- Backend services (4 files)
- API endpoints (6 files)
- Models (4 files)
- Documentation (2 files)
- Infrastructure (1 file)
- Migration script (1 file)

**Total Changes:**
- 18 files modified
- 1 file created (PreferenceService)
- 1 file created (migration script)
- 2 documentation files created
