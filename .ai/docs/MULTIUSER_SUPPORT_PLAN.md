# Multiuser Support - Implementation Plan

**Date**: November 13, 2025  
**Status**: ✅ Ready for Implementation  
**Version**: 1.0

---

## 📋 Executive Summary

This document outlines the implementation plan for adding multiuser support to the Vagrantfile Generator application. The design supports two deployment modes: self-hosted (simple, no auth) and public (full multiuser with authentication).

**Key Features**:
- Hybrid authentication (OIDC + Email OTP)
- Unified data structure with deployment-specific permissions
- User-owned resources (boxes, plugins, provisioners, triggers)
- Shared system resources catalog
- ~42 hours total implementation effort

---

## 1. Deployment Modes

### 1.1 Overview

The application supports two deployment modes controlled by the `DEPLOYMENT_MODE` environment variable:

| Mode | Use Case | Authentication | Data Access |
|------|----------|----------------|-------------|
| **self-hosted** | Personal/team deployments | None | Full read-write to `/data/shared/` |
| **public** | Public SaaS offering | Required (OIDC + OTP) | User: RW `/data/users/{id}/`, RO `/data/shared/` |

**Default**: `self-hosted` (simplest configuration)

### 1.2 Self-Hosted Mode

**Purpose**: Personal or small team deployments in trusted environments.

**Characteristics**:
- No authentication required
- Full read-write access to `/data/shared/` directory
- Projects stored in `/data/shared/projects/`
- No `/data/users/` directory needed
- Essentially "admin mode" for managing global resources

**Use Cases**:
- Developer working locally
- Small team with shared internal server
- Enterprise private deployment (behind VPN/firewall)
- Workshop/training environments

**Configuration**:
```bash
DEPLOYMENT_MODE=self-hosted  # Default, can be omitted
```

### 1.3 Public Mode

**Purpose**: Public-facing SaaS deployment with multiple untrusted users.

**Characteristics**:
- Authentication required (OIDC or Email OTP)
- Users get isolated `/data/users/{user-id}/` directory (read-write)
- Shared resources in `/data/shared/` are read-only for users
- Projects stored per-user in `/data/users/{user-id}/projects/`
- JWT-based session management

**Use Cases**:
- Public SaaS offering
- Shared hosting platform
- Community/enterprise multi-tenant deployments

**Configuration**:
```bash
DEPLOYMENT_MODE=public

# Required authentication settings
GOOGLE_CLIENT_ID=...
GITHUB_CLIENT_ID=...
GITLAB_CLIENT_ID=...
MAILGUN_API_KEY=...
JWT_SECRET_KEY=...
```

---

## 2. Data Structure

### 2.1 Unified Directory Layout

**Single structure for both modes** (permissions vary by deployment mode):

```
backend/data/
  shared/                    # Global/system resources
    boxes/
      boxes.json            # Official Vagrant boxes catalog
    plugins/
      {plugin-id}.json      # Common plugins
    provisioners/
      {provisioner-id}.json # Example provisioner templates
    triggers/
      {trigger-id}.json     # Example trigger configurations
    projects/               # Only in self-hosted mode
      {project-id}.json
  
  users/                    # Only in public mode
    {user-id}/              # Per-user isolated resources
      projects/
        {project-id}.json
      boxes/
        {box-id}.json
      plugins/
        {plugin-id}.json
      provisioners/
        {provisioner-id}.json
      triggers/
        {trigger-id}.json
```

### 2.2 Resource Resolution (Public Mode)

When listing resources in public mode:

1. Load all resources from `/data/shared/{resource-type}/`
2. Load user's resources from `/data/users/{user-id}/{resource-type}/`
3. Merge and return combined list
4. Mark shared resources with `is_shared: true` flag

**Example - User sees**:
- 50 shared boxes (from `/data/shared/boxes/`)
- 2 custom boxes (from `/data/users/alice-123/boxes/`)
- **Total**: 52 boxes displayed in UI

### 2.3 Permission Model

| Operation | Self-Hosted Mode | Public Mode (Shared) | Public Mode (User) |
|-----------|------------------|----------------------|--------------------|
| **List** | ✅ All resources | ✅ Read-only | ✅ Full access |
| **Create** | ✅ In `/shared/` | ❌ Forbidden | ✅ In `/users/{id}/` |
| **Update** | ✅ Any resource | ❌ Forbidden | ✅ Own resources only |
| **Delete** | ✅ Any resource | ❌ Forbidden | ✅ Own resources only |

### 2.4 Migration Path

**One-time migration** (run before first deployment):

```bash
#!/bin/bash
# migrate_to_shared.sh

mkdir -p backend/data/shared

mv backend/data/boxes backend/data/shared/
mv backend/data/plugins backend/data/shared/
mv backend/data/provisioners backend/data/shared/
mv backend/data/triggers backend/data/shared/
mv backend/data/projects backend/data/shared/

echo "Migration complete. Existing data moved to /data/shared/"
```

**Note**: This is a breaking change. All deployments must run this migration once.

---

## 3. Authentication (Public Mode)

### 3.1 Hybrid Strategy

Users can authenticate via **either** method:

1. **OIDC Social Login** (Google, GitHub, GitLab) - Preferred for convenience
2. **Email OTP** (6-digit code via Mailgun EU) - Privacy-focused alternative

**Benefits**:
- Maximum accessibility (~95% coverage with OIDC, 100% with email fallback)
- User choice (social vs privacy)
- No password management complexity

### 3.2 OIDC Providers

**Selected Providers**: Google, GitHub, GitLab

| Provider | Developer Audience | Free Tier | Setup Complexity |
|----------|-------------------|-----------|------------------|
| Google | ✅ High | ✅ Unlimited | ⭐⭐ Moderate |
| GitHub | ✅ Very High | ✅ Unlimited | ⭐ Easy |
| GitLab | ✅ High | ✅ Unlimited | ⭐ Easy |

**Why these three?**
- Free, no usage limits
- Developer-focused (target audience)
- Simple OAuth 2.0 / OIDC setup
- Combined coverage: ~95% of developers

**Excluded**: Apple Sign In (requires $99/year Apple Developer account)

**Implementation**: Use `authlib` library (Python)

### 3.3 Email OTP

**Service**: Mailgun EU Region

**Why Mailgun EU?**
- GDPR-compliant (EU data center)
- 99.99% uptime SLA
- Simple REST API
- 5,000 emails/month free tier
- Excellent deliverability

**Flow**:
1. User enters email address
2. Backend generates 6-digit code (valid 15 minutes)
3. Send via Mailgun API
4. User enters code
5. Backend validates and issues JWT

**Rate Limiting**: 5 OTP requests per hour per email

### 3.4 Session Management

**Method**: JWT tokens (stateless)

**Configuration**:
- Algorithm: HS256
- Expiration: 24 hours
- Storage: Browser localStorage
- Transmitted: Authorization header (`Bearer {token}`)

**Token Payload**:
```json
{
  "user_id": "uuid-v4",
  "email": "user@example.com",
  "name": "User Name",
  "auth_provider": "google|github|gitlab|email",
  "iat": 1234567890,
  "exp": 1234654290
}
```

---

## 4. User Interface

### 4.1 Login Page (Public Mode)

**Layout**: Single page with two sections

**Section 1 - Social Login** (Preferred):
```
┌─────────────────────────────────┐
│   Continue with Google   [🔵]   │
│   Continue with GitHub   [⚫]   │
│   Continue with GitLab   [🟠]   │
└─────────────────────────────────┘
```

**Section 2 - Email OTP** (Alternative):
```
┌─────────────────────────────────┐
│  Or sign in with email          │
│  ┌───────────────────────────┐  │
│  │ Email address             │  │
│  └───────────────────────────┘  │
│  [Send Code]                    │
└─────────────────────────────────┘
```

### 4.2 Settings Page (Public Mode)

**Design**: Single list with visual indicators (minimal changes from current UI)

**Visual Indicators**:
- 🔒 icon = Shared/system resource (read-only)
- 👤 icon = User-owned resource (editable)

**Example - Plugins List**:
```
┌────────────────────────────────────────────────────┐
│ Plugins                                  [+ Add]   │
├────────────────────────────────────────────────────┤
│ 🔒 vagrant-vbguest                    [View]       │
│    System Plugin                                   │
│                                                    │
│ 🔒 vagrant-disksize                   [View]       │
│    System Plugin                                   │
│                                                    │
│ 👤 my-custom-plugin            [Edit] [Delete]     │
│    My Plugin                                       │
└────────────────────────────────────────────────────┘
```

**Behavior**:
- Shared resources: View-only, no Edit/Delete buttons
- User resources: Full Edit/Delete functionality
- Tooltip on hover explains read-only vs editable
- "Add" button always creates in user directory

**Filter Dropdown** (optional):
- All Resources
- System Resources Only
- My Resources Only

### 4.3 Self-Hosted Mode UI

**No changes** from current implementation:
- No login page
- Settings page shows full CRUD on all resources
- No visual indicators needed (everything is editable)

---

## 5. Backend Implementation

### 5.1 Service Layer Pattern

```python
# backend/src/services/plugin_service.py
from pathlib import Path
from typing import List, Optional
import os

class PluginService:
    def __init__(self, user_id: Optional[str] = None):
        self.deployment_mode = os.getenv("DEPLOYMENT_MODE", "self-hosted")
        self.shared_dir = Path("/app/data/shared/plugins")
        
        # Public mode: user has own directory
        if self.deployment_mode == "public" and user_id:
            self.user_id = user_id
            self.user_dir = Path(f"/app/data/users/{user_id}/plugins")
            self.user_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Self-hosted mode: no user directory
            self.user_id = None
            self.user_dir = None
    
    def list_all(self) -> List[Plugin]:
        """Return combined shared + user plugins"""
        plugins = []
        
        # Always load shared plugins
        for file in self.shared_dir.glob("*.json"):
            plugin = Plugin.parse_file(file)
            plugin.is_shared = True
            plugins.append(plugin)
        
        # Load user plugins (public mode only)
        if self.user_dir:
            for file in self.user_dir.glob("*.json"):
                plugin = Plugin.parse_file(file)
                plugin.is_shared = False
                plugins.append(plugin)
        
        return plugins
    
    def create(self, plugin_data: dict) -> Plugin:
        """Create new plugin"""
        plugin_id = str(uuid.uuid4())
        
        if self.deployment_mode == "public" and self.user_dir:
            # Public mode: save to user directory
            file_path = self.user_dir / f"{plugin_id}.json"
        else:
            # Self-hosted mode: save to shared directory
            file_path = self.shared_dir / f"{plugin_id}.json"
        
        plugin = Plugin(id=plugin_id, **plugin_data)
        file_path.write_text(plugin.json())
        return plugin
    
    def delete(self, plugin_id: str):
        """Delete plugin - enforce permissions"""
        if self.user_dir:
            # Public mode: can only delete user's own plugins
            user_file = self.user_dir / f"{plugin_id}.json"
            if user_file.exists():
                user_file.unlink()
            else:
                raise PermissionError("Cannot delete shared resource")
        else:
            # Self-hosted mode: can delete from shared directory
            shared_file = self.shared_dir / f"{plugin_id}.json"
            if shared_file.exists():
                shared_file.unlink()
            else:
                raise PluginNotFoundError(plugin_id)
```

### 5.2 Authentication Middleware

```python
# backend/src/middleware/auth.py
from fastapi import Request, HTTPException
from jose import jwt, JWTError
import os

DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "self-hosted")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")

async def auth_middleware(request: Request, call_next):
    # Skip auth in self-hosted mode
    if DEPLOYMENT_MODE == "self-hosted":
        return await call_next(request)
    
    # Public mode: require JWT
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        request.state.user_id = payload["user_id"]
        request.state.user_email = payload["email"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return await call_next(request)
```

### 5.3 API Endpoints

**Authentication Endpoints** (public mode only):

```
POST   /api/auth/oidc/{provider}        # Initiate OIDC flow (google|github|gitlab)
GET    /api/auth/callback/{provider}    # OIDC callback handler
POST   /api/auth/otp/request            # Request OTP via email
POST   /api/auth/otp/verify             # Verify OTP code
POST   /api/auth/logout                 # Invalidate session (client-side)
GET    /api/auth/me                     # Get current user info
```

**Resource Endpoints** (all modes):

```
# Plugins
GET    /api/plugins                     # List all (shared + user)
POST   /api/plugins                     # Create plugin
GET    /api/plugins/{id}                # Get plugin details
PUT    /api/plugins/{id}                # Update plugin (user-owned only)
DELETE /api/plugins/{id}                # Delete plugin (user-owned only)

# Similar for: boxes, provisioners, triggers, projects
```

---

## 6. Managing Shared Resources (Public Mode)

### 6.1 Direct File Editing

**Approach**: System administrators manage `/data/shared/` via SSH/terminal access.

**Workflow**:

```bash
# SSH into server
ssh admin@your-server.com

# Navigate to shared plugins directory
cd /app/data/shared/plugins

# Create new shared plugin
cat > company-vpn-plugin.json << 'EOF'
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "company-vpn",
  "description": "Company VPN configuration",
  "install_command": "vagrant plugin install vagrant-company-vpn"
}
EOF

# Or edit existing shared resources
nano ../boxes/boxes.json

# Changes are immediately available to all users
```

**Benefits**:
- ✅ Simplest implementation (no additional code)
- ✅ Secure (requires server access)
- ✅ Flexible (use any editor, git for version control)
- ✅ Standard practice for system configuration

**No admin UI needed** - keeps codebase simple.

---

## 7. Implementation Phases

### Phase 1: OIDC Authentication (11 hours)

**Tasks**:
- Register OAuth apps with Google, GitHub, GitLab
- Implement OIDC flow using `authlib`
- Create `/api/auth/oidc/{provider}` endpoints
- Implement callback handlers
- JWT token generation
- Store user info in `/data/users/{user-id}/profile.json`

**Deliverable**: Users can log in with Google/GitHub/GitLab

### Phase 2: Email OTP (8 hours)

**Tasks**:
- Set up Mailgun EU account and verify domain
- Implement OTP generation (6 digits, 15min expiry)
- Create `/api/auth/otp/request` and `/api/auth/otp/verify` endpoints
- Email template design (HTML + plain text)
- Rate limiting (5 requests/hour per email)
- OTP validation logic

**Deliverable**: Users can log in with email OTP

### Phase 3: Backend Data Model (8 hours)

**Tasks**:
- Update service layer to support `user_id` context
- Implement resource resolution (shared + user merge)
- Add permission checks (can't modify shared resources)
- Update all services: PluginService, BoxService, ProvisionerService, TriggerService
- Add `is_shared` flag to resource models
- Create deployment mode detection logic

**Deliverable**: Backend enforces multiuser data isolation

### Phase 4: Frontend Updates (8 hours)

**Tasks**:
- Create login page (OIDC + OTP forms)
- Implement JWT storage (localStorage)
- Add Authorization header to all API requests
- Update Settings page with visual indicators (🔒/👤)
- Handle token expiration (redirect to login)
- Add user info display in header/menu
- Add logout functionality

**Deliverable**: Complete user-facing auth flow

### Phase 5: Testing & Security (4 hours)

**Tasks**:
- Authentication flow tests (OIDC + OTP)
- Permission enforcement tests
- Data isolation tests (users can't see each other's data)
- Rate limiting tests
- JWT validation tests
- Security audit (OWASP checklist)

**Deliverable**: Tested, secure multiuser system

### Phase 6: Documentation (3 hours)

**Tasks**:
- Update README with deployment modes
- Document environment variables
- Write migration guide
- Create setup instructions (OAuth apps, Mailgun)
- API documentation updates

**Deliverable**: Complete documentation

---

## 8. Configuration Reference

### 8.1 Environment Variables

**Self-Hosted Mode (Minimal)**:
```bash
DEPLOYMENT_MODE=self-hosted  # Default, can be omitted
```

**Public Mode (Full Configuration)**:
```bash
# Deployment Mode
DEPLOYMENT_MODE=public

# OIDC Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITLAB_CLIENT_ID=your-gitlab-client-id
GITLAB_CLIENT_SECRET=your-gitlab-client-secret

# Mailgun Email Service
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=mg.your-domain.com
MAILGUN_API_BASE=https://api.eu.mailgun.net
MAILGUN_FROM_EMAIL=noreply@vagrantfile-generator.com
MAILGUN_FROM_NAME=Vagrantfile Generator

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OTP Configuration
OTP_EXPIRATION_MINUTES=15
OTP_MAX_ATTEMPTS=5
OTP_REQUEST_LIMIT_PER_HOUR=5
```

### 8.2 OAuth Application Setup

**Google**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://your-domain.com/api/auth/callback/google`

**GitHub**:
1. Go to Settings → Developer settings → OAuth Apps
2. Create new OAuth app
3. Set callback URL: `https://your-domain.com/api/auth/callback/github`

**GitLab**:
1. Go to User Settings → Applications
2. Create new application
3. Set redirect URI: `https://your-domain.com/api/auth/callback/gitlab`
4. Select scopes: `read_user`, `email`

### 8.3 Mailgun Setup

1. Create account at [Mailgun](https://www.mailgun.com/) (select EU region)
2. Add and verify your domain
3. Get API key from dashboard
4. Test email delivery

---

## 9. Dependencies

### 9.1 Python Packages

```bash
pip install authlib httpx python-jose[cryptography] requests pydantic[email]
```

**Package Purposes**:
- `authlib` - OIDC client library
- `httpx` - Async HTTP client for authlib
- `python-jose` - JWT encoding/decoding
- `requests` - Mailgun API calls
- `pydantic[email]` - Email validation

### 9.2 Frontend (No new dependencies)

Current Alpine.js setup is sufficient.

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Service layer permission checks
- JWT token generation/validation
- OTP generation/validation
- Resource resolution logic (shared + user merge)

### 10.2 Integration Tests

- Full OIDC flow (mocked providers)
- Email OTP flow (mocked Mailgun)
- API endpoints with authentication
- Data isolation between users

### 10.3 Security Tests

- Invalid JWT rejection
- Expired token handling
- Rate limiting enforcement
- Permission boundary violations
- XSS/CSRF protection

---

## 11. Effort Estimate

| Phase | Description | Hours |
|-------|-------------|-------|
| 1 | OIDC Implementation | 11 |
| 2 | Email OTP | 8 |
| 3 | Backend Data Model | 8 |
| 4 | Frontend Updates | 8 |
| 5 | Testing & Security | 4 |
| 6 | Documentation | 3 |
| **Total** | | **42 hours** |

**Timeline**: ~1 week full-time or 2 weeks part-time

---

## 12. Success Criteria

### 12.1 Self-Hosted Mode

- ✅ App works without authentication
- ✅ Full read-write access to all resources
- ✅ No breaking changes from previous version
- ✅ Migration script moves data to `/data/shared/`

### 12.2 Public Mode

- ✅ Users can log in via Google/GitHub/GitLab
- ✅ Users can log in via email OTP
- ✅ Users only see/edit their own projects
- ✅ Users see shared + own resources in Settings
- ✅ Users cannot modify shared resources
- ✅ Session persists for 24 hours
- ✅ No data leakage between users

### 12.3 Security

- ✅ All API endpoints protected in public mode
- ✅ JWT validation on every request
- ✅ Rate limiting on OTP requests
- ✅ No permission escalation vulnerabilities
- ✅ OWASP security checklist passed

---

## 13. Future Enhancements (Out of Scope)

These features are **not** included in the initial 42-hour implementation:

- S3 storage backend (currently filesystem only)
- User profile editing
- Usage statistics per user
- Admin dashboard UI
- Microsoft/Apple authentication providers
- Two-factor authentication (beyond email OTP)
- Audit logging
- Resource sharing between users
- Team/organization support

---

## Appendix: Decisions Log

### A. Alternative Options Considered (Declined)

See [MULTIUSER_SUPPORT_DISCUSSION.md](./MULTIUSER_SUPPORT_DISCUSSION.md) for detailed analysis of declined options:

**Authentication Alternatives**:
- ❌ Password-based authentication (complex, security burden)
- ❌ Apple Sign In (requires $99/year)
- ❌ Email magic links (less secure than OTP)

**Settings UI Alternatives**:
- ❌ Tabbed interface (more code changes)
- ❌ Collapsible sections (cluttered)

**Admin Management Alternatives** (Public Mode):
- ❌ Anonymous admin mode (security risk)
- ❌ Hard-coded admin account (added complexity)

**Data Structure Alternatives**:
- ❌ Dual structure (self-hosted uses old, public uses new)
- ❌ Database storage (overkill for current scale)

### B. Key Discussion Points

1. **Why hybrid auth?** - Maximize coverage (95%+ OIDC, 100% with email)
2. **Why Mailgun EU?** - GDPR compliance, reliability, free tier
3. **Why no backwards compatibility?** - Cleaner codebase, one-time migration acceptable
4. **Why no admin UI?** - Simplicity, direct file editing is standard practice

---

**Document Version**: 1.0  
**Last Updated**: November 13, 2025  
**Status**: ✅ Approved for Implementation  
**Next Steps**: Begin Phase 1 (OIDC Implementation)
