# Multiuser Support Discussion

**Date**: November 13, 2025  
**Status**: Planning Phase  
**Purpose**: Design document for adding basic user management and multiuser support

---

## 📋 Executive Summary

**Authentication**: **Hybrid Strategy** - OIDC (Google/GitHub/GitLab) + Email OTP (Mailgun EU)  
**Data Model**: Shared resources (read-only) + User resources (read-write)  
**Storage**: JSON files in `/shared/` and `/users/{user-id}/` directories  
**Sessions**: JWT tokens (24-hour expiration, stateless)  
**Total Effort**: ~42 hours (11h OIDC + 8h OTP + 8h backend + 8h frontend + 4h testing + 3h docs)

**Key Decisions**:
- ✅ **OIDC Providers**: Google, GitHub, GitLab (all free, developer-focused)
- ✅ **OTP Email**: Mailgun EU Region (GDPR-compliant, reliable)
- ✅ **Hybrid Approach**: Users choose OIDC (preferred) or email OTP (privacy/accessibility)
- ✅ **User Resources**: Users can add custom boxes, plugins, provisioners, triggers
- ✅ **Settings Page**: Single list with visual indicators (🔒 system vs 👤 user) - See Section 2.1.1
- ✅ Hybrid shared/user resources provide excellent UX for new users + flexibility for power users
- ⚠️ Skip Apple Sign In ($99/year, complex setup)
- 🎯 Maximum flexibility: Social login for convenience, email for privacy

---

## 1. Core Requirements (User-Specified)

### 1.1 Simplicity
- Store minimal user information
- Keep data model lightweight
- Avoid complexity where possible

### 1.2 Authentication Strategy
- **Hybrid Approach** - Users choose their preferred method
- **OIDC Providers**: Google, GitHub, GitLab - One-click social login
- **Email OTP**: 6-digit code via Mailgun (EU Region) - Privacy-focused alternative
- **No passwords** - Fully passwordless authentication flow
- **Detailed analysis** - See Section 2.13 (OIDC) and Section 2.3 (Email/Mailgun)

### 1.3 Data Storage
- **JSON files on backend** - sufficient for initial implementation
- **S3 support** - discussed separately for future scalability

---

## 2. Additional Topics to Explore

### 2.1 Data Isolation & Ownership

**Critical Question**: How should projects and resources be scoped to users?

#### Current State Analysis
- Projects stored in: `backend/data/projects/{project-id}.json`
- Global resources (plugins, provisioners, triggers, boxes) shared across all projects
- No user context in current data models

#### Proposed Changes

**Hybrid Data Directory Structure (User-defined + Shared Resources)**

```
backend/data/
  shared/                          # Read-only for users, system-wide defaults
    boxes/
      boxes.json                   # Official Vagrant boxes catalog
    plugins/
      {plugin-id}.json             # Common plugins (vagrant-vbguest, etc.)
    provisioners/
      {provisioner-id}.json        # Example provisioner templates
    triggers/
      {trigger-id}.json            # Example trigger configurations
    
  users/
    {user-id}/
      projects/
        {project-id}.json          # User's Vagrant projects
      boxes/
        {box-id}.json              # User-added custom boxes
      plugins/
        {plugin-id}.json           # User-created custom plugins
      provisioners/
        {provisioner-id}.json      # User-created provisioners
      triggers/
        {trigger-id}.json          # User-created triggers
```

**Resource Resolution Logic**:
1. Check user's directory first (`users/{user-id}/{resource-type}/{id}.json`)
2. If not found, fallback to shared directory (`shared/{resource-type}/{id}.json`)
3. User can "override" shared resources by creating same ID in their directory
4. Users cannot modify shared resources (enforced at API level)
5. **Applies to all resources**: projects, boxes, plugins, provisioners, triggers

**Benefits**:
- ✅ **Separation of concerns**: System defaults vs user customizations
- ✅ **Reduced duplication**: Common resources shared across all users
- ✅ **Easy onboarding**: New users start with curated shared resources
- ✅ **Flexibility**: Users can create custom resources without affecting others
- ✅ **Migration friendly**: Current data moves to `/shared` initially
- ✅ **Storage efficient**: Shared resources stored once, not per user

**Implementation Notes**:
- API endpoints return merged view (user resources + shared resources)
- DELETE/PUT operations check ownership (can't modify shared)
- POST operations always create in user directory
- Shared resource IDs should use reserved namespace (e.g., prefix with `shared-` or UUIDs in specific range)

**Practical Example - User Perspective**:

Alice (new user) logs in and sees:
- **Projects**: Empty (none created yet)
- **Boxes**: 50+ items (all from `/shared/boxes/`) - ubuntu/focal64, centos/7, etc.
- **Plugins**: 10 items (all from `/shared/plugins/`) - vagrant-vbguest, vagrant-disksize, etc.
- **Provisioners**: 5 items (all from `/shared/provisioners/`) - shell, ansible, puppet examples
- **Triggers**: 3 items (all from `/shared/triggers/`) - common trigger templates

Alice creates custom resources:
- Creates "my-custom-plugin" → saved to `/users/alice-id/plugins/{uuid}.json`
- Adds custom box "my-company/internal-base" → saved to `/users/alice-id/boxes/{uuid}.json`
- Now sees 11 plugins (10 shared + 1 custom) and 51 boxes (50 shared + 1 custom)
- Can edit/delete her custom resources
- **Cannot** edit/delete shared resources (UI shows read-only badge)
- **Cannot** edit/delete shared plugins (UI shows read-only badge)

Bob (another user) logs in:
- Sees same 10 shared plugins
- **Cannot** see Alice's custom plugin
- Creates his own "bob-special-provisioner" → saved to `/users/bob-id/provisioners/{uuid}.json`

Admin updates shared resources:
- Adds new "vagrant-timezone" plugin to `/shared/plugins/`
- All users (Alice, Bob, etc.) immediately see it in their plugin list
- No data migration needed

**Service Layer Implementation**:

```python
# backend/src/services/plugin_service.py
class PluginService:
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.shared_dir = Path("data/shared/plugins")
        self.user_dir = Path(f"data/users/{user_id}/plugins") if user_id else None
    
    def list_all(self) -> List[Plugin]:
        """Return merged list: shared + user plugins"""
        plugins = {}
        
        # Load shared plugins first
        for file in self.shared_dir.glob("*.json"):
            plugin = self._load_plugin(file)
            plugin.scope = "shared"
            plugin.read_only = True
            plugins[plugin.id] = plugin
        
        # Load user plugins (override shared if same ID)
        if self.user_dir and self.user_dir.exists():
            for file in self.user_dir.glob("*.json"):
                plugin = self._load_plugin(file)
                plugin.scope = "user"
                plugin.read_only = False
                plugins[plugin.id] = plugin
        
        return list(plugins.values())
    
    def get_by_id(self, plugin_id: str) -> Plugin:
        """Check user dir first, then shared"""
        # Try user's directory first
        if self.user_dir:
            user_file = self.user_dir / f"{plugin_id}.json"
            if user_file.exists():
                return self._load_plugin(user_file, scope="user")
        
        # Fallback to shared
        shared_file = self.shared_dir / f"{plugin_id}.json"
        if shared_file.exists():
            return self._load_plugin(shared_file, scope="shared")
        
        raise PluginNotFoundError(plugin_id)
    
    def create(self, plugin: PluginCreate) -> Plugin:
        """Always create in user directory"""
        if not self.user_id:
            raise ValueError("User context required for creation")
        
        self.user_dir.mkdir(parents=True, exist_ok=True)
        plugin_id = uuid4()
        file_path = self.user_dir / f"{plugin_id}.json"
        
        # Save to user directory
        with open(file_path, 'w') as f:
            json.dump(plugin.model_dump(), f)
        
        return self.get_by_id(str(plugin_id))
    
    def delete(self, plugin_id: str):
        """Only allow deleting user's own plugins"""
        if not self.user_dir:
            raise ValueError("User context required for deletion")
        
        user_file = self.user_dir / f"{plugin_id}.json"
        
        if user_file.exists():
            user_file.unlink()  # Delete user's plugin
        else:
            # Check if it's a shared resource (can't delete)
            shared_file = self.shared_dir / f"{plugin_id}.json"
            if shared_file.exists():
                raise PermissionError("Cannot delete shared resource")
            else:
                raise PluginNotFoundError(plugin_id)
```

---

### 2.1.1 Settings Page UI/UX for Multiuser Support

**Current State (Single User)**:
- Settings page manages **global resources** (plugins, provisioners, boxes, triggers)
- All resources are system-wide and shared across all projects
- Simple CRUD interface: Add, Edit, Delete buttons visible for all items
- No concept of ownership or permissions

**Challenge with Multiuser**:
How to present both **shared (system)** and **user-created** resources in a unified, intuitive interface?

---

#### Option 1: Single List with Visual Indicators (Recommended)

**Approach**: Show all resources (shared + user) in one list with clear visual distinction

**UI Design**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings > Boxes                                      [+ Add Box] │
├─────────────────────────────────────────────────────────────────┤
│  Filter: [All ▾] [System ▾] [My Boxes ▾]         Search: [____] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🔒 ubuntu/focal64                            [View Details]     │
│     System Box • Official Ubuntu 20.04 LTS                       │
│                                                                   │
│  🔒 centos/7                                  [View Details]     │
│     System Box • CentOS 7 base image                             │
│                                                                   │
│  👤 my-company/internal-base                 [Edit] [Delete]     │
│     My Box • Custom internal base for projects                   │
│     Created: Nov 13, 2025                                        │
│                                                                   │
│  🔒 debian/bullseye64                        [View Details]     │
│     System Box • Debian 11 Bullseye                              │
│                                                                   │
│  👤 alice/dev-environment                    [Edit] [Delete]     │
│     My Box • Development environment with tools                  │
│     Created: Nov 10, 2025                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Visual Indicators**:
- 🔒 **Lock icon** = Shared/System resource (read-only)
- 👤 **User icon** = User's custom resource (editable)
- **Badge**: "System Box" vs "My Box" label
- **Actions**: System items show only "View Details", user items show "Edit" + "Delete"
- **Styling**: System items could have subtle background color (e.g., light gray)

**Filter Options**:
- **All**: Show everything (default)
- **System**: Show only shared resources
- **My [Resource Type]**: Show only user's custom resources

**Benefits**:
- ✅ Familiar UX (same layout as current app)
- ✅ Clear visual hierarchy
- ✅ No confusion about permissions (actions disabled for system resources)
- ✅ Easy to find both system and custom resources
- ✅ Minimal code changes to frontend

**Implementation**:
```javascript
// Alpine.js component
<div x-data="settingsBoxes()">
  <!-- Filter -->
  <select x-model="filter">
    <option value="all">All Boxes</option>
    <option value="system">System Boxes</option>
    <option value="user">My Boxes</option>
  </select>
  
  <!-- Box list -->
  <template x-for="box in filteredBoxes" :key="box.id">
    <div class="box-item" 
         :class="{ 'system-box': box.scope === 'shared' }">
      
      <!-- Icon -->
      <span x-show="box.scope === 'shared'">🔒</span>
      <span x-show="box.scope === 'user'">👤</span>
      
      <!-- Name & Description -->
      <div>
        <h3 x-text="box.name"></h3>
        <p>
          <span x-text="box.scope === 'shared' ? 'System Box' : 'My Box'"></span>
          • 
          <span x-text="box.description"></span>
        </p>
      </div>
      
      <!-- Actions -->
      <template x-if="box.scope === 'shared'">
        <button @click="viewDetails(box)">View Details</button>
      </template>
      
      <template x-if="box.scope === 'user'">
        <button @click="editBox(box)">Edit</button>
        <button @click="deleteBox(box)">Delete</button>
      </template>
    </div>
  </template>
</div>
```

---

#### Option 2: Tabbed Interface

**Approach**: Separate tabs for "System Resources" and "My Resources"

**UI Design**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings > Boxes                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [System Boxes] [My Boxes (2)]                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                    [+ Add Box]    │
│  my-company/internal-base                        [Edit] [Delete] │
│    Custom internal base for projects                             │
│    Created: Nov 13, 2025                                         │
│                                                                   │
│  alice/dev-environment                           [Edit] [Delete] │
│    Development environment with tools                            │
│    Created: Nov 10, 2025                                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Clear separation of concerns
- ✅ User's resources get full attention (not mixed with 50+ system boxes)
- ✅ Cleaner UI when user has many custom resources

**Drawbacks**:
- ❌ Can't see system and user resources together
- ❌ More clicks to switch between tabs
- ❌ User might forget to check system resources

---

#### Option 3: Collapsible Sections

**Approach**: Collapsible accordion-style sections

**UI Design**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings > Boxes                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ▼ My Boxes (2)                                  [+ Add Box]     │
│  ├─ my-company/internal-base                     [Edit] [Delete] │
│  │    Custom internal base for projects                          │
│  └─ alice/dev-environment                        [Edit] [Delete] │
│       Development environment with tools                          │
│                                                                   │
│  ▼ System Boxes (50+)                                            │
│  ├─ ubuntu/focal64                               [View Details]  │
│  │    Official Ubuntu 20.04 LTS                                  │
│  ├─ centos/7                                     [View Details]  │
│  │    CentOS 7 base image                                        │
│  └─ ... (show first 10, "Load More" button)                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ User's resources shown first and highlighted
- ✅ Can collapse system resources to reduce clutter
- ✅ Both sections visible at once (if expanded)

**Drawbacks**:
- ❌ More complex to implement
- ❌ Search/filter across sections might be confusing

---

#### Recommendation: **Option 1 (Single List with Indicators)**

**Rationale**:
1. **Simplest migration**: Existing frontend code needs minimal changes
2. **Familiar UX**: Same layout, just add visual indicators
3. **Best discoverability**: Users see all available resources
4. **Clear permissions**: Visual cues (lock icon, disabled buttons) prevent confusion
5. **Flexible filtering**: Users can focus on what they need

**Implementation Checklist**:
- [ ] Add `scope` field to resource API responses (`"shared"` or `"user"`)
- [ ] Add `read_only` boolean field to API responses
- [ ] Update frontend to render lock/user icons based on scope
- [ ] Update frontend to conditionally show Edit/Delete buttons
- [ ] Add filter dropdown (All / System / My Resources)
- [ ] Add visual styling (background color, badges) for system resources
- [ ] Update "Add" button to create in user directory
- [ ] Add confirmation dialog for delete (with scope information)

---

#### Settings Page Responsive Behavior

**Desktop (Current)**:
- Full table/grid view with all columns
- Filters in top bar
- Actions buttons on right side

**Mobile (Current + Enhancements)**:
- Card-based layout
- Icons more prominent (🔒 or 👤)
- "System" or "My" badge clearly visible
- Swipe actions for Edit/Delete (user resources only)

---

#### Settings Page - New User Experience

**First Login (No Custom Resources Yet)**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings > Plugins                              [+ Add Plugin]  │
├─────────────────────────────────────────────────────────────────┤
│  Filter: [All ▾]                              Search: [____]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  💡 You don't have any custom plugins yet.                       │
│     System plugins are available below. Click "+ Add Plugin"     │
│     to create your own custom plugin configuration.              │
│                                                                   │
│  🔒 vagrant-vbguest                           [View Details]     │
│     System Plugin • VirtualBox Guest Additions                   │
│                                                                   │
│  🔒 vagrant-disksize                          [View Details]     │
│     System Plugin • Disk size management                         │
│                                                                   │
│  ... (more system plugins)                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**After Creating Custom Resources**:

- Custom resources appear at top (sorted by created date, newest first)
- System resources below (sorted alphabetically)
- Clear count in filter: "My Plugins (3)" vs "System Plugins (10)"

---

#### Advanced Feature: Resource Favoriting (Optional)

**Idea**: Allow users to "favorite" system resources they use frequently

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings > Boxes                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Filter: [All ▾] [Favorites ▾]                                   │
├─────────────────────────────────────────────────────────────────┤
│  ⭐ ubuntu/focal64                            [View] [Unfavorite] │
│     System Box • Official Ubuntu 20.04 LTS                       │
│                                                                   │
│  👤 my-company/internal-base                 [Edit] [Delete]     │
│     My Box • Custom internal base                                │
│                                                                   │
│  🔒 centos/7                                  [View] [★ Favorite] │
│     System Box • CentOS 7 base image                             │
└─────────────────────────────────────────────────────────────────┘
```

**Storage**: User favorites stored in `users/{user-id}/preferences.json`

**Benefits**:
- Quick access to frequently used system resources
- Personalizes experience without duplicating data
- Useful when system catalog has 100+ boxes

---

### 2.13 OIDC (OpenID Connect) Deep Dive

**What is OIDC?**
- Industry-standard authentication protocol built on OAuth 2.0
- Allows users to authenticate using existing accounts (Google, GitHub, Apple, etc.)
- Provides identity verification without handling passwords
- Returns JWT tokens with user information

---

#### 2.13.1 Complexity Assessment

**Initial Perception**: Complex  
**Reality**: Moderate complexity, but well-supported by libraries

**Complexity Breakdown**:

| Aspect | Complexity Level | Details |
|--------|-----------------|---------|
| Library Integration | ⭐ Low | Python libraries like `authlib` handle heavy lifting |
| Provider Setup | ⭐⭐ Medium | Need to register app with each provider (one-time) |
| Token Validation | ⭐ Low | Libraries handle JWT verification automatically |
| User Provisioning | ⭐⭐ Medium | Map provider user to local user (custom logic) |
| Multi-Provider Support | ⭐⭐⭐ Medium-High | Each provider has slight differences |
| Testing | ⭐⭐ Medium | Need to mock OIDC flows or use test providers |
| Frontend Integration | ⭐⭐ Medium | OAuth redirect flow with state management |

**Overall Assessment**: ⭐⭐ Medium Complexity
- **Easier than**: Building custom password system with all security considerations
- **Harder than**: Simple OTP-only approach
- **Best suited for**: Production applications wanting professional auth

---

#### 2.13.2 Provider-Specific Implementation

**Google OIDC**
- **Difficulty**: ⭐ Easy (excellent documentation)
- **Setup Steps**:
  1. Create project in Google Cloud Console
  2. Enable Google+ API
  3. Create OAuth 2.0 credentials
  4. Configure authorized redirect URIs
  5. Get Client ID + Client Secret
- **User Info**: Email, name, profile picture, email verified status
- **Free Tier**: Unlimited (no cost for authentication)
- **Docs**: https://developers.google.com/identity/protocols/oauth2/openid-connect

**GitHub OAuth**
- **Difficulty**: ⭐ Easy (straightforward process)
- **Setup Steps**:
  1. Go to Settings → Developer Settings → OAuth Apps
  2. Register new application
  3. Set authorization callback URL
  4. Get Client ID + Client Secret
- **User Info**: Email, username, name, avatar
- **Note**: Not pure OIDC, but OAuth 2.0 (similar flow)
- **Free Tier**: Unlimited
- **Docs**: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps

**GitLab OAuth** ⭐ **INCLUDED**
- **Difficulty**: ⭐ Easy (similar to GitHub)
- **Setup Steps**:
  1. Go to User Settings → Applications
  2. Create new application
  3. Set redirect URI
  4. Select scopes: `read_user`, `email`
  5. Get Application ID + Secret
- **User Info**: Email, username, name, avatar
- **Note**: OAuth 2.0 (similar to GitHub flow)
- **Free Tier**: Unlimited
- **Docs**: https://docs.gitlab.com/ee/integration/oauth_provider.html
- **Why GitLab**: Popular in DevOps/enterprise, self-hosted options, covers non-GitHub users

**Apple Sign In** ❌ **EXCLUDED**
- **Difficulty**: ⭐⭐⭐ Medium-Hard (more complex setup)
- **Cost**: $99/year Apple Developer Program (**blocker**)
- **Decision**: Excluded due to cost and complexity
- **Alternative**: Users with Apple ID can use email OTP fallback

---

#### 2.13.3 Recommended OIDC Implementation

**Approach**: Use `authlib` library (FastAPI-compatible)

**Architecture**:
```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Frontend  │────────▶│   Backend    │────────▶│ OIDC Provider   │
│  (Alpine.js)│         │   (FastAPI)  │         │ (Google/GitHub) │
└─────────────┘         └──────────────┘         └─────────────────┘
      │                        │                         │
      │  1. Click "Login"      │                         │
      ├────────────────────────▶                         │
      │  2. Redirect to        │                         │
      │     /auth/login/google │                         │
      │                        ├────────────────────────▶│
      │                        │  3. Redirect to Google  │
      │                        │     with client_id      │
      │◀───────────────────────┴─────────────────────────┤
      │  4. User authenticates with Google               │
      │────────────────────────┬─────────────────────────▶
      │                        │  5. Redirect back with  │
      │                        │     authorization code  │
      │                        ◀─────────────────────────┤
      │                        │  6. Exchange code for   │
      │                        │     access_token        │
      │                        ├────────────────────────▶│
      │                        ◀─────────────────────────┤
      │                        │  7. Get user info       │
      │  8. Set JWT cookie     │     (email, name)       │
      ◀────────────────────────┤                         │
      │  9. Redirect to app    │                         │
      │     (authenticated)    │                         │
```

**Backend Code Structure**:

```python
# backend/src/auth/oidc_providers.py
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config('.env')

oauth = OAuth(config)

# Google
oauth.register(
    name='google',
# GitHub
oauth.register(
    name='github',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

# GitLab
oauth.register(
    name='gitlab',
    access_token_url='https://gitlab.com/oauth/token',
    authorize_url='https://gitlab.com/oauth/authorize',
    api_base_url='https://gitlab.com/api/v4/',
    client_kwargs={'scope': 'read_user email'}
)auth.register(
    name='apple',
    server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email name'}
)
```

```python
# backend/src/api/auth.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from ..auth.oidc_providers import oauth
from ..services.user_service import UserService
from ..auth.jwt_handler import create_jwt_token

router = APIRouter(prefix="/auth", tags=["authentication"])
@router.get("/login/{provider}")
async def login(request: Request, provider: str):
    """Initiate OIDC login flow"""
    if provider not in ['google', 'github', 'gitlab']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    if provider not in ['google', 'github', 'apple']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    redirect_uri = request.url_for('auth_callback', provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)

@router.get("/callback/{provider}")
async def auth_callback(request: Request, provider: str):
    """Handle OIDC callback and create user session"""
    try:
        # Get access token from provider
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        
        # Get user info from provider
        if provider == 'google':
            user_info = token.get('userinfo')
            email = user_info.get('email')
            name = user_info.get('name')
        elif provider == 'github':
            resp = await client.get('user', token=token)
            user_info = resp.json()
            email = user_info.get('email')
            name = user_info.get('name') or user_info.get('login')
        elif provider == 'gitlab':
            resp = await client.get('user', token=token)
            user_info = resp.json()
            email = user_info.get('email')
            name = user_info.get('name') or user_info.get('username')
        
        # Find or create user in our system
        user = user_service.find_or_create_by_email(email, name, provider)
        
        # Create JWT token
        jwt_token = create_jwt_token(user.id, email)
        
        # Redirect to frontend with token
        response = RedirectResponse(url=f"/?token={jwt_token}")
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            secure=True,  # HTTPS only
            samesite="lax"
        )
        return response
        
    except Exception as e:
        # Log error and redirect to login page
        print(f"OIDC callback error: {e}")
        return RedirectResponse(url="/?error=auth_failed")
```

**Frontend Code (Alpine.js)**:

```html
<!-- Login buttons -->
<div x-data="{ loggingIn: false }">
  <h2>Sign in to Vagrantfile Generator</h2>
  
  <button @click="window.location.href='/api/auth/login/google'"
          class="btn-google">
    <svg><!-- Google icon --></svg>
    Sign in with Google
  </button>
  
  <button @click="window.location.href='/api/auth/login/github'"
          class="btn-github">
    <svg><!-- GitHub icon --></svg>
    Sign in with GitHub
  </button>
  
  <button @click="window.location.href='/api/auth/login/gitlab'"
          class="btn-gitlab">
    <svg><!-- GitLab icon --></svg>
    Sign in with GitLab
  </button>
</div>

<script>
  // Extract token from URL (if redirected back)
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  
  if (token) {
    localStorage.setItem('jwt_token', token);
    // Remove token from URL
    window.history.replaceState({}, document.title, "/");
    // Reload to show authenticated state
    window.location.reload();
  }
</script>
```

---

#### 2.13.4 Implementation Effort Estimate

**OIDC: Google + GitHub + GitLab**:

| Task | Effort | Details |
|------|--------|---------|
| Install authlib | 5 min | `pip install authlib httpx` |
| Register with Google | 15 min | Create OAuth credentials |
| Register with GitHub | 10 min | Create OAuth app |
| Register with GitLab | 10 min | Create OAuth app |
| Backend OIDC endpoints | 2.5 hours | Login, callback, token handling (3 providers) |
| User service integration | 1 hour | Find/create user logic |
| Frontend login UI | 1.5 hours | 3 login buttons + styling |
| Token storage/handling | 1 hour | LocalStorage + auth headers |
| Testing | 2.5 hours | Manual testing + unit tests (3 providers) |
| Documentation | 1 hour | Setup guide for env vars |
| **Total** | **~11 hours** | **For 3 providers** |

**Email OTP with Mailgun EU**: ~8 hours
- Mailgun SDK integration: 1 hour
- OTP generation/validation: 2 hours
- Rate limiting: 2 hours
- Email templates: 1 hour
- Frontend OTP input: 1.5 hours
- Testing: 0.5 hours

**Hybrid Total**: ~19 hours (11h OIDC + 8h OTP)

**Verdict**: Hybrid approach provides maximum flexibility with reasonable effort.

---

#### 2.13.5 OIDC vs OTP Comparison

| Factor | OIDC (Google/GitHub) | Email OTP |
|--------|---------------------|-----------|
| **User Experience** | ⭐⭐⭐⭐⭐ One-click login | ⭐⭐⭐ Wait for email, type code |
| **Security** | ⭐⭐⭐⭐⭐ Managed by Google/GitHub | ⭐⭐⭐⭐ Good (if implemented well) |
| **Setup Complexity** | ⭐⭐⭐ One-time provider setup | ⭐⭐ Email service configuration |
| **Code Complexity** | ⭐⭐⭐ OAuth flow, library usage | ⭐⭐⭐ OTP generation, rate limits |
| **Dependencies** | External providers (Google/GitHub) | Email service (SendGrid/Resend) |
| **Cost** | 🆓 Free | 🆓 Free tier (limited emails) |
| **Privacy** | Provider sees your app usage | More private (direct email) |
| **Offline Users** | ❌ Requires provider access | ✅ Works if email works |
| **Email Deliverability** | N/A | ⚠️ Spam filters, delays |
| **Mobile Friendly** | ⭐⭐⭐⭐⭐ Seamless | ⭐⭐⭐ Copy/paste code |
| **Branding** | Provider login screens | Your email templates |
| **Account Recovery** | Handled by provider | Need separate flow |

---

#### 2.13.6 Hybrid Approach ✅ **SELECTED**

**Best of both worlds**: Support OIDC **AND** email OTP

**Strategy**:
1. **Primary**: OIDC (Google + GitHub + GitLab) for best UX
2. **Alternative**: Email OTP via Mailgun EU for users without social accounts or privacy-conscious users

**Benefits**:
- ✅ Maximum accessibility (users choose preferred method)
- ✅ Better conversion (one-click social login)
- ✅ Privacy option (OTP for those who want it)
- ✅ Redundancy (if OIDC provider has outage, OTP still works)
- ✅ No vendor lock-in (users not forced to use Google/GitHub/GitLab)
- ✅ GDPR-friendly (Mailgun EU region, user choice)

**Login Screen**:
```
┌─────────────────────────────────────────┐
│  Sign in to Vagrantfile Generator       │
├─────────────────────────────────────────┤
│                                         │
│  [🔵 Sign in with Google]              │
│  [⚫ Sign in with GitHub]              │
│  [🟠 Sign in with GitLab]              │
│                                         │
│  ─────────── OR ───────────            │
│                                         │
│  📧 Email: [________________]          │
│  [Send Login Code]                     │
│                                         │
│  Privacy-focused? Use email login      │
└─────────────────────────────────────────┘
```

**Implementation Phases**:
- **Phase 1A**: OIDC (Google + GitHub + GitLab) - 11 hours
- **Phase 1B**: Email OTP (Mailgun EU) - 8 hours
- **Total**: 19 hours for complete hybrid solution

---

#### 2.13.7 Required Environment Variables (OIDC + OTP)

```bash
# Google OIDC
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-secret

# GitLab OAuth
GITLAB_CLIENT_ID=your-gitlab-client-id
GITLAB_CLIENT_SECRET=your-gitlab-secret
GITLAB_BASE_URL=https://gitlab.com  # or self-hosted URL

# Mailgun (EU Region)
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=mg.your-domain.com
MAILGUN_API_BASE=https://api.eu.mailgun.net  # EU region endpoint
MAILGUN_FROM_EMAIL=noreply@your-domain.com
MAILGUN_FROM_NAME=Vagrantfile Generator

# OTP Configuration
OTP_EXPIRATION_MINUTES=15
OTP_MAX_ATTEMPTS=5
OTP_REQUEST_LIMIT_PER_HOUR=5

# General Auth
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application URLs
FRONTEND_URL=https://your-app.com
BACKEND_URL=https://api.your-app.com
```

---

#### 2.13.8 Testing OIDC Locally

**Challenge**: OAuth redirects require public URLs (can't use `localhost` with providers)

**Solutions**:

1. **Ngrok / Cloudflare Tunnel**
   - Expose local server to internet
   - Use tunnel URL in OAuth redirect settings
   - Free tier available

2. **Localhost Exception**
   - Google/GitHub allow `http://localhost:8000` in redirect URIs
   - Works for development testing
   - Configure separate OAuth app for local dev

3. **Mock OIDC Provider**
   - Use `authlib` test utilities
   - Fully offline testing
   - Faster test execution

**Recommended**: Use localhost exception for dev, mock provider for unit tests

---

#### 2.13.9 OIDC Decision Matrix

**Choose OIDC if**:
- ✅ Want professional, polished authentication
- ✅ Targeting public/hosted deployment
- ✅ Users likely have Google/GitHub accounts
- ✅ Want to avoid email deliverability issues
- ✅ Prefer battle-tested security (Google/GitHub handle it)

**Choose OTP if**:
- ✅ Want maximum control over auth flow
- ✅ Privacy is paramount (no third-party providers)
- ✅ Users may not have Google/GitHub accounts
- ✅ Want to avoid external dependencies
- ✅ Targeting enterprise/private deployments

**Choose Hybrid if**:
- ✅ Want maximum flexibility
- ✅ Can invest ~17 hours in auth implementation
- ✅ Want best UX + privacy options
- ✅ **RECOMMENDED for this project**

---

#### 2.13.10 OIDC Provider Recommendations

**✅ Selected Providers (Tier 1)**:
1. **Google** - Largest user base, excellent docs, reliable
2. **GitHub** - Perfect for developer tools, many tech users have accounts
3. **GitLab** - DevOps users, self-hosted enterprise options, covers non-GitHub developers

**Tier 2 (Consider Adding Later)**:
4. **Microsoft** - Enterprise users, good for business tools, Azure integrations
5. **Bitbucket** - Atlassian ecosystem users (smaller audience)

**❌ Excluded**:
6. **Apple** - Requires $99/year, complex setup, mobile-focused (not worth it for web app)
7. **Facebook** - Privacy concerns, declining developer trust, not professional

**For Vagrantfile Generator**: 
- Google + GitHub + GitLab should cover **95%+ of target users** (developers/DevOps)
- Email OTP covers remaining 5% + privacy-conscious users
- Total coverage: ~100% with hybrid approach

---

### 2.1.2 Deployment Modes: Self-Hosted vs Public Service

**Critical Design Decision**: The application needs to support two fundamentally different deployment scenarios.

---

#### Deployment Mode Comparison

| Aspect | Self-Hosted Mode | Public Service Mode |
|--------|------------------|---------------------|
| **Use Case** | Personal/team use, company internal | Public SaaS offering |
| **Authentication** | ❌ Disabled | ✅ Required (OIDC + OTP) |
| **User Management** | ❌ Not needed | ✅ Full multiuser support |
| **Data Structure** | `/data/shared/` (read-write) | `/data/shared/` (read-only) + `/data/users/{id}/` (read-write) |
| **Global Resources** | ✅ Full CRUD via UI | 🔒 Manual file editing only |
| **Projects Storage** | `/data/shared/projects/` | `/data/users/{id}/projects/` |
| **Data Isolation** | ❌ Single user/team | ✅ Per-user directories |
| **Deployment** | Docker/podman on local/private server | Cloud hosting (public URL) |
| **Configuration** | Simple (no auth setup) | Complex (auth providers, email) |
| **Target Users** | Developers, small teams, enterprises | General public, freelancers |

---

#### Unified Data Structure (Both Modes)

**Philosophy**: Single data structure for simplicity - deployment mode only changes permission model.

**Data Structure** (Always):
```
backend/data/
  shared/          # Global/system resources
    boxes/
      boxes.json
    plugins/
      {plugin-id}.json
    provisioners/
      {provisioner-id}.json
    triggers/
      {trigger-id}.json
    projects/      # Only in self-hosted mode
      {project-id}.json
  users/           # Only exists in public mode
    {user-id}/     # User-specific resources
      projects/
        {project-id}.json
      boxes/
      plugins/
      provisioners/
      triggers/
```

**Migration Path** (One-time operation):
```bash
# Move existing data to shared/
mkdir -p backend/data/shared
mv backend/data/boxes backend/data/shared/
mv backend/data/plugins backend/data/shared/
mv backend/data/provisioners backend/data/shared/
mv backend/data/triggers backend/data/shared/
mv backend/data/projects backend/data/shared/
```

---

#### Self-Hosted Mode Design

**Philosophy**: Full read-write access to `/data/shared/` - essentially "admin mode" for managing global resources.

**Configuration**:
```bash
DEPLOYMENT_MODE=self-hosted  # Default
```

**Behavior in Self-Hosted Mode**:

1. **No Authentication**:
   - App loads directly to Projects page (current behavior)
   - No login page, no OIDC, no OTP, no JWT
   - No user context needed

2. **Global Resources Management**:
   - **Full read-write access** to `/data/shared/` directory
   - Settings page provides full CRUD on all resources (boxes, plugins, provisioners, triggers)
   - Projects stored in `/data/shared/projects/` (no user isolation)
   - **No `/data/users/` directory exists** in this mode
   - No ownership/permission checks

3. **Simplified Backend**:
   - No authentication middleware
   - No user context in service layer
   - Direct file access to `/data/shared/`
   - Single-user assumptions throughout

**Benefits**:
- ✅ **Backwards compatible**: Existing deployments work without changes
- ✅ **Simple**: No auth setup, no email service, no OAuth apps
- ✅ **Fast**: No JWT validation overhead
- ✅ **Familiar**: Current users see no difference
**Benefits**:
- ✅ **Simple**: No auth setup, no email service, no OAuth apps
- ✅ **Fast**: No JWT validation overhead
- ✅ **Familiar**: Works like current version
- ✅ **Flexible**: Full control over shared resources via UI

**Use Cases**:
- Developer running locally for personal projects
- Small team with shared internal server (trusted environment)
- Enterprise with private deployment (behind VPN/firewall)
- Workshop/training environments

---

#### Public Service Mode Design

**Philosophy**: Authenticated users get read-write access to their own data (`/data/users/{user-id}/`) and read-only access to shared resources (`/data/shared/`).

**Configuration**:
```bash
DEPLOYMENT_MODE=public

# All auth-related env vars (from Section 2.13.7)
GOOGLE_CLIENT_ID=...
MAILGUN_API_KEY=...
# etc.
```

**Behavior in Public Service Mode**:

1. **Authentication Required**:
   - Landing page shows login options (OIDC + OTP)
   - All API endpoints require valid JWT
   - Session management, logout, etc.

2. **User Permissions**:
   - **Read-write**: `/data/users/{user-id}/` (own resources)
   - **Read-only**: `/data/shared/` (global resources)
   - Projects stored in `/data/users/{user-id}/projects/`
   - Can create custom boxes/plugins/provisioners/triggers in user directory

3. **Global Resources Management**:
   - `/data/shared/` managed via **direct file editing** (SSH/terminal)
   - Operators with server access edit JSON files manually
   - No special admin UI, no anonymous mode, no hard-coded admin
   - Simple, secure, no additional code complexity

**Benefits**:
- ✅ **Secure**: No unauthenticated admin endpoints
- ✅ **Simple**: No admin account management code
- ✅ **Flexible**: Full control via direct file access
- ✅ **Standard**: Common practice for system-level config

**Use Cases**:
- Public SaaS offering
- Shared hosting for multiple users
- Community/enterprise platforms

---

#### Managing Global/Shared Resources in Public Mode

**Approach: Direct File Editing** (Manual management via SSH/terminal)

**Concept**: Special environment variable enables unrestricted access to shared resources.

```bash
DEPLOYMENT_MODE=public
ALLOW_ANONYMOUS_ADMIN=true  # Enables global resource management without auth
```

**Behavior**:
- When `ALLOW_ANONYMOUS_ADMIN=true`:
  - Special endpoint `/admin/resources` accessible without JWT
  - Or: Settings page shows shared resources as editable (no lock icons)
  - Full CRUD on shared resources
  - **⚠️ Security Risk**: Only enable during setup/maintenance

**Workflow**:
1. Deploy app with `ALLOW_ANONYMOUS_ADMIN=true`
2. Access admin interface (no login required)
3. Add/update shared boxes, plugins, etc.
4. Set `ALLOW_ANONYMOUS_ADMIN=false` and restart
5. App now requires auth, shared resources are read-only

**Use Case**: Initial setup, periodic updates to shared catalog

**Security**:
- Only enable temporarily
- Use firewall rules to restrict access during admin mode
- Or: Require IP whitelist when `ALLOW_ANONYMOUS_ADMIN=true`

---

##### **Option B: Hard-Coded Admin Account**

**Concept**: Special admin user with elevated permissions.

```bash
DEPLOYMENT_MODE=public
ADMIN_EMAIL=admin@your-domain.com
ADMIN_PASSWORD=secure-admin-password  # Or use OTP to this email
```

**Behavior**:
- Admin user can authenticate normally (OIDC or OTP)
- Backend checks if authenticated user email matches `ADMIN_EMAIL`
- If admin: Can edit shared resources
- If regular user: Shared resources read-only

**Implementation**:
```python
# backend/src/middleware/auth.py
def get_current_user(token: str) -> User:
    user = validate_jwt(token)
    
    # Check if admin
    admin_email = os.getenv("ADMIN_EMAIL")
    if admin_email and user.email == admin_email:
        user.is_admin = True
    
    return user

# backend/src/services/plugin_service.py
def delete_plugin(self, plugin_id: str):
    user_file = self.user_dir / f"{plugin_id}.json"
    
    if user_file.exists():
        user_file.unlink()  # User's own plugin
    else:
        shared_file = self.shared_dir / f"{plugin_id}.json"
        if shared_file.exists():
            # Check if user is admin
            if not self.user.is_admin:
                raise PermissionError("Cannot delete shared resource")
            else:
                shared_file.unlink()  # Admin can delete shared
        else:
            raise PluginNotFoundError(plugin_id)
```

**UI Changes**:
- Admin sees Edit/Delete buttons on shared resources
- Settings page shows admin badge/indicator
- Regular users see lock icons (unchanged)

**Benefits**:
- ✅ Proper access control
- ✅ Audit trail (admin actions logged)
- ✅ No need to restart app

#### Managing Global/Shared Resources in Public Mode

**Approach: Direct File Editing** (Manual management via SSH/terminal)

**Concept**: System administrators manage `/data/shared/` resources by editing JSON files directly on the server.

**Workflow**:
1. SSH into server where app is deployed
2. Edit files in `/data/shared/boxes/`, `/data/shared/plugins/`, etc.
3. App automatically picks up changes (or restart if needed)

**Example - Adding a new shared box**:
```bash
# On server
cd /path/to/vagrantfile-generator/backend/data/shared/plugins

# Create new plugin file
cat > company-vpn.json << 'EOF'
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "company-vpn",
  "description": "Company VPN configuration plugin",
  "source": "internal",
  "install_command": "vagrant plugin install vagrant-company-vpn"
}
EOF

# Or edit existing boxes.json
nano ../boxes/boxes.json

# Restart app if needed (most file changes are picked up automatically)
docker-compose restart backend
```

**Benefits**:
- ✅ **Simplest**: No additional code needed
- ✅ **Secure**: Requires server access (already restricted)
- ✅ **Flexible**: Use any text editor, git for version control
- ✅ **Standard**: Common practice for system-level configuration
- ✅ **No UI complexity**: No admin roles, permissions, or special endpoints

**Drawbacks**:
- ❌ Requires server/SSH access
- ❌ Manual process (no UI)
- ❌ Harder for non-technical admins (but this is public SaaS - rare updates)

---

#### Implementation Strategy

**Unified Approach** (Single data structure, mode changes permissions):

```python
# backend/src/main.py
import os
from pathlib import Path

DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "self-hosted")
DATA_DIR = Path("/app/data")

# Ensure data structure exists
(DATA_DIR / "shared" / "boxes").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "shared" / "plugins").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "shared" / "provisioners").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "shared" / "triggers").mkdir(parents=True, exist_ok=True)

if DEPLOYMENT_MODE == "self-hosted":
    # Projects in shared directory (no users)
    (DATA_DIR / "shared" / "projects").mkdir(parents=True, exist_ok=True)
    # No authentication middleware
    # Full read-write to /data/shared/
else:  # public mode
    # Projects in user directories
    (DATA_DIR / "users").mkdir(parents=True, exist_ok=True)
    # Add JWT authentication middleware
    # Read-only for /data/shared/, read-write for /data/users/{user-id}/
```

**Service Layer Changes**:
```python
# backend/src/services/plugin_service.py
class PluginService:
    def __init__(self, user_id: Optional[str] = None):
        self.shared_dir = Path("/app/data/shared/plugins")
        self.user_id = user_id
        self.user_dir = Path(f"/app/data/users/{user_id}/plugins") if user_id else None
        
        if self.user_dir:
            self.user_dir.mkdir(parents=True, exist_ok=True)
    
    def list_plugins(self) -> List[Plugin]:
        """Return combined shared + user plugins"""
        plugins = []
        
        # Load shared plugins (always available)
        for file in self.shared_dir.glob("*.json"):
            plugin = Plugin.parse_file(file)
            plugin.is_shared = True  # Mark as read-only
            plugins.append(plugin)
        
        # Load user plugins (public mode only)
        if self.user_dir:
            for file in self.user_dir.glob("*.json"):
                plugin = Plugin.parse_file(file)
                plugin.is_shared = False
                plugins.append(plugin)
        
        return plugins
    
    def delete_plugin(self, plugin_id: str):
        """Delete plugin - only user's own plugins"""
        if self.user_dir:
            # Public mode: Check user directory only
            user_file = self.user_dir / f"{plugin_id}.json"
            if user_file.exists():
                user_file.unlink()
            else:
                raise PermissionError("Cannot delete shared resource")
        else:
            # Self-hosted mode: Can delete from shared directory
            shared_file = self.shared_dir / f"{plugin_id}.json"
            if shared_file.exists():
                shared_file.unlink()
            else:
                raise PluginNotFoundError(plugin_id)
```

---

#### Configuration Reference

**Self-Hosted Mode**:
```bash
# Minimal configuration
DEPLOYMENT_MODE=self-hosted  # Default
CORS_ORIGINS=http://localhost:5173
```

**Public Service Mode**:
```bash
DEPLOYMENT_MODE=public
CORS_ORIGINS=https://your-domain.com

# Authentication (required)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITLAB_CLIENT_ID=...
GITLAB_CLIENT_SECRET=...

# Mailgun (required)
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=mg.your-domain.com
MAILGUN_API_BASE=https://api.eu.mailgun.net

# JWT (required)
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# No admin config needed - use direct file editing
```

---

#### Migration Path

**One-Time Data Migration**:
```bash
# Move existing data to shared directory
mkdir -p backend/data/shared
mv backend/data/boxes backend/data/shared/
mv backend/data/plugins backend/data/shared/
mv backend/data/provisioners backend/data/shared/
mv backend/data/triggers backend/data/shared/
mv backend/data/projects backend/data/shared/  # For self-hosted mode
```

**For Self-Hosted Deployments**:
1. Pull updated version
2. Run migration script (one time)
3. Continue using as before (no config changes)
4. Full read-write access to `/data/shared/`

**To Enable Public Mode**:
1. Run migration script
2. Set `DEPLOYMENT_MODE=public`
3. Configure auth providers (Google, GitHub, GitLab, Mailgun)
4. Remove `/data/shared/projects/` (users will have own project directories)
5. Restart app
6. Users now authenticate and get isolated `/data/users/{user-id}/` directories
4. Migration moves `/data/` → `/data/shared/` (becomes global catalog)
5. Restart app
6. Users can now register and create their own resources

---

#### Recommended Approach Summary

**For Your Use Case** (public hosting + self-hosted support):

1. ✅ **Support both modes**: Self-hosted (current users) + Public (new offering)
2. ✅ **Default to self-hosted**: Backwards compatibility
3. ✅ **Public mode**: Full multiuser with OIDC + OTP
4. ✅ **Global resources**: Start with **Option C (manual file editing)**
   - Simplest to implement
   - Secure (requires server access)
   - Add admin UI later if needed (Option B)
   - Avoid Option A (security risk)

**Implementation Priority**:
1. **Week 1-3**: Implement public mode (auth + multiuser)
2. **Week 3-4**: Test self-hosted mode still works (backwards compatibility)
3. **Week 4**: Document both deployment modes
4. **Future**: Consider adding admin UI (Option B) if manual editing becomes tedious

**Why This Works**:
- ✅ **Backwards compatible**: Self-hosted users unaffected
- ✅ **Simple**: No admin UI to build initially
- ✅ **Secure**: Server access required for global resource changes
- ✅ **Flexible**: Can add admin account later if needed
- ✅ **Clear separation**: Self-hosted = simple, Public = full-featured

---

### 2.2 Session Management

**Requirements**:
- Track authenticated users
- Maintain session state between requests
- Handle session expiration

**Implementation Options**:

**Option 1: JWT Tokens**
- Stateless authentication
- Token contains user_id and expiration
- Frontend stores in localStorage/sessionStorage
- Backend validates token signature

**Option 2: Session Store (JSON-based)**
```
backend/data/sessions/
  {session-id}.json  # Contains user_id, created_at, expires_at
```

**Recommendation**: JWT Tokens
- Aligns with simplicity requirement
- No additional file I/O for session validation
- Scalable (stateless)
- Standard approach for SPAs

### 2.3 Email Delivery Service (Mailgun EU)

**Selected Provider**: **Mailgun (EU Region)** ✅

**Why Mailgun EU?**
- ✅ **GDPR Compliance**: EU data center (emails stored/processed in EU)
- ✅ **Reliability**: 99.99% uptime SLA, proven infrastructure
- ✅ **Developer-Friendly**: Simple REST API, excellent Python SDK
- ✅ **Analytics**: Detailed delivery tracking, open/click rates, bounce handling
- ✅ **Free Tier**: 5,000 emails/month for 3 months (sufficient for MVP/testing)
- ✅ **Paid Plans**: Reasonable pricing ($35/month for 50k emails after trial)
- ✅ **Email Validation API**: Built-in email verification (reduce bounces)

**Mailgun EU Setup**:
1. Sign up at https://signup.mailgun.com/new/signup (select EU region)
2. Add and verify your domain (or use Mailgun sandbox for testing)
3. Get API key from Settings → API Keys
4. Note: EU endpoint is `https://api.eu.mailgun.net` (NOT `.com`)

**Implementation with Mailgun Python SDK**:

```python
# backend/src/services/email_service.py
import requests
from datetime import datetime, timedelta
import secrets
import json
from pathlib import Path

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("MAILGUN_API_KEY")
        self.domain = os.getenv("MAILGUN_DOMAIN")
        self.api_base = os.getenv("MAILGUN_API_BASE", "https://api.eu.mailgun.net")
        self.from_email = os.getenv("MAILGUN_FROM_EMAIL")
        self.from_name = os.getenv("MAILGUN_FROM_NAME", "Vagrantfile Generator")
        
    def send_otp(self, to_email: str, otp_code: str) -> bool:
        """Send OTP code via Mailgun"""
        url = f"{self.api_base}/v3/{self.domain}/messages"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .otp-code {{ 
                    font-size: 32px; 
                    font-weight: bold; 
                    letter-spacing: 8px;
                    color: #2563eb;
                    background: #f3f4f6;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{ color: #6b7280; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Your Login Code</h2>
                <p>Use this code to sign in to Vagrantfile Generator:</p>
                <div class="otp-code">{otp_code}</div>
                <p>This code will expire in 15 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <div class="footer">
                    <p>Vagrantfile Generator - https://your-app.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_body = f"""
        Your Vagrantfile Generator Login Code
        
        {otp_code}
        
        This code will expire in 15 minutes.
        If you didn't request this code, please ignore this email.
        
        Vagrantfile Generator - https://your-app.com
        """
        
        try:
            response = requests.post(
                url,
                auth=("api", self.api_key),
                data={
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": to_email,
                    "subject": f"Your login code: {otp_code}",
                    "text": text_body,
                    "html": html_body,
                    "o:tag": ["otp", "authentication"],
                    "o:tracking": "yes"  # Track opens/clicks
                }
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Mailgun error: {e}")
            return False

class OTPService:
    def __init__(self):
        self.email_service = EmailService()
        self.otp_storage_path = Path("data/otp_codes.json")
        self.otp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
    def generate_otp(self) -> str:
        """Generate 6-digit OTP code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def send_otp(self, email: str) -> dict:
        """Generate and send OTP, return status"""
        # Check rate limiting
        if self._is_rate_limited(email):
            return {
                "success": False,
                "error": "Too many requests. Please wait before requesting another code.",
                "retry_after": self._get_retry_after(email)
            }
        
        # Generate OTP
        otp_code = self.generate_otp()
        expires_at = datetime.now() + timedelta(minutes=15)
        
        # Send via Mailgun
        if self.email_service.send_otp(email, otp_code):
            # Store OTP
            self._store_otp(email, otp_code, expires_at)
            return {
                "success": True,
                "message": "OTP sent successfully",
                "expires_in_minutes": 15
            }
        else:
            return {
                "success": False,
                "error": "Failed to send email. Please try again."
            }
    
    def verify_otp(self, email: str, otp_code: str) -> dict:
        """Verify OTP code"""
        stored = self._get_stored_otp(email)
        
        if not stored:
            return {"success": False, "error": "No OTP found for this email"}
        
        # Check expiration
        if datetime.now() > datetime.fromisoformat(stored["expires_at"]):
            self._delete_otp(email)
            return {"success": False, "error": "OTP expired"}
        
        # Check attempts
        if stored.get("attempts", 0) >= 5:
            self._delete_otp(email)
            return {"success": False, "error": "Too many failed attempts"}
        
        # Verify code
        if stored["code"] == otp_code:
            self._delete_otp(email)
            return {"success": True, "email": email}
        else:
            # Increment attempts
            stored["attempts"] = stored.get("attempts", 0) + 1
            self._store_otp_data(email, stored)
            remaining = 5 - stored["attempts"]
            return {
                "success": False,
                "error": f"Invalid code. {remaining} attempts remaining"
            }
    
    # ... (rate limiting and storage methods)
```

**Mailgun Advantages for OTP**:
- **Deliverability**: High inbox placement rate (not marked as spam)
- **Speed**: Emails typically delivered in < 5 seconds
- **Tracking**: See if emails were opened, bounced, or failed
- **EU Compliance**: Data sovereignty for European users
- **Webhooks**: Get notified of delivery events (optional)

### 2.4 Rate Limiting & Security

**Critical Considerations**:

1. **OTP Request Rate Limiting**
   - Prevent spam/abuse of email sending
   - Limit: 3-5 OTP requests per email per hour
   - Implementation: In-memory cache or JSON file with timestamps

2. **OTP Validation Attempts**
   - Prevent brute force attacks
   - Limit: 5 attempts per OTP
   - OTP expiration: 10-15 minutes

3. **Email Validation**
   - Basic format validation
   - Consider: Email verification on first registration
   - Disposable email blocking (optional)

4. **CORS Configuration**
   - Update allowed origins based on deployment
   - Already partially implemented in `main.py`

**Proposed Rate Limit Storage** (JSON):
```json
{
  "user@example.com": {
    "otp_requests": [
      {"timestamp": "2025-11-13T10:00:00Z"},
      {"timestamp": "2025-11-13T10:05:00Z"}
    ],
    "last_otp": {
      "code": "encrypted_otp",
      "created_at": "2025-11-13T10:05:00Z",
      "attempts": 2
    }
  }
}
```

### 2.5 User Data Model

**Minimal User Schema**:
```python
class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True)
    
    # Optional metadata
    display_name: Optional[str] = None  # Derived from email or set by user
```

**Storage**: `backend/data/users/{user-id}.json`

**Index for Email Lookup**: `backend/data/users/email_index.json`
```json
{
  "user@example.com": "user-uuid-1",
  "another@example.com": "user-uuid-2"
}
```

### 2.6 Migration Strategy

**Current State**: No user concept exists

**Migration Path**:

1. **Phase 1: Add User System (Backward Compatible)**
   - Introduce user models and authentication
   - Create "system" or "default" user for existing data
   - All current projects assigned to default user
   - Multi-user disabled by feature flag initially

2. **Phase 2: Enable Multi-User**
   - Allow new user registrations
   - Migrate existing data to directory structure
   - Enable authentication middleware

3. **Phase 3: Cleanup**
   - Remove default user (if desired)
   - Enforce authentication on all endpoints

**Data Migration Script Needed**: 
- Move `data/projects/*.json` → `data/users/{default-user-id}/projects/*.json`
- Same for plugins, provisioners, triggers

### 2.7 API Changes

**New Endpoints Required**:

```
# OIDC Authentication
GET    /api/auth/login/{provider}           # Initiate OIDC flow (google/github/gitlab)
GET    /api/auth/callback/{provider}        # OIDC callback handler

# Email OTP Authentication
POST   /api/auth/otp/request                # Request OTP code (send to email)
POST   /api/auth/otp/verify                 # Verify OTP and get JWT

# Common
GET    /api/auth/me                         # Get current user info
POST   /api/auth/logout                     # Invalidate session (optional)
POST   /api/auth/refresh                    # Refresh JWT token (optional)
```

**Example OTP Endpoint Implementation**:

```python
# backend/src/api/auth_otp.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from ..services.otp_service import OTPService
from ..services.user_service import UserService
from ..auth.jwt_handler import create_jwt_token

router = APIRouter(prefix="/auth/otp", tags=["authentication"])
otp_service = OTPService()
user_service = UserService()

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    code: str

@router.post("/request")
async def request_otp(request: OTPRequest):
    """Send OTP code to email via Mailgun"""
    result = otp_service.send_otp(request.email)
    
    if result["success"]:
        return {
            "message": "OTP sent successfully",
            "expires_in_minutes": 15
        }
    else:
        raise HTTPException(
            status_code=429 if "Too many requests" in result["error"] else 500,
            detail=result["error"]
        )

@router.post("/verify")
async def verify_otp(request: OTPVerify):
    """Verify OTP and return JWT token"""
    result = otp_service.verify_otp(request.email, request.code)
    
    if result["success"]:
        # Find or create user
        user = user_service.find_or_create_by_email(
            request.email, 
            provider="email"
        )
        
        # Create JWT
        token = create_jwt_token(user.id, request.email)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email
            }
        }
    else:
        raise HTTPException(
            status_code=401,
            detail=result["error"]
        )
```

**Existing Endpoints Updates**:
- All project/VM endpoints require authentication (user-scoped)
- Plugin/provisioner/trigger endpoints return **merged view** (shared + user resources)
- Add user_id context to service layer
- Filter results by authenticated user + shared resources

**Resource Access Logic**:
```python
# Example for GET /api/plugins
def get_plugins(user_id: str) -> List[Plugin]:
    user_plugins = load_from_dir(f"data/users/{user_id}/plugins/")
    shared_plugins = load_from_dir("data/shared/plugins/")
    
    # Merge, user plugins override shared if same ID
    all_plugins = {p.id: p for p in shared_plugins}
    all_plugins.update({p.id: p for p in user_plugins})
    
    return list(all_plugins.values())

# Example for DELETE /api/plugins/{plugin_id}
def delete_plugin(user_id: str, plugin_id: str):
    user_plugin_path = f"data/users/{user_id}/plugins/{plugin_id}.json"
    
    if exists(user_plugin_path):
        delete_file(user_plugin_path)  # OK - user owns it
    else:
        # Check if it's a shared resource
        shared_path = f"data/shared/plugins/{plugin_id}.json"
        if exists(shared_path):
            raise HTTPException(403, "Cannot delete shared resource")
        else:
            raise HTTPException(404, "Plugin not found")
```

**API Response Metadata** (Optional - helpful for UI):
```json
{
  "id": "plugin-uuid",
  "name": "vagrant-vbguest",
  "scope": "shared",  // or "user"
  "read_only": true   // true if scope=shared
}
```

**Middleware Required**:
- JWT validation middleware
- Attach user context to request
- Handle unauthorized responses (401)

### 2.8 Frontend Changes

**Authentication Flow**:

1. **Landing Page** (if not authenticated)
   - OIDC login buttons (Google, GitHub, GitLab)
   - Email input form
   - "Send Login Code" button

2. **OTP Verification Page** (if using email auth)
   - 6-digit code input
   - "Verify" button
   - "Resend OTP" link (with rate limit feedback)

3. **Authenticated App**
   - Store JWT in localStorage
   - Add Authorization header to all API requests
   - Handle token expiration (redirect to login)
   - Display user email in header/user menu

**Settings Page Updates** (See Section 2.1.1 for detailed design):
- Add visual indicators for shared vs user resources (🔒 vs 👤)
- Add scope badges ("System Box" vs "My Box")
- Conditionally show Edit/Delete buttons based on resource ownership
- Add filter dropdown (All / System / My Resources)
- Update "Add" flows to create in user directory
- Show empty state for new users ("No custom resources yet")
- Add `scope` and `read_only` fields to resource displays

**Alpine.js Considerations**:
- Simple state management for auth status
- Minimal additional complexity
- Use Alpine.js `x-data` for auth state
- Intercept fetch calls to add auth header
- Add computed property for filtering resources by scope
- Handle resource CRUD with ownership checks

### 2.9 S3 Storage Discussion

**Why S3?**
- Scalability beyond single server
- Better for hosted/cloud deployments
- Backup and disaster recovery
- Multi-region support

**When to Implement?**
- Not initially (JSON files sufficient)
- Consider when:
  - User base grows significantly
  - Need horizontal scaling
  - Deploying to cloud infrastructure

**Implementation Strategy**:
- Abstract storage layer (Repository pattern)
- Create interface: `StorageBackend` (read/write/delete/list)
- Implementations:
  - `FileSystemStorage` (current JSON approach)
  - `S3Storage` (future)
- Environment variable to switch: `STORAGE_BACKEND=filesystem|s3`

**S3 Structure**:
```
bucket-name/
  users/
    {user-id}/
      projects/
        {project-id}.json
      ...
  shared/
    boxes/
      boxes.json
```

### 2.10 Testing Considerations

**New Test Coverage Needed**:

1. **Authentication Tests**
   - OTP generation and validation
   - JWT creation and verification
   - Rate limiting enforcement
   - Email sending (mocked)

2. **Authorization Tests**
   - User can only access their own projects
   - User cannot access other users' resources
   - Unauthenticated requests rejected

3. **Data Isolation Tests**
   - Multiple users with same project names
   - Resource IDs unique per user
   - No cross-user data leakage

4. **Migration Tests**
   - Existing data properly migrated
   - Default user assignment works
   - No data loss during migration

### 2.11 Configuration & Environment Variables

**New Environment Variables**:

```bash
# Deployment Mode (See Section 2.1.2)
DEPLOYMENT_MODE=self-hosted  # or "public" (default: self-hosted)

# Public Mode - Authentication (only required in public mode)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
OTP_EXPIRATION_MINUTES=15
OTP_MAX_ATTEMPTS=5

# Public Mode - OIDC Providers
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITLAB_CLIENT_ID=...
GITLAB_CLIENT_SECRET=...

# Public Mode - Email Service (Mailgun)
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=mg.your-domain.com
MAILGUN_API_BASE=https://api.eu.mailgun.net
MAILGUN_FROM_EMAIL=noreply@vagrantfile-generator.com
MAILGUN_FROM_NAME=Vagrantfile Generator

# Public Mode - Rate Limiting
OTP_REQUEST_LIMIT_PER_HOUR=5
OTP_REQUEST_WINDOW_MINUTES=60

# Storage (future, both modes)
STORAGE_BACKEND=filesystem  # or s3
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```
JWT_EXPIRATION_HOURS=24
OTP_EXPIRATION_MINUTES=15
OTP_MAX_ATTEMPTS=5

# Public Mode - Email Service (Mailgun)
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=mg.your-domain.com
MAILGUN_API_BASE=https://api.eu.mailgun.net
MAILGUN_FROM_EMAIL=noreply@vagrantfile-generator.com
MAILGUN_FROM_NAME=Vagrantfile Generator

# Public Mode - Rate Limiting
OTP_REQUEST_LIMIT_PER_HOUR=5
OTP_REQUEST_WINDOW_MINUTES=60

# Public Mode - Shared Resource Management (Optional)
ALLOW_ANONYMOUS_ADMIN=false  # Dangerous! Only for initial setup
ADMIN_EMAIL=admin@yourdomain.com  # If using hard-coded admin (Option B)

# Storage (future)
STORAGE_BACKEND=filesystem  # or s3
S3_BUCKET=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

### 2.12 User Experience Considerations

**Onboarding Flow**:
1. User visits app → sees email prompt
2. Enters email → receives OTP
3. Enters OTP → authenticated, sees their projects
4. First-time user → empty project list with welcome message

**Session Persistence**:
- Remember user for 24 hours (JWT expiration)
- Optional "Remember me" → longer expiration (7 days)
- Clear session on explicit logout

**Error Handling**:
- Clear error messages for OTP failures
- Rate limit notifications ("Please wait X minutes")
- Email delivery issues (retry mechanism)

**Accessibility**:
- OTP input should be accessible
- Clear labels and error states
- Keyboard navigation support

---

## 3. Implementation Phases

### Phase 1A: OIDC Authentication (Week 1, ~11 hours)
- [ ] Install authlib dependency
- [ ] Register OAuth apps (Google, GitHub, GitLab)
- [ ] Implement OIDC providers configuration
- [ ] Create auth endpoints (`/login/{provider}`, `/callback/{provider}`)
- [ ] User service: find or create by email + provider
- [ ] JWT token generation and validation
- [ ] Basic testing with all 3 providers

### Phase 1B: Email OTP with Mailgun (Week 1-2, ~8 hours)
- [ ] Set up Mailgun EU account and domain
- [ ] Implement EmailService (Mailgun API integration)
- [ ] Implement OTPService (generate, store, verify)
- [ ] Create OTP endpoints (`/otp/request`, `/otp/verify`)
- [ ] Rate limiting mechanism for OTP requests
- [ ] Email template design (HTML + plain text)
- [ ] Testing OTP flow end-to-end

### Phase 2: Backend Integration (Week 2-3, ~8 hours)
- [ ] Implement shared/user resource directory structure
- [ ] Update service layer for user context (PluginService, etc.)
- [ ] Implement merged resource view logic
- [ ] Authentication middleware (JWT validation)
- [ ] Protect existing endpoints with auth
- [ ] Data migration script (move current data to `/shared/`)
- [ ] Backend unit and integration tests

### Phase 3: Frontend (Week 3-4, ~8 hours)
- [ ] Login page UI (3 OIDC buttons + email form)
- [ ] OTP verification page (6-digit input)
- [ ] JWT storage in localStorage
- [ ] Auth state management (Alpine.js)
- [ ] Add Authorization headers to API calls
- [ ] Session persistence and logout
- [ ] **Settings page redesign** (Section 2.1.1):
  - [ ] Add scope indicators (🔒 system vs 👤 user icons)
  - [ ] Add scope badges ("System Box" vs "My Box")
  - [ ] Conditional Edit/Delete buttons (based on ownership)
  - [ ] Add filter dropdown (All / System / My Resources)
  - [ ] Empty state for new users
  - [ ] Update all resource types (boxes, plugins, provisioners, triggers)

### Phase 4: Testing & Security (Week 4, ~4 hours)
- [ ] End-to-end auth testing (all providers + OTP)
- [ ] Security audit (rate limiting, JWT expiry, etc.)
- [ ] Cross-user data isolation tests
- [ ] Error handling improvements
- [ ] API documentation updates

### Phase 5: Documentation & Launch (Week 5, ~3 hours)
- [ ] Environment variables setup guide
- [ ] OAuth app registration guides (Google/GitHub/GitLab)
- [ ] Mailgun setup documentation
- [ ] User-facing auth documentation
- [ ] Deployment guide updates
- [ ] Beta testing with real users

**Total Estimated Effort**: ~42 hours (11h OIDC + 8h OTP + 8h backend + 8h frontend + 4h testing + 3h docs)
- [ ] Production deployment

---

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Email deliverability issues | High - users can't log in | Use reputable email service, implement retry logic, provide support contact |
| OTP brute force attacks | High - security breach | Strong rate limiting, account lockout after X failures, monitoring |
| JWT secret compromise | Critical - auth bypass | Store in secure env vars, rotate regularly, use strong random keys |
| Data migration failures | High - data loss | Comprehensive testing, backup before migration, rollback plan |
| Scalability beyond JSON files | Medium - performance | Abstract storage layer early, plan S3 migration path |
| Session hijacking | High - unauthorized access | HTTPS only, short JWT expiration, secure token storage guidance |

---

## 5. Open Questions

1. **Should we support email change after registration?**
   - If yes, require OTP to new email for verification

2. **Account deletion / data export?**
   - GDPR compliance considerations
   - Export all user data as ZIP?

3. ~~**Admin users / roles?**~~ ✅ **RESOLVED** (See Section 2.1.2)
   - Self-hosted mode: No admin needed (single user)
   - Public mode: Manual file editing for shared resources (Option C)
   - Future: Can add admin account (Option B) if needed

4. ~~**Shared resource management?**~~ ✅ **RESOLVED** (See Section 2.1.2)
   - Self-hosted: Direct CRUD in Settings page
   - Public: Manual file editing (SSH to server, edit JSON)
   - Alternative: Anonymous admin mode or hard-coded admin account

5. **Public/shared projects?**
   - Should users be able to share project URLs?
   - Read-only access for non-owners?

6. **Email from address / branding?**
   - Custom domain needed?
   - "noreply@" vs "support@"?

7. **Multiple sessions per user?**
   - Allow login from multiple devices?
   - Currently JWT is stateless, so yes by default

8. **User analytics / telemetry?**
   - Track user activity for product improvements?
   - Privacy considerations

9. **Deployment mode detection?** ✅ **RESOLVED**
   - Use `DEPLOYMENT_MODE` environment variable
   - Default: `self-hosted` (backwards compatibility)

---

## 6. Dependencies & Libraries

**Python Backend (Hybrid Auth)**:
```
# OIDC/OAuth
authlib                   # OIDC/OAuth client library (Google/GitHub/GitLab)
httpx                     # HTTP client (required by authlib)

# JWT
python-jose[cryptography] # JWT token handling

# Email (Mailgun)
requests                  # For Mailgun API calls (simpler than full SDK)

# Validation
pydantic[email]          # Email validation

# Other
python-multipart          # Form data handling
```

**Optional Python Packages**:
```
mailgun                   # Official Mailgun SDK (alternative to requests)
```

**Frontend**:
- No additional dependencies needed (Alpine.js sufficient)
- Alpine.js handles auth state and UI interactions
- Native fetch API for HTTP requests

---

## 7. Alternative Approaches Considered

### 7.1 OAuth2 / OIDC with External Provider
**Pros**: Industry standard, battle-tested, social login options  
**Cons**: Complex setup, external dependencies  
**Decision**: ✅ **ACCEPTED** - Detailed analysis in Section 2.13 shows complexity is manageable with authlib library. Google + GitHub recommended.

### 7.2 Password-based Authentication
**Pros**: Familiar to users, no email dependency  
**Cons**: Password management complexity, security risks, recovery flows  
**Decision**: Rejected in favor of passwordless authentication

### 7.3 Magic Links instead of OTP
**Pros**: No code to type, one-click login  
**Cons**: Email client issues, link expiration handling, less user control  
**Decision**: Could be future alternative, OTP more predictable for now

### 7.4 Database (PostgreSQL/SQLite) instead of JSON
**Pros**: Better querying, transactions, relationships  
**Cons**: Additional infrastructure, migration complexity from current JSON  
**Decision**: Stick with JSON initially, but design with DB migration in mind

---

## 8. Success Criteria

**Must Have**:
- ✅ Users can authenticate with Google or GitHub (OIDC)
- ✅ Users authenticated via JWT
- ✅ Complete data isolation between users (user-scoped directories)
- ✅ Shared resources available to all users (read-only)
- ✅ Users can create custom resources in their namespace
- ✅ Existing data preserved during migration (moved to /shared)
- ✅ No security vulnerabilities introduced

**Should Have**:
- ✅ Clear UI distinction between shared and user resources
- ✅ Session persists for reasonable time (24 hours)
- ✅ Logout functionality works
- ✅ Tests cover authentication flows
- ✅ Email OTP fallback (optional, for users without Google/GitHub)

**Nice to Have**:
- User profile editing (display name, avatar from provider)
- Usage statistics per user
- S3 storage backend option
- Microsoft/GitLab provider support

---

## 9. Next Steps

1. ✅ **Review this document** - Finalized hybrid strategy
2. ✅ **Decide on authentication strategy** - **Hybrid: Google/GitHub/GitLab OIDC + Mailgun OTP**
3. **Register OAuth apps**:
   - [ ] Google Cloud Console OAuth credentials
   - [ ] GitHub Developer Settings OAuth app
   - [ ] GitLab Applications OAuth app
4. **Set up Mailgun**:
   - [ ] Create Mailgun account (EU region)
   - [ ] Add and verify domain
   - [ ] Get API key
5. **Create proof of concept**:
   - [ ] OIDC flow with authlib (1 provider)
   - [ ] OTP flow with Mailgun
   - [ ] JWT token generation
6. **Implement shared/user resource model** - Update service layer
7. **Full implementation** - Follow Phase 1-5 plan
8. **Testing and launch**

---

## 10. References & Resources

**Authentication**:
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Authlib Documentation](https://docs.authlib.org/en/latest/)
- [Python-JOSE Documentation](https://python-jose.readthedocs.io/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheatsheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

**OIDC Providers**:
- [Google OpenID Connect](https://developers.google.com/identity/protocols/oauth2/openid-connect)
- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps)
- [GitLab OAuth Applications](https://docs.gitlab.com/ee/integration/oauth_provider.html)

**Email Service**:
- [Mailgun Documentation](https://documentation.mailgun.com/en/latest/)
- [Mailgun API Reference](https://documentation.mailgun.com/en/latest/api_reference.html)
- [Mailgun EU Region Setup](https://help.mailgun.com/hc/en-us/articles/203068914-What-are-the-differences-between-the-US-and-EU-regions-)

---

## 11. Discussion Summary & Decisions

### ✅ Final Decisions (Nov 13, 2025)

**1.1 Deployment Modes** (See Section 2.1.2):
- ✅ **Two deployment modes**: Self-Hosted (default) + Public Service
- ✅ **Self-Hosted Mode**: No authentication, preserves current functionality, backwards compatible
- ✅ **Public Mode**: Full multiuser with OIDC + OTP authentication
- ✅ **Configuration**: `DEPLOYMENT_MODE` environment variable
- ✅ **Admin Management (Public Mode)**: Manual file editing via SSH/terminal (Option C - RECOMMENDED)
  - Simple, secure, no UI complexity
  - Alternatives: Anonymous admin mode (Option A - risky) or hard-coded admin account (Option B - more complex)
- ✅ **Migration Path**: Existing users continue using self-hosted mode seamlessly

**1.2 Authentication - Hybrid Strategy SELECTED** (Public Mode):
- ✅ **OIDC Providers**: Google + GitHub + GitLab (3 providers, ~11 hours)
- ✅ **Email OTP**: Mailgun EU Region (~8 hours)
- ✅ **Total Auth Effort**: ~19 hours for complete hybrid solution
- ✅ **User Choice**: Social login (convenience) OR email OTP (privacy)
- ✅ **Coverage**: 95%+ with OIDC, 100% with email OTP fallback
- ❌ **Apple excluded**: $99/year cost not justified

**Mailgun EU Selection**:
- ✅ GDPR-compliant (EU data center)
- ✅ 99.99% uptime SLA
- ✅ Simple REST API
- ✅ 5,000 emails/month free trial
- ✅ Excellent deliverability

**2.1 Data Structure - Unified Approach**:
- ✅ **Single data structure**: Always use `/data/shared/` + `/data/users/{id}/` (no dual structure)
- ✅ **Self-Hosted Mode**: Read-write access to `/data/shared/`, projects in `/data/shared/projects/`
- ✅ **Public Mode**: Read-only `/data/shared/`, read-write `/data/users/{user-id}/`, projects per-user
- ✅ **Migration**: One-time move of existing data to `/data/shared/` (simple, clean)
- ✅ **No backwards compatibility needed**: Clean break, unified architecture
- ✅ **Benefits**: 
  - Single codebase, simpler implementation
  - Self-hosted = admin mode for global resources
  - Public = isolated user resources + shared catalog
  - Consistent structure regardless of deployment mode

**2.1.1 Settings Page UI/UX** (Public Mode):
- ✅ **Selected: Option 1 - Single List with Visual Indicators**
- ✅ Shows all resources in unified lists (boxes, plugins, provisioners, triggers)
- ✅ Visual distinction: 🔒 (shared/system) vs 👤 (user-owned)
- ✅ "Delete" button disabled for shared resources
- ✅ Tooltip on hover explains shared vs user-owned
- ✅ Benefits: Minimal code changes, familiar UX, clear permissions

**2.1.2 Admin Management** (Public Mode):
- ✅ **Direct file editing** - Manual management of `/data/shared/` via SSH/terminal
- ✅ No anonymous admin mode, no hard-coded admin accounts
- ✅ Simple, secure, no additional code complexity

**Implementation Summary**:
1. **Deployment**: Two modes via `DEPLOYMENT_MODE` env var (self-hosted default)
2. **Auth Strategy (Public Mode)**: Hybrid (OIDC + OTP)
3. **OIDC Providers**: Google, GitHub, GitLab
4. **Email Service**: Mailgun EU
5. **Data Model**: Unified structure, permissions change based on mode
6. **Session Management**: JWT tokens (stateless, 24-hour expiration) in public mode
7. **Storage**: JSON files in `/data/shared/` and `/data/users/{id}/` (unified)
8. **Migration**: One-time migration to `/data/shared/`, no backwards compatibility
9. **Admin Management**: Direct file editing for shared resources in public mode

**Estimated Timeline**:
- **Phase 1A**: OIDC implementation - 11 hours
- **Phase 1B**: OTP/Mailgun implementation - 8 hours
- **Phase 2**: Backend services + data model - 8 hours
- **Phase 3**: Frontend - 6 hours
- **Phase 4**: Testing & security - 4 hours
- **Phase 5**: Documentation - 3 hours
- **Total**: ~40 hours (approximately 1 week full-time or 2 weeks part-time)

**Next Immediate Actions**:
1. Register OAuth apps with Google, GitHub, GitLab
2. Create Mailgun EU account and verify domain
3. Set up development environment variables
4. Begin Phase 1A: OIDC proof of concept
3. **Data Model**: Shared resources (read-only) + user resources (full control)
4. **Session Management**: JWT tokens (stateless, 24-hour expiration)
5. **Storage**: JSON files with `/shared/` and `/users/{user-id}/` structure
6. **Migration**: Move existing data to `/shared/` directory

**Implementation Priority**:
1. **Phase 1** (9 hours): OIDC (Google + GitHub) + JWT
2. **Phase 2** (8 hours): Shared/User resource model in services
3. **Phase 3** (8 hours): Frontend auth + resource UI
4. **Phase 4** (optional, 8 hours): Email OTP fallback
5. **Total**: 25-33 hours depending on OTP inclusion

---

**Document Version**: 3.0  
**Last Updated**: November 13, 2025 (Finalized: Hybrid Auth with Google/GitHub/GitLab + Mailgun EU)  
**Author**: Development Team Discussion  
**Status**: Ready for Implementation  
**Next Review**: After Phase 1 proof of concept

---

## Quick Reference Card

### Deployment Modes
| Mode | Authentication | Use Case | Admin Management |
|------|----------------|----------|------------------|
| **Self-Hosted** | None (optional basic HTTP auth) | Personal/team deployments | Direct file editing |
| **Public** | OIDC + Email OTP required | Public SaaS offering | Manual file editing (recommended) |

**Configuration**: `DEPLOYMENT_MODE=self-hosted` or `public` (default: self-hosted)

### Authentication Stack (Public Mode)
| Component | Choice | Effort |
|-----------|--------|--------|
| **OIDC Providers** | Google, GitHub, GitLab | 11 hours |
| **Email OTP** | Mailgun EU Region | 8 hours |
| **Session** | JWT (24h expiration) | Included |
| **Library** | authlib + python-jose | Included |

### Data Structure

**Unified Structure** (both modes):
```
data/
  shared/           # Global/system resources
    boxes/
    plugins/
    provisioners/
    triggers/
    projects/       # Only in self-hosted mode
  users/            # Only in public mode
    {user-id}/      # User-specific resources
      projects/
      boxes/
      plugins/
      provisioners/
      triggers/
```

**Permissions by Mode**:
- **Self-hosted**: Read-write to `/data/shared/`, no `/data/users/`
- **Public**: Read-only `/data/shared/`, read-write `/data/users/{user-id}/`

### Environment Variables

**Self-Hosted Mode (Minimal)**:
```bash
DEPLOYMENT_MODE=self-hosted  # Default
```

**Public Mode (Required)**:
```bash
DEPLOYMENT_MODE=public

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITLAB_CLIENT_ID=...
GITLAB_CLIENT_SECRET=...

# Mailgun
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=mg.your-domain.com
MAILGUN_API_BASE=https://api.eu.mailgun.net

# Auth
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Key Dependencies
```bash
pip install authlib httpx python-jose[cryptography] requests pydantic[email]
```

### Total Implementation: ~42 hours (~1-2 weeks)

### Settings Page Design (Section 2.1.1)
- **Single list** with visual indicators (🔒 system vs 👤 user)
- **Filter options**: All / System / My Resources
- **Actions**: System resources = "View Details" only, User resources = "Edit" + "Delete"
- **Applies to**: Boxes, Plugins, Provisioners, Triggers
