# Copy-on-Write Implementation Plan for Shared Resources

**Status**: Design Document  
**Date**: 2025-11-15  
**Branch**: 001-multiuser-auth  

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Current Implementation Status](#current-implementation-status)
4. [Core Requirement: Seamless Editing](#core-requirement-seamless-editing)
5. [Edge Case: Existing Copies Detection](#edge-case-existing-copies-detection)
6. [Edge Case: Copy-as-Template Problem](#edge-case-copy-as-template-problem)
7. [Recommended Solution](#recommended-solution)
8. [Implementation Phases](#implementation-phases)
9. [Technical Specifications](#technical-specifications)
10. [Deployment Mode Compatibility](#deployment-mode-compatibility)

---

## Executive Summary

**Goal**: Enable users to seamlessly edit read-only shared resources (plugins, provisioners, triggers) within their projects without complex manual workflows.

**Approach**: Copy-on-write pattern where clicking "Edit" on a shared resource automatically:
1. Creates a user-owned copy
2. Replaces the shared resource reference in the project
3. Opens the edit modal for the new copy

**Key Challenge**: Preventing false positives when detecting existing copies (users often misuse "Copy" as "Create New").

**Recommended Solution**: Three-phase implementation:
- Phase 1: Smart filtering of existing copies
- Phase 2: Intent-based copying (customize vs template)
- Phase 3: Manual unlink capability

---

## Problem Statement

### Current Situation

When a project references a shared resource:
```json
{
  "id": "my-project",
  "global_plugins": ["shared-plugin-123"]
}
```

**Problems:**
1. Users cannot click "Edit" on shared resources in project view (button disabled/hidden)
2. If users manually copy in Settings, the project still references the shared ID
3. Manual replacement workflow is complex and error-prone
4. Separate "Copy" button creates confusion about workflow

### User Pain Points

**Scenario**: User wants to customize "vagrant-vbguest" plugin for their project

**Current workflow (broken):**
1. Go to Settings → Plugins
2. Find "vagrant-vbguest" in shared resources
3. Click "Copy" → creates "vagrant-vbguest (Copy)"
4. Go back to Project
5. ❌ Project still uses shared version
6. ❌ No clear way to replace shared with copy

**Desired workflow:**
1. In Project view, click "Edit" on "vagrant-vbguest"
2. ✅ Automatically creates copy + replaces in project + opens editor
3. ✅ Make changes and save
4. ✅ Done

---

## Current Implementation Status

### ✅ Backend: Fully Implemented

**Resource Models** include `source_id` field:
- ✅ `Plugin` model has `source_id`, `is_shared`, `owner_id`
- ✅ `GlobalProvisioner` model has `source_id`, `is_shared`, `owner_id`
- ✅ `GlobalTrigger` model has `source_id`, `is_shared`, `owner_id`
- ✅ `Box` model has `source_id`, `is_shared`, `owner_id`

**Copy Endpoints** (standalone copy to user library):
```
POST /api/plugins/{id}/copy
POST /api/provisioners/{id}/copy
POST /api/triggers/{id}/copy
POST /api/boxes/{id}/copy
```

**Copy-and-Replace Endpoints** (atomic operation):
```
POST /api/projects/{project_id}/plugins/{id}/copy
POST /api/projects/{project_id}/provisioners/{id}/copy
POST /api/projects/{project_id}/triggers/{id}/copy
```

Returns:
```json
{
  "old_id": "shared-plugin-123",
  "new_id": "user-plugin-456",
  "project_updated": true
}
```

**Replace Endpoints** (use existing copy):
```
POST /api/projects/{project_id}/plugins/{old_id}/replace/{new_id}
POST /api/projects/{project_id}/provisioners/{old_id}/replace/{new_id}
POST /api/projects/{project_id}/triggers/{old_id}/replace/{new_id}
```

**Helper Endpoints** (find existing copies):
```
GET /api/plugins/copies-of/{source_id}
GET /api/provisioners/copies-of/{source_id}
GET /api/triggers/copies-of/{source_id}
GET /api/boxes/copies-of/{source_id}
```

### ⚠️ Frontend: Partially Implemented

**What works:**
- ✅ Green "Copy" button visible for shared resources
- ✅ `copySharedResource()` function calls copy API
- ✅ Adds copied resource to local lists

**What's missing:**
- ❌ Edit modals don't open for shared resources
- ❌ No copy-on-write when clicking Edit
- ❌ No detection/handling of existing copies
- ❌ No automatic replacement in projects
- ❌ No visual indicators for shared vs user-owned resources

---

## Core Requirement: Seamless Editing

### User Experience Flow

```
STEP 1: Project Detail View
┌──────────────────────────────────┐
│ Plugins in Project               │
│                                  │
│ ┌────────────────────────────┐  │
│ │ 📦 vagrant-vbguest         │  │
│ │ Shared resource     [Edit] │  │ ← User clicks Edit
│ └────────────────────────────┘  │
└──────────────────────────────────┘

STEP 2: Brief Loading (200-500ms)
┌──────────────────────────────────┐
│ Creating your copy...            │
└──────────────────────────────────┘

STEP 3: Edit Modal Opens
┌──────────────────────────────────┐
│ Edit Plugin                 [×]  │
├──────────────────────────────────┤
│ ℹ️ This is your copy of a       │ ← Info banner
│    shared resource               │
├──────────────────────────────────┤
│ Name: vagrant-vbguest (Copy)     │ ← Auto-renamed
│ Description: [...editable...]    │
│ ...                              │
│                                  │
│      [Cancel]  [Save Changes]    │
└──────────────────────────────────┘

STEP 4: After Save
┌──────────────────────────────────┐
│ ✅ Plugin updated successfully!  │
└──────────────────────────────────┘

Plugins in Project:
┌──────────────────────────────────┐
│ 📦 vagrant-vbguest (Copy)        │
│ Your resource           [Edit]   │ ← No longer "shared"
└──────────────────────────────────┘
```

### Backend State Changes

**Before:**
```json
// Project
{
  "global_plugins": ["shared-plugin-123"]
}

// Shared resource: shared-plugin-123.json
{
  "id": "shared-plugin-123",
  "name": "vagrant-vbguest",
  "is_shared": true,
  "owner_id": null
}
```

**After:**
```json
// Project (atomically updated)
{
  "global_plugins": ["user-plugin-456"]
}

// User's copy: user-plugin-456.json
{
  "id": "user-plugin-456",
  "name": "vagrant-vbguest (Copy)",
  "is_shared": false,
  "owner_id": "user-abc",
  "source_id": "shared-plugin-123"  // Tracks provenance
}
```

### Implementation Code

```javascript
// Frontend: app.js
async handleEditSharedResource(type, resourceId) {
    try {
        // Show loading
        this.setInfo('Creating your copy...');
        
        // Atomic copy + replace
        const result = await api.copyAndReplaceInProject(
            this.currentProject.id,
            type,
            resourceId
        );
        
        // Update local state
        this.replaceResourceInCurrentProject(type, result.old_id, result.new_id);
        
        // Load the new copy
        const newResource = await api.getResource(type, result.new_id);
        
        // Open edit modal
        this.openEditModal(type, newResource);
        
        this.setSuccess(`Copy created! Edit "${newResource.name}"`);
        
    } catch (error) {
        this.setError('Failed to copy: ' + error.message);
    }
}

replaceResourceInCurrentProject(type, oldId, newId) {
    const arrayName = `global_${type}s`;
    const index = this.currentProject[arrayName].indexOf(oldId);
    if (index !== -1) {
        this.currentProject[arrayName][index] = newId;
    }
}
```

### Key "Seamless" Aspects

1. ✅ **Single Click** - No intermediate dialogs
2. ✅ **Atomic Operation** - Copy + replace in one backend call
3. ✅ **Instant Feedback** - Modal opens ~300ms after click
4. ✅ **Transparent Naming** - `(Copy)` suffix shows ownership
5. ✅ **Auto-Update** - Project reference replaced automatically
6. ✅ **Standard Workflow** - Save works normally after modal opens

---

## Edge Case: Existing Copies Detection

### The Problem

**Timeline:**
1. Week 1: User copies "vagrant-vbguest" in Settings → "vagrant-vbguest (Copy)"
2. Week 2: User creates Project A → adds shared "vagrant-vbguest"
3. Week 3: User clicks Edit on "vagrant-vbguest" in Project A

**Question**: Should we:
- **Option A**: Create another copy → "vagrant-vbguest (Copy 2)"
- **Option B**: Offer to reuse existing "vagrant-vbguest (Copy)"
- **Option C**: Auto-use existing copy without asking

### Recommended Solution: Smart Choice Modal

```javascript
async handleEditSharedResource(type, resourceId) {
    // Check for existing copies
    const existingCopies = await api.getResourceCopies(type, resourceId);
    
    if (existingCopies.length === 0) {
        // No copies → seamless create
        await this.createCopyAndEdit(type, resourceId);
        
    } else if (existingCopies.length === 1) {
        // One copy → smart confirmation
        this.showSingleCopyConfirmation(type, resourceId, existingCopies[0]);
        
    } else {
        // Multiple copies → full choice modal
        this.showCopyChoiceModal(type, resourceId, existingCopies);
    }
}
```

### Choice Modal UI

```
┌──────────────────────────────────────────────────┐
│ Choose How to Edit "vagrant-vbguest"      [×]   │
├──────────────────────────────────────────────────┤
│ You already have copies of this resource:       │
│                                                  │
│ ○ Use existing copy:                            │
│   ┌──────────────────────────────────────────┐  │
│   │ ● vagrant-vbguest (Copy)                 │  │
│   │   Created: Nov 1, 2025                   │  │
│   └──────────────────────────────────────────┘  │
│                                                  │
│   ┌──────────────────────────────────────────┐  │
│   │ ○ My Custom VBGuest                      │  │
│   │   Created: Nov 8, 2025                   │  │
│   └──────────────────────────────────────────┘  │
│                                                  │
│ ○ Create a new variation                        │
│   (Will be named "vagrant-vbguest (Copy 3)")    │
│                                                  │
│              [Cancel]  [Continue]                │
└──────────────────────────────────────────────────┘
```

### User Actions

| **User Choice** | **API Call** | **Result** |
|----------------|--------------|-----------|
| Use existing copy | `POST /projects/{pid}/plugins/{shared-id}/replace/{existing-copy-id}` | Replaces in project, edits existing copy |
| Create new | `POST /projects/{pid}/plugins/{shared-id}/copy` | Creates new copy, replaces in project |

### Benefits

1. ✅ **Prevents Wasted Work** - User sees they already have a copy
2. ✅ **Supports Variations** - User can create multiple specialized versions
3. ✅ **Smart Defaults** - First copy is seamless, subsequent offer choice
4. ✅ **Transparency** - User knows what copies exist

---

## Edge Case: Copy-as-Template Problem

### The Problem

Users often misuse "Copy" as "Create New" when no "Create New" button exists.

**Scenario:**
1. User copies shared provisioner "Install Docker"
2. Renames to "Install PostgreSQL"
3. Replaces entire script content
4. Saves

**Result:**
```json
{
  "id": "user-copy-123",
  "name": "Install PostgreSQL",
  "shell_config": {
    "script": "apt-get install postgresql"  // ← Completely different
  },
  "source_id": "shared-docker-install",  // ← ⚠️ MISLEADING!
  "is_shared": false,
  "owner_id": "user-abc"
}
```

### Impact: False Positive Detection

When user later clicks Edit on shared "Install Docker":

```
GET /api/provisioners/copies-of/shared-docker-install

Response:
[
  {id: "user-copy-1", name: "Install PostgreSQL"},  // ❌ NOT related!
  {id: "user-copy-2", name: "My Docker Setup"}      // ✅ Actually related
]
```

**Choice Modal shows:**
```
You have existing copies:
  ○ Install PostgreSQL    ← ⚠️ CONFUSING! Not Docker-related
  ○ My Docker Setup       ← ✅ Makes sense
```

### Root Cause

The app has **two legitimate use cases**:

| **Use Case** | **Intent** | **Should Track source_id?** |
|-------------|-----------|---------------------------|
| **Copy-to-Customize** | "I want to edit THIS resource" | ✅ YES |
| **Copy-as-Template** | "I want a starting point for NEW resource" | ❌ NO |

Currently, backend cannot distinguish between these intents.

### Solution Options Comparison

#### Option A: Auto-Clear on Divergence

**Approach**: Backend detects when copy diverges significantly and auto-clears `source_id`

```python
def update_provisioner(self, provisioner_id: str, update_data: dict):
    provisioner = self.get_provisioner(provisioner_id)
    
    if provisioner.source_id:
        divergence = calculate_divergence(provisioner, update_data)
        if divergence > 0.7:  # >70% different
            update_data["source_id"] = None
```

**Pros**: ✅ Automatic, no user action  
**Cons**: ⚠️ Heuristics unreliable, might unlink legitimate customizations

#### Option B: Manual Unlink UI

**Approach**: Add "Unlink from original" button in edit modal

```html
<div x-show="resource.source_id">
  📋 Copy of: <strong x-text="originalName"></strong>
  <button @click="unlinkFromOriginal()">Unlink</button>
</div>
```

**Pros**: ✅ User control, explicit  
**Cons**: ⚠️ Requires user awareness, rarely used

#### Option C: Intent-Based Copying ⭐ (Recommended)

**Approach**: User preferences control advanced copy behavior

**Settings Page → Advanced Section:**
```html
<!-- Settings → Advanced Preferences -->
<div class="preferences-section">
  <h3>Copy Behavior</h3>
  
  <label class="checkbox-label">
    <input type="checkbox" x-model="preferences.enableIntentBasedCopying">
    <div>
      <strong>Enable intent-based copying</strong>
      <p class="text-sm text-gray-600">
        Show "Copy to Customize" vs "Use as Template" options when copying shared resources.
        Templates won't be suggested when editing the original resource.
      </p>
    </div>
  </label>
  
  <label class="checkbox-label">
    <input type="checkbox" x-model="preferences.showSourceProvenance">
    <div>
      <strong>Show resource provenance</strong>
      <p class="text-sm text-gray-600">
        Display "Based on: [Original Resource]" for copied resources and allow unlinking.
      </p>
    </div>
  </label>
  
  <label class="checkbox-label">
    <input type="checkbox" x-model="preferences.alwaysShowCopyChoices">
    <div>
      <strong>Always show copy choices</strong>
      <p class="text-sm text-gray-600">
        Ask before creating new copies even if you don't have existing ones.
      </p>
    </div>
  </label>
</div>
```

**Copy Button Behavior (Adaptive UI):**

When `enableIntentBasedCopying = false` (default):
```html
<!-- Simple single button -->
<button @click="copyResource(id, 'customize')">
  📋 Copy
</button>
```

When `enableIntentBasedCopying = true`:
```html
<!-- Dropdown menu or modal choice -->
<button @click="showCopyIntentMenu(id)">
  📋 Copy ▼
</button>

<!-- Dropdown options -->
<div class="copy-intent-menu">
  <button @click="copyResource(id, 'customize')">
    Copy to Customize
  </button>
  <button @click="copyResource(id, 'template')">
    Use as Template
  </button>
</div>
```

**Backend (unchanged):**
```python
def copy_shared_provisioner(
    self, 
    provisioner_id: str, 
    copy_intent: str = "customize"  # Default maintains backward compatibility
):
    plugin_copy = {
        **plugin_data,
        "id": new_id,
        "name": f"{plugin_data['name']} (Copy)",
        "is_shared": False,
        "owner_id": self.user_id,
        
        # Only set source_id for "customize" intent
        "source_id": plugin_id if copy_intent == "customize" else None,
    }
```

**Pros**: 
- ✅ Simple UI for basic users (just "Copy")
- ✅ Power features available when needed
- ✅ Progressive disclosure - doesn't overwhelm new users
- ✅ Self-documenting (tooltips explain behavior)
- ✅ No forced workflow changes

**Cons**: 
- ⚠️ Requires user preferences storage
- ⚠️ Slightly more complex implementation

#### Option D: Smart Filtering (Pragmatic)

**Approach**: Filter copy detection results by name similarity

```javascript
async getRelevantCopies(type, resourceId) {
    const allCopies = await api.getResourceCopies(type, resourceId);
    const original = await api.getResource(type, resourceId);
    
    return allCopies.filter(copy => {
        // Check if copy name still resembles original
        const similarity = calculateNameSimilarity(original.name, copy.name);
        const daysSinceCreated = getDaysSince(copy.created_at);
        
        // Show if name >40% similar OR created within 7 days
        return similarity > 0.4 || daysSinceCreated < 7;
    });
}
```

**Pros**: ✅ No backend changes, works immediately  
**Cons**: ⚠️ Heuristics might filter legitimate copies

---

## Recommended Solution

### Three-Phase Approach with Progressive Enhancement

**Philosophy**: Simple by default, powerful when needed.

Instead of forcing all users through complex workflows, we implement a **preference-based progressive disclosure** pattern:

1. **Default Experience** (90% of users):
   - Single "Copy" button (simple)
   - Seamless copy-on-write editing
   - Smart filtering hides divergent copies
   - No complexity, no learning curve

2. **Advanced Experience** (10% of power users):
   - Optional: Intent-based copying (customize vs template)
   - Optional: Source provenance display with unlink
   - Optional: Always show copy choices
   - Full control when needed

**Why This Works:**
- ✅ **No forced workflows** - Users aren't confronted with "Copy to Customize" vs "Use as Template" if they don't care
- ✅ **Self-documenting** - Settings page explains what each feature does
- ✅ **Gradual learning** - Users discover advanced features organically
- ✅ **Backward compatible** - Defaults match current simple behavior
- ✅ **Professional UX** - Follows industry patterns (Gmail, VS Code, etc.)

---

### Implementation Approach

The implementation is broken into **three sequential phases**, each building on the previous:

#### **Phase 1: Core Copy-on-Write (Essential)** 
- **Timeline**: Week 1
- **Effort**: ~2-3 days (frontend only)
- **Goal**: Enable seamless editing of shared resources in projects

**What gets implemented:**
- Enable Edit button for shared resources
- Implement `handleEditSharedResource()` function
- Add visual badge/indicator for shared resources
- Add info banner in edit modal when editing copy
- Update project state after copy-and-replace
- Remove/hide standalone Copy button for shared resources in project views

**Key deliverable**: Users can click Edit on shared plugin → copy created → project updated → modal opens

---

#### **Phase 2: Existing Copy Detection with Smart Filtering (Important)**
- **Timeline**: Week 2
- **Effort**: ~3-5 days (frontend only)
- **Goal**: Prevent duplicate copies when user already has one

**What gets implemented:**

*Smart Filtering Logic:*
```javascript
// Filter copies by name similarity
function calculateNameSimilarity(name1, name2) {
    const words1 = name1.toLowerCase().split(/\s+/);
    const words2 = name2.toLowerCase().split(/\s+/);
    
    const matches = words1.filter(w1 => 
        words2.some(w2 => w1.includes(w2) || w2.includes(w1))
    );
    
    return matches.length / words1.length;
}

async getRelevantCopies(type, resourceId) {
    const allCopies = await api.getResourceCopies(type, resourceId);
    const original = await api.getResource(type, resourceId);
    
    return allCopies.filter(copy => {
        const similarity = calculateNameSimilarity(original.name, copy.name);
        return similarity > 0.5;  // Show if >50% of words match
    });
}
```

*Copy Choice Modal:*
- Create copy choice modal component
- Add logic to show modal when relevant copies exist
- Implement "use existing" vs "create new" flows
- Add single-copy confirmation variant

**Key deliverable**: If user has existing copies, they're shown a choice; divergent copies are filtered out

---

#### **Phase 3: Intent-Based Copying with Preferences (Nice-to-Have)**
- **Timeline**: Week 3
- **Effort**: ~5-7 days (backend + frontend + preferences)
- **Goal**: Solve root cause with opt-in advanced features

#### **Phase 3: Intent-Based Copying with Preferences (Nice-to-Have)**
- **Timeline**: Week 3
- **Effort**: ~5-7 days (backend + frontend + preferences)
- **Goal**: Solve root cause with opt-in advanced features

**What gets implemented:**

**Preferences Storage:**
```javascript
// User preferences model
{
  enableIntentBasedCopying: false,     // Default: simple copy
  showSourceProvenance: false,         // Default: hide source info
  alwaysShowCopyChoices: false,        // Default: seamless first copy
  autoFilterDivergentCopies: true      // Default: smart filtering enabled
}
```

**Backend Changes:**
```python
# Copy endpoint accepts intent (defaults to "customize")
@router.post("/provisioners/{provisioner_id}/copy")
async def copy_provisioner(
    provisioner_id: str,
    copy_intent: str = Query(default="customize", regex="^(customize|template)$"),
    ...
):
    copied = provisioner_service.copy_shared_provisioner(
        provisioner_id, 
        copy_intent=copy_intent
    )
    return copied

# Preferences endpoint
@router.get("/preferences")
async def get_preferences(user_id: str = Depends(get_current_user)):
    return preference_service.get_preferences(user_id)

@router.put("/preferences")
async def update_preferences(
    prefs: PreferencesUpdate,
    user_id: str = Depends(get_current_user)
):
    return preference_service.update_preferences(user_id, prefs)
```

**Frontend Changes:**

*Settings Page - Advanced Section:*
```html
<div class="settings-section">
  <h3>Advanced Copy Settings</h3>
  
  <label>
    <input type="checkbox" x-model="preferences.enableIntentBasedCopying">
    Enable intent-based copying
    <span class="help-text">Show copy options (customize vs template)</span>
  </label>
  
  <label>
    <input type="checkbox" x-model="preferences.showSourceProvenance">
    Show resource provenance
    <span class="help-text">Display original source and unlink option</span>
  </label>
</div>
```

*Adaptive Copy Button:*
```javascript
// Simple mode (default)
<button @click="copyResource(id)" x-show="!preferences.enableIntentBasedCopying">
  Copy
</button>

// Advanced mode (opt-in)
<div x-show="preferences.enableIntentBasedCopying">
  <button @click="showCopyIntentMenu(id)">
    Copy ▼
  </button>
  <!-- Dropdown: "Copy to Customize" / "Use as Template" -->
</div>
```

*Source Provenance Display (when enabled):*
```html
<!-- In edit modal - only shown when preference enabled -->
<div x-show="editingResource.source_id && preferences.showSourceProvenance" 
     class="bg-blue-50 p-3 rounded border border-blue-200">
  <div class="flex items-center justify-between">
    <p class="text-sm text-blue-800">
      📋 Based on: <strong x-text="getOriginalResourceName(editingResource.source_id)"></strong>
    </p>
    <button @click="unlinkFromOriginal()" 
            class="text-xs text-blue-600 hover:underline">
      Unlink from original
    </button>
  </div>
</div>
```

*Unlinking Logic:*
```javascript
async unlinkFromOriginal() {
    if (!confirm('Remove the link to the original shared resource? This cannot be undone.')) {
        return;
    }
    
    await api.updateResource(this.editingResource.type, this.editingResource.id, {
        source_id: null
    });
    
    this.editingResource.source_id = null;
    this.setSuccess('Resource unlinked from original');
}
```

**Benefits:**
- ✅ Doesn't overwhelm basic users
- ✅ Power features available when needed
- ✅ Progressive disclosure pattern
- ✅ Backward compatible (defaults to simple behavior)

**Key deliverable**: Advanced users can enable intent-based copying and source provenance tracking; basic users see no change

---

### Summary of Phased Approach

| Phase | Name | Effort | Scope | Impact |
|-------|------|--------|-------|--------|
| 1 | Core Copy-on-Write | 2-3 days | Frontend only | ⭐⭐⭐⭐⭐ Solves main UX problem |
| 2 | Copy Detection + Filtering | 3-5 days | Frontend only | ⭐⭐⭐⭐ Prevents duplicates |
| 3 | Preferences + Intent | 5-7 days | Backend + Frontend | ⭐⭐⭐ Opt-in power features |

**Total**: 2-3 weeks for complete implementation

---

## Implementation Phases

### Phase 1: Core Copy-on-Write (Essential)

**Goal**: Enable seamless editing of shared resources in projects

**Implementation Decisions:**

| Question | Decision | Rationale |
|----------|----------|-----------|
| 1. Edit Button | **Keep pencil icon, change behavior** | Seamless UX - same button, smart behavior based on resource type |
| 2. Loading State | **Inline spinner on button** | Minimal disruption, clear feedback without modal |
| 3a. Info Banner When | **Show every time modal opens** | Consistent reminder of copy status |
| 3b. Info Banner Dismissible | **Tied to provenance preference** | Aligns with Phase 3 progressive enhancement |
| 3c. Info Banner Message | **Tied to provenance preference** | Consistency with overall preference system |
| 4. Shared Badge | **Change from "read-only" to "Shared"** | Clearer terminology, better UX |
| 5. Error Handling | **Toast notification** | Standard pattern, doesn't block workflow |
| 6. Copy Button Disposition | **Remove from project views** | Eliminates confusion, Edit does everything |
| 7. API Method Naming | **`copyAndReplaceInProject()`** | Self-documenting, clear intent |
| 8. State Update | **Pessimistic (wait for API)** | Data consistency, avoid rollback complexity |

**Tasks:**
1. ✅ Update Edit button click handler to detect shared resources and branch logic
2. ✅ Implement `handleEditSharedResource()` function with inline spinner
3. ✅ Add `copyAndReplaceInProject()` API client method
4. ✅ Change shared resource badge from "read-only" to "Shared"
5. ✅ Add info banner in edit modal (shown always, content depends on preferences)
6. ✅ Update project state pessimistically after API response
7. ✅ Remove standalone green "Copy" button from project views
8. ✅ Add toast error notifications for copy failures

**Files to Modify:**
- `frontend/src/views/project-detail.html` (UI changes: badge text, remove Copy button)
- `frontend/src/js/app.js` (business logic: smart Edit handler, state management)
- `frontend/src/js/utils/api.js` (API client: `copyAndReplaceInProject()` method)

**Success Criteria:**
- User clicks Edit button (pencil icon) on shared resource → inline spinner appears
- Copy is created automatically via `POST /api/projects/{pid}/plugins/{id}/copy`
- Project reference updates atomically (pessimistic update after API response)
- Edit modal opens with new copy and info banner
- Info banner shows "This is your copy of a shared resource" (basic message when preferences disabled)
- Badge shows "Shared" instead of "read-only" for shared resources
- Green Copy button no longer appears in project views
- Copy failures show toast notification with error message
- Changes save normally after modal opens

---

## Phase 1 Implementation Specification

### 1. Edit Button Behavior (Smart Click Handler)

**Current State:**
```html
<!-- project-detail.html -->
<button @click="openEditProjectPluginModal(plugin.name)" 
        x-show="!plugin.is_shared"
        class="...">
  <svg><!-- pencil icon --></svg>
</button>
```

**New Implementation:**
```html
<!-- project-detail.html - Remove x-show condition -->
<button @click="handleEditClick('plugins', plugin)" 
        class="...">
  <svg x-show="!isEditingResource"><!-- pencil icon --></svg>
  <svg x-show="isEditingResource" class="animate-spin"><!-- spinner icon --></svg>
</button>
```

**Logic in app.js:**
```javascript
// New method - routes to appropriate handler
async handleEditClick(resourceType, resource) {
    if (resource.is_shared) {
        await this.handleEditSharedResource(resourceType, resource.id);
    } else {
        this.openEditModal(resourceType, resource);
    }
}

// New method - copy-on-write flow
async handleEditSharedResource(resourceType, resourceId) {
    this.isEditingResource = true; // Show inline spinner
    
    try {
        // Call atomic copy-and-replace endpoint
        const result = await api.copyAndReplaceInProject(
            this.currentProject.id,
            resourceType,
            resourceId
        );
        
        // Pessimistic update: wait for API, then update local state
        await this.replaceResourceInCurrentProject(resourceType, result.old_id, result.new_id);
        
        // Load the new copy
        const newResource = await api.getResource(resourceType, result.new_id);
        
        // Open edit modal with new copy
        this.openEditModal(resourceType, newResource, { isCopiedFromShared: true });
        
    } catch (error) {
        this.showToast('error', `Failed to copy resource: ${error.message}`);
    } finally {
        this.isEditingResource = false; // Hide spinner
    }
}
```

### 2. Badge Text Change

**Current State:**
```html
<span x-show="plugin.is_shared" 
      class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">
  read-only
</span>
```

**New Implementation:**
```html
<span x-show="plugin.is_shared" 
      class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">
  Shared
</span>
```

### 3. Info Banner in Edit Modal

**Implementation:**
```html
<!-- In edit modal (e.g., modals/edit-plugin.html) -->
<div x-show="editContext.isCopiedFromShared" 
     class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
  <div class="flex items-start">
    <svg class="w-5 h-5 text-blue-600 mr-2 flex-shrink-0"><!-- info icon --></svg>
    <p class="text-sm text-blue-800">
      This is your copy of a shared resource. Changes will only affect your projects.
    </p>
  </div>
</div>
```

**Context Passing:**
```javascript
// When opening modal
openEditModal(resourceType, resource, context = {}) {
    this.editingResource = resource;
    this.editContext = context; // { isCopiedFromShared: true }
    this.showModal('edit-' + resourceType);
}
```

**Phase 3 Enhancement (Preferences-aware):**
```javascript
// Future: When showSourceProvenance preference is enabled
getBannerMessage() {
    if (!this.preferences.showSourceProvenance) {
        return "This is your copy of a shared resource.";
    }
    
    // Enhanced message when preferences enabled
    const originalName = this.getOriginalResourceName(this.editingResource.source_id);
    return `Based on: <strong>${originalName}</strong>`;
}
```

### 4. Remove Copy Button from Project Views

**Current State:**
```html
<!-- Green Copy button for shared resources -->
<button @click="copySharedResource('plugins', plugin.id)" 
        x-show="plugin.is_shared"
        class="text-green-600 hover:text-green-800">
  📋 Copy
</button>
```

**New Implementation:**
```html
<!-- Remove entirely from project-detail.html -->
<!-- Copy functionality now handled by smart Edit button -->
```

**Note:** Copy button remains in Settings page for creating library copies independent of projects.

### 5. API Client Method

**New Method in `frontend/src/js/utils/api.js`:**
```javascript
/**
 * Copy a shared resource and replace it in a project atomically.
 * 
 * @param {string} projectId - Project ID
 * @param {string} resourceType - 'plugins' | 'provisioners' | 'triggers'
 * @param {string} resourceId - ID of shared resource to copy
 * @returns {Promise<{old_id: string, new_id: string, project_updated: boolean}>}
 */
async copyAndReplaceInProject(projectId, resourceType, resourceId) {
    const endpoint = `/api/projects/${projectId}/${resourceType}/${resourceId}/copy`;
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: this.getHeaders(),
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Copy operation failed');
    }
    
    return await response.json();
}

/**
 * Get a single resource by ID.
 */
async getResource(resourceType, resourceId) {
    const endpoint = `/api/${resourceType}/${resourceId}`;
    const response = await fetch(endpoint, {
        headers: this.getHeaders(),
    });
    
    if (!response.ok) {
        throw new Error(`Failed to load ${resourceType}`);
    }
    
    return await response.json();
}
```

### 6. Project State Update (Pessimistic)

**Implementation:**
```javascript
/**
 * Update local project state after successful copy-and-replace.
 * Uses pessimistic update pattern (waits for API confirmation).
 */
async replaceResourceInCurrentProject(resourceType, oldId, newId) {
    // Update project array
    const arrayName = `global_${resourceType}`;
    const index = this.currentProject[arrayName].indexOf(oldId);
    
    if (index !== -1) {
        this.currentProject[arrayName][index] = newId;
    }
    
    // Update cache if exists
    if (this.resourceCache && this.resourceCache[resourceType]) {
        delete this.resourceCache[resourceType][oldId];
        // New resource will be loaded separately
    }
    
    // No optimistic update - state only changes after API confirms
}
```

### 7. Error Handling (Toast Notifications)

**Toast Component (if not exists):**
```javascript
// In app.js
showToast(type, message) {
    this.toast = {
        show: true,
        type: type, // 'success' | 'error' | 'info'
        message: message
    };
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        this.toast.show = false;
    }, 5000);
}
```

**Toast UI:**
```html
<!-- In main layout -->
<div x-show="toast.show" 
     x-transition
     :class="{
         'bg-red-100 border-red-400 text-red-700': toast.type === 'error',
         'bg-green-100 border-green-400 text-green-700': toast.type === 'success',
         'bg-blue-100 border-blue-400 text-blue-700': toast.type === 'info'
     }"
     class="fixed top-4 right-4 px-4 py-3 rounded border z-50">
  <span x-text="toast.message"></span>
  <button @click="toast.show = false" class="ml-4">×</button>
</div>
```

### 8. Complete Flow Example

**User Action:** Clicks Edit (pencil icon) on shared "vagrant-vbguest" plugin

**Frontend Steps:**
1. `handleEditClick('plugins', plugin)` called
2. Detects `plugin.is_shared === true`
3. Calls `handleEditSharedResource('plugins', 'shared-plugin-123')`
4. Sets `isEditingResource = true` → inline spinner appears
5. Calls `api.copyAndReplaceInProject(projectId, 'plugins', 'shared-plugin-123')`

**Backend Processing:**
1. Receives `POST /api/projects/{pid}/plugins/shared-plugin-123/copy`
2. Creates copy: `user-plugin-456` with `source_id: 'shared-plugin-123'`
3. Updates project: replaces `shared-plugin-123` → `user-plugin-456`
4. Returns `{old_id: 'shared-plugin-123', new_id: 'user-plugin-456', project_updated: true}`

**Frontend Completion:**
1. Receives response, calls `replaceResourceInCurrentProject('plugins', 'shared-plugin-123', 'user-plugin-456')`
2. Updates local project state (pessimistic)
3. Calls `api.getResource('plugins', 'user-plugin-456')` to load full copy
4. Calls `openEditModal('plugins', newResource, {isCopiedFromShared: true})`
5. Modal opens with:
   - Info banner: "This is your copy of a shared resource"
   - Name field: "vagrant-vbguest (Copy)"
   - All fields editable
6. Sets `isEditingResource = false` → spinner disappears

**Error Scenario:**
1. API call fails (network error, permission denied, etc.)
2. `catch` block executes
3. Shows toast: "Failed to copy resource: [error details]"
4. `finally` block sets `isEditingResource = false`
5. User can retry or cancel

---

### Phase 2: Existing Copy Detection (Important)

**Goal**: Prevent duplicate copies when user already has one

**Tasks:**
1. ✅ Implement smart filtering (`getRelevantCopies()`)
2. ✅ Create copy choice modal component
3. ✅ Add logic to show modal when copies exist
4. ✅ Implement "use existing" vs "create new" flows
5. ✅ Add single-copy confirmation variant

**Files to Modify:**
- `frontend/src/modals/copy-choice.html` (new file)
- `frontend/src/js/app.js` (detection logic)

**Success Criteria:**
- If no copies exist: seamless create
- If 1 copy exists: show confirmation
- If multiple copies: show choice modal
- User can reuse existing or create new

### Phase 3: Intent-Based Copying (Nice-to-Have)

**Goal**: Solve copy-as-template problem at the source with opt-in advanced features

**Tasks:**
1. ✅ Create user preferences model and storage
2. ✅ Add advanced settings section in Settings page
3. ✅ Add `copy_intent` parameter to backend copy methods
4. ✅ Update copy endpoints to accept intent
5. ✅ Implement adaptive UI (simple vs advanced mode)
6. ✅ Add copy intent dropdown/menu (when enabled)
7. ✅ Add source provenance display (when enabled)
8. ✅ Add unlink functionality (when provenance shown)
9. ✅ Update frontend to read/respect preferences

**Files to Modify:**
- `backend/src/models/user_preferences.py` (new model)
- `backend/src/services/preference_service.py` (already exists, extend)
- `backend/src/api/preferences.py` (new/extend existing)
- `backend/src/services/plugin_service.py` (add intent parameter)
- `backend/src/api/plugins.py` (accept intent in copy endpoint)
- `frontend/src/views/settings.html` (add advanced section)
- `frontend/src/js/app.js` (load/save preferences, adaptive UI logic)

**User Preferences Model:**
```python
class CopyPreferences(BaseModel):
    """User preferences for copy behavior."""
    enable_intent_based_copying: bool = Field(
        default=False,
        description="Show 'Copy to Customize' vs 'Use as Template' options"
    )
    show_source_provenance: bool = Field(
        default=False,
        description="Display original source and allow unlinking"
    )
    always_show_copy_choices: bool = Field(
        default=False,
        description="Always ask before creating new copies"
    )
    auto_filter_divergent_copies: bool = Field(
        default=True,
        description="Hide copies that have diverged significantly from original"
    )
```

**Settings UI:**
```html
<!-- Settings → Advanced -->
<div class="settings-section">
  <h3>Copy Behavior</h3>
  <p class="text-sm text-gray-600 mb-4">
    Advanced options for controlling how resources are copied and tracked.
  </p>
  
  <div class="space-y-3">
    <label class="flex items-start space-x-3">
      <input type="checkbox" 
             x-model="preferences.enableIntentBasedCopying"
             @change="savePreferences()">
      <div>
        <div class="font-medium">Enable intent-based copying</div>
        <div class="text-sm text-gray-600">
          Show "Copy to Customize" vs "Use as Template" options. 
          Templates won't be suggested when editing the original.
        </div>
      </div>
    </label>
    
    <label class="flex items-start space-x-3">
      <input type="checkbox" 
             x-model="preferences.showSourceProvenance"
             @change="savePreferences()">
      <div>
        <div class="font-medium">Show resource provenance</div>
        <div class="text-sm text-gray-600">
          Display "Based on: [Original]" in edit modals with option to unlink.
        </div>
      </div>
    </label>
    
    <label class="flex items-start space-x-3">
      <input type="checkbox" 
             x-model="preferences.alwaysShowCopyChoices"
             @change="savePreferences()">
      <div>
        <div class="font-medium">Always show copy choices</div>
        <div class="text-sm text-gray-600">
          Ask before creating new copies even if you don't have existing ones.
        </div>
      </div>
    </label>
  </div>
</div>
```

**Success Criteria:**
- Settings page shows advanced copy preferences
- Preferences persist per user
- Default behavior is simple (single "Copy" button)
- Advanced mode shows intent options (customize/template)
- Source provenance only shows when enabled
- Unlink option only appears when provenance enabled
- All features gracefully degrade if preferences not loaded

---

## Technical Specifications

### API Endpoints Summary

**Already Implemented:**

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| POST | `/api/plugins/{id}/copy` | Copy shared plugin to user library | Plugin object |
| POST | `/api/projects/{pid}/plugins/{id}/copy` | Copy + replace in project (atomic) | `{old_id, new_id, project_updated}` |
| POST | `/api/projects/{pid}/plugins/{old}/replace/{new}` | Replace plugin reference | `{old_id, new_id, project_updated}` |
| GET | `/api/plugins/copies-of/{source_id}` | Find user's copies of shared resource | Array of Plugin objects |

*(Same endpoints exist for provisioners, triggers, boxes)*

**Needs Update (Phase 3):**

```python
# Add copy_intent parameter
POST /api/plugins/{id}/copy?copy_intent=customize
POST /api/plugins/{id}/copy?copy_intent=template
```

### Data Model

**Resource Fields:**
```typescript
interface Resource {
  id: string;
  name: string;
  // ... resource-specific fields
  
  // Multi-user fields
  is_shared: boolean;      // true = shared, false = user-owned
  owner_id: string | null; // null for shared, user-id for owned
  source_id: string | null; // ID of original shared resource (provenance)
  
  created_at: string;
  updated_at: string;
}
```

**source_id Behavior:**
- Set when: User copies shared resource with "customize" intent
- Not set when: 
  - Creating new resource from scratch
  - Copying with "template" intent
  - Resource is manually unlinked
- Used for: Finding existing copies, showing provenance

### Frontend State Management

**Project State:**
```javascript
{
  currentProject: {
    id: "project-123",
    global_plugins: ["user-plugin-456"],  // ← Updated after copy
    global_provisioners: [...],
    global_triggers: [...]
  },
  
  // Cache of full resource objects
  projectPluginsCache: {
    "user-plugin-456": { /* full plugin object */ }
  }
}
```

**After copy-and-replace:**
```javascript
// Update project array
this.currentProject.global_plugins[index] = newId;

// Add to cache
this.projectPluginsCache[newId] = newResource;

// Remove old from cache (optional)
delete this.projectPluginsCache[oldId];
```

---

## Deployment Mode Compatibility

### Self-Hosted Mode (`DEPLOYMENT_MODE=self-hosted`)

**Characteristics:**
- ✅ No authentication (`user_id = None`)
- ✅ All resources in `/data/shared/` directory
- ✅ All resources have `is_shared: false, owner_id: null`
- ✅ Edit works normally (no copy logic)

**Implementation Impact:**
```javascript
// In handleEditSharedResource()
async handleEditSharedResource(type, resourceId) {
    const plugin = this.getResource(resourceId);
    
    if (!plugin.is_shared) {
        // Self-hosted mode: just edit directly
        this.openEditModal(type, plugin);
        return;
    }
    
    // Public mode: copy-on-write logic
    // ...
}
```

**Key Point**: Copy-on-write logic only activates when `is_shared: true`, which never happens in self-hosted mode.

### Public Mode (`DEPLOYMENT_MODE=public`)

**Characteristics:**
- ✅ JWT authentication required
- ✅ `user_id` set from token
- ✅ Shared resources in `/data/shared/`
- ✅ User resources in `/data/users/{user_id}/`
- ✅ Copy endpoints require `user_id`

**Backend Validation:**
```python
def copy_shared_plugin(self, plugin_id: str) -> Plugin:
    if not self.user_id:
        raise PluginServiceError("Cannot copy plugins in self-hosted mode")
    # ... rest of copy logic
```

### Compatibility Matrix

| Feature | Self-Hosted | Public Mode |
|---------|-------------|-------------|
| Edit shared resources | ✅ Direct edit | ✅ Copy-on-write |
| Copy button | ❌ Hidden/disabled | ✅ Visible for shared |
| `source_id` tracking | N/A | ✅ Enabled |
| Existing copy detection | N/A | ✅ Enabled |
| Intent-based copying | N/A | ✅ Enabled |

---

## Open Questions & Future Considerations

### ✅ Resolved Questions

1. **Copy Button Visibility**: ✅ Keep standalone "Copy" button but make it adaptive
   - **Default mode**: Single "Copy" button (simple)
   - **Advanced mode** (opt-in): Dropdown with "Customize" vs "Template" options

2. **Intent-Based Copying**: ✅ Implement as opt-in preference
   - Default: All copies set `source_id` (simple, consistent)
   - When enabled: Users choose intent, controls `source_id` behavior
   - Benefits: Doesn't overwhelm basic users, power features available

3. **Source Provenance Display**: ✅ Preference-gated
   - Default: Hidden (simpler UI)
   - When enabled: Shows "Based on: [Original]" with unlink option
   - Only power users who need it will enable it

### Questions to Resolve

1. **Shared Resource Indicators**: How should we visually distinguish shared vs user-owned resources?
   - **Option A**: Badge (🔒 "Shared" / 👤 "Yours")
   - **Option B**: Different card styling (border color, background tint)
   - **Option C**: Icon only (minimal visual noise)
   - **Recommendation**: Option A for clarity, especially for new users

2. **Modal Info Banner**: Should the "This is your copy" banner persist after first save?
   - **Option A**: Show every time modal opens
   - **Option B**: Show only first time, then hide (dismissible)
   - **Option C**: Tie to provenance preference (shown when enabled)
   - **Recommendation**: Option C (consistent with preference model)

3. **Copy Naming**: Should users be prompted to rename the copy before editing?
   - **Option A**: Auto-name with "(Copy)" suffix, let user rename in modal ⭐ (recommended)
   - **Option B**: Show rename dialog before opening edit modal
   - **Option C**: Smart naming based on context
   - **Recommendation**: Option A (seamless flow, rename happens naturally)

4. **Preference Defaults**: What should the default preference values be?
   - **Current recommendation**:
     ```javascript
     {
       enableIntentBasedCopying: false,      // Simple by default
       showSourceProvenance: false,          // Hide complexity
       alwaysShowCopyChoices: false,         // Seamless first copy
       autoFilterDivergentCopies: true       // Smart filtering on
     }
     ```

5. **Preference Scope**: Should preferences be global or per-resource-type?
   - **Option A**: Global (one setting for all resource types) ⭐ (recommended)
   - **Option B**: Per-type (different settings for plugins vs provisioners)
   - **Recommendation**: Option A (simpler, less overwhelming)

### Future Enhancements

**Settings Page - Advanced Copy Preferences (Visual):**
```
┌────────────────────────────────────────────────────────────┐
│ Settings                                                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ COPY BEHAVIOR                                              │
│ Advanced options for controlling resource copying         │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ ☐ Enable intent-based copying                     │    │
│ │   Show "Copy to Customize" vs "Use as Template"   │    │
│ │   options. Templates won't be suggested when      │    │
│ │   editing the original resource.                  │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ ☐ Show resource provenance                        │    │
│ │   Display "Based on: [Original]" in edit modals   │    │
│ │   with option to unlink from the source.          │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ ☐ Always show copy choices                        │    │
│ │   Ask before creating new copies even if you      │    │
│ │   don't have existing ones.                       │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│ ┌────────────────────────────────────────────────────┐    │
│ │ ☑ Auto-filter divergent copies                    │    │ ← On by default
│ │   Hide copies that have diverged significantly    │    │
│ │   from the original (e.g., different names).      │    │
│ └────────────────────────────────────────────────────┘    │
│                                                            │
│                           [Save Preferences]               │
└────────────────────────────────────────────────────────────┘
```

**Copy History/Provenance Tracking:**
- Show "Based on: [Original Name]" in resource details (when preference enabled)
- Link to original shared resource for reference
- Show when original was last updated (for sync considerations)
- Visual divergence indicator (percentage changed from original)

**Bulk Operations:**
- "Copy all shared resources to my library" option
- "Replace all shared with my copies" in project settings

**Sync Capabilities:**
- "Check for updates" on copies with `source_id`
- Optional: "Sync changes from original" (merge operation)
- Track divergence percentage

**Analytics:**
- Track which shared resources are most copied
- Identify unused shared resources
- Popular customizations/variations

---

## Summary

**Implementation Priority:**

1. **Phase 1 (Essential)**: Core copy-on-write for seamless editing
   - **Effort**: ~2-3 days
   - **Impact**: ⭐⭐⭐⭐⭐ (solves main UX problem)
   
2. **Phase 2 (Important)**: Existing copy detection with smart filtering
   - **Effort**: ~3-5 days
   - **Impact**: ⭐⭐⭐⭐ (prevents duplicates)
   
3. **Phase 3 (Nice-to-Have)**: Intent-based copying + preferences
   - **Effort**: ~5-7 days
   - **Impact**: ⭐⭐⭐ (solves edge case, opt-in power features)

**Total Estimated Effort**: 2-3 weeks for all phases

**Progressive Enhancement Benefits:**
- ✅ **Simple by default**: Basic users see one "Copy" button, seamless workflow
- ✅ **Power when needed**: Advanced users can enable granular control
- ✅ **Self-documenting**: Settings page explains each feature's purpose
- ✅ **No forced workflow**: Users choose their complexity level
- ✅ **Gradual learning curve**: Users discover features as needed

**Key Success Metrics:**
- ✅ Users can edit shared resources in projects without manual workflows
- ✅ No duplicate copies created unnecessarily (with smart filtering)
- ✅ Advanced features available but not required
- ✅ Clear distinction between customization vs template usage (when enabled)
- ✅ Works seamlessly in both self-hosted and public modes

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-15  
**Next Review**: After Phase 1 implementation
