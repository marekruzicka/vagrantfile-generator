# Multi-User Authentication - Developer Quick Start

**Feature Branch**: `001-multiuser-auth`  
**Spec**: [specs/001-multiuser-auth/spec.md](./spec.md)  
**Status**: Planning complete, implementation pending

---

## Overview

This guide helps you set up a local development environment to implement and test the multi-user authentication feature. The feature adds deployment mode switching (self-hosted vs public) with hybrid authentication (email OTP + OIDC).

### What You'll Build

- **Self-hosted mode**: No authentication, full access to shared resources (current behavior)
- **Public mode**: Email OTP or OIDC authentication required, isolated user data with read-only shared resources

---

## Prerequisites

- **Python 3.11+** installed
- **Podman or Docker** with Compose support
- **Mailgun account** (free tier works) for email OTP testing
- Optional: **Google/GitHub/GitLab OAuth app** for OIDC testing (can skip initially)

---

## Quick Setup

### 1. Install Backend Dependencies

```bash
cd backend/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (including new auth libraries)
pip install -r requirements.txt

# New dependencies added for this feature:
# - PyJWT==2.8.0         # JWT token generation/validation
# - authlib==1.3.0       # OIDC authentication flows
# - requests==2.31.0     # Mailgun API integration
```

### 2. Configure Environment Variables

Create `backend/.env` file with deployment mode and authentication settings:

```bash
# Deployment Mode
DEPLOYMENT_MODE=public  # Options: "self-hosted" | "public"

# JWT Configuration (generate random secret: openssl rand -hex 32)
JWT_SECRET=your-random-secret-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email OTP Configuration (Mailgun API)
MAILGUN_API_KEY=your-mailgun-api-key-here
MAILGUN_DOMAIN=sandbox1234567890.mailgun.org  # Your Mailgun domain
MAILGUN_FROM_EMAIL=noreply@sandbox1234567890.mailgun.org
OTP_EXPIRATION_MINUTES=15
OTP_MAX_ATTEMPTS=5

# Rate Limiting
RATE_LIMIT_WINDOW_HOURS=1
RATE_LIMIT_MAX_REQUESTS=5

# OIDC Configuration (Optional - can skip for initial testing)
# Google OAuth
OIDC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
OIDC_GITHUB_CLIENT_ID=your-github-client-id
OIDC_GITHUB_CLIENT_SECRET=your-github-client-secret

# GitLab OAuth
OIDC_GITLAB_CLIENT_ID=your-gitlab-application-id
OIDC_GITLAB_CLIENT_SECRET=your-gitlab-secret
```

**For self-hosted mode testing**, use this minimal `.env`:

```bash
DEPLOYMENT_MODE=self-hosted
# No other variables needed - authentication disabled
```

### 3. Get Mailgun API Credentials

1. Sign up at [mailgun.com](https://www.mailgun.com/) (free tier: 5,000 emails/month)
2. Navigate to **Sending → Domain Settings → API Keys**
3. Copy your **Private API key**
4. Copy your **Sandbox domain** (e.g., `sandbox1234567890.mailgun.org`)
5. Add **authorized recipients** in sandbox settings to test with your email

### 4. Run Backend with Containers (Recommended)

```bash
# From repository root
make dev-up

# Backend runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### 5. Run Backend Directly (Alternative)

```bash
cd backend/
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Testing Email OTP Flow

### Test OTP Request Endpoint

```bash
# Request OTP code
curl -X POST http://localhost:8000/api/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "your-authorized-email@example.com"}'

# Expected response:
# {
#   "message": "Verification code sent to your-authorized-email@example.com",
#   "expires_in": 900
# }
```

**Check your email** for the 6-digit OTP code (arrives within seconds).

### Test OTP Verification

```bash
# Verify OTP code
curl -X POST http://localhost:8000/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-authorized-email@example.com",
    "code": "123456"
  }'

# Expected response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "user": {
#     "user_id": "550e8400-e29b-41d4-a716-446655440000",
#     "email": "your-authorized-email@example.com",
#     "auth_provider": "email",
#     "created_at": "2025-11-13T14:30:00Z",
#     "last_login": "2025-11-13T14:30:00Z"
#   },
#   "expires_at": "2025-11-14T14:30:00Z"
# }
```

**Save the JWT token** - you'll use it to authenticate subsequent requests.

### Test Authenticated Endpoint

```bash
# Get current user profile
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

# Expected response:
# {
#   "user_id": "550e8400-e29b-41d4-a716-446655440000",
#   "email": "your-authorized-email@example.com",
#   "auth_provider": "email",
#   "created_at": "2025-11-13T14:30:00Z",
#   "last_login": "2025-11-13T14:30:00Z"
# }
```

### Test Rate Limiting

```bash
# Send 6 OTP requests rapidly (5 should succeed, 6th fails)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/otp/request \
    -H "Content-Type: application/json" \
    -d '{"email": "your-email@example.com"}'
  echo ""
done

# 6th request expected response:
# {
#   "error": "Rate limit exceeded",
#   "detail": "Maximum 5 OTP requests per hour. Try again later."
# }
```

---

## Testing Resource Isolation (Public Mode)

### Create User-Specific Project

```bash
# Authenticated request to create project
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Personal Dev Environment",
    "description": "Testing user isolation"
  }'

# Project saved to: /data/users/{user_id}/projects/{project_id}.json
```

### List Projects (Shared + User's)

```bash
# Get all accessible projects
curl http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

# Response includes:
# - Shared projects from /data/shared/projects/ (is_shared: true, no edit/delete)
# - User's projects from /data/users/{user_id}/projects/ (is_shared: false, full CRUD)
```

### Attempt to Modify Shared Resource (Should Fail)

```bash
# Try to update shared project
curl -X PUT http://localhost:8000/api/projects/SHARED_PROJECT_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "Hacked Name"}'

# Expected response:
# {
#   "error": "Permission denied",
#   "detail": "Shared resources are read-only"
# }
```

---

## Testing Self-Hosted Mode

### Switch to Self-Hosted Mode

```bash
# Update backend/.env
DEPLOYMENT_MODE=self-hosted

# Restart backend
make dev-restart
```

### Access Without Authentication

```bash
# No auth required - works immediately
curl http://localhost:8000/api/projects

# All endpoints accessible without Authorization header
# All resources stored in /data/shared/
```

---

## OIDC Testing (Optional)

### Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → APIs & Services → Credentials
3. Create **OAuth 2.0 Client ID**
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/auth/callback/google`
4. Copy Client ID and Client Secret to `backend/.env`

### Test OIDC Flow

```bash
# Open in browser (will redirect to Google login):
http://localhost:8000/api/auth/oidc/google

# After authorization, redirects back to:
http://localhost:8000/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Extract token from URL and use for authenticated requests
```

---

## Frontend Integration

### Store Token in LocalStorage

```javascript
// After successful OTP verification or OIDC callback
const token = responseData.token;
localStorage.setItem('session_token', token);
```

### Add Auth Header to API Requests

```javascript
// Alpine.js data component
Alpine.data('apiClient', () => ({
    async fetchProjects() {
        const token = localStorage.getItem('session_token');
        const headers = token 
            ? { 'Authorization': `Bearer ${token}` }
            : {};
        
        const response = await fetch('/api/projects', { headers });
        return response.json();
    }
}));
```

### Check Authentication Status

```javascript
async function checkAuth() {
    const token = localStorage.getItem('session_token');
    if (!token) return null;
    
    const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 401) {
        // Token expired - clear and redirect to login
        localStorage.removeItem('session_token');
        window.location.href = '/login';
        return null;
    }
    
    return response.json();
}
```

---

## Data Storage Locations

### Self-Hosted Mode
```
/data/shared/
  ├── boxes/boxes.json
  ├── plugins/{plugin-id}.json
  ├── provisioners/{provisioner-id}.json
  ├── triggers/{trigger-id}.json
  └── projects/{project-id}.json
```

### Public Mode
```
/data/
  ├── shared/  # Read-only for all users
  │   ├── boxes/boxes.json
  │   ├── plugins/{plugin-id}.json
  │   ├── provisioners/{provisioner-id}.json
  │   └── triggers/{trigger-id}.json
  ├── auth/  # Authentication data
  │   ├── otp-requests.json  # In-memory + file persistence
  │   └── rate-limits.json   # In-memory + file persistence
  └── users/{user-id}/  # Per-user isolated data
      ├── profile.json
      ├── plugins/{plugin-id}.json
      ├── provisioners/{provisioner-id}.json
      ├── triggers/{trigger-id}.json
      └── projects/{project-id}.json
```

---

## Development Workflow

### 1. Start with Email OTP (Priority 1)
- Implement OTP request endpoint (`/api/auth/otp/request`)
- Implement OTP verification endpoint (`/api/auth/otp/verify`)
- Add rate limiting logic
- Test with Mailgun sandbox

### 2. Add Session Management (Priority 2)
- Implement JWT token generation
- Create authentication middleware (FastAPI dependency)
- Implement `/api/auth/me` endpoint
- Test token expiration handling

### 3. Implement Data Isolation (Priority 1)
- Create `FileService` methods for user-specific paths
- Update resource endpoints to check `is_shared` flag
- Enforce read-only permissions on shared resources
- Test cross-user access prevention

### 4. Add OIDC Support (Priority 3)
- Implement `/api/auth/oidc/{provider}` redirect
- Implement `/api/auth/callback/{provider}` handler
- Test with Google OAuth (easiest to set up)
- Extend to GitHub and GitLab

---

## Troubleshooting

### OTP Email Not Arriving

**Check Mailgun dashboard** → Sending → Logs for delivery status.

Common issues:
- Email not in authorized recipients (sandbox mode)
- Invalid API key or domain
- Rate limiting triggered

### JWT Token Invalid

```bash
# Decode JWT to inspect claims (paste token at jwt.io)
# Check expiration: "exp" field should be future timestamp
```

### Permission Denied Errors

- Verify `DEPLOYMENT_MODE=public` in `.env`
- Check JWT token includes correct `user_id` claim
- Confirm resource `owner_id` matches authenticated user

### OIDC Redirect Fails

- Verify redirect URI matches OAuth app settings exactly
- Check client ID and secret are correct
- Ensure provider is enabled in environment variables

---

## Testing with Chrome DevTools MCP

### User Flow Testing

```javascript
// Test OTP login flow
await mcp_chrome_devtools.navigate_page({ 
    type: 'url', 
    url: 'http://localhost:8000/login' 
});

await mcp_chrome_devtools.fill({ 
    uid: 'email-input', 
    value: 'test@example.com' 
});

await mcp_chrome_devtools.click({ uid: 'request-otp-button' });

// Check email manually for OTP code, then:
await mcp_chrome_devtools.fill({ 
    uid: 'otp-code-input', 
    value: '123456' 
});

await mcp_chrome_devtools.click({ uid: 'verify-otp-button' });

// Verify redirect to main app
await mcp_chrome_devtools.wait_for({ text: 'Dashboard' });
```

---

## Next Steps

1. **Implement authentication endpoints** following [contracts/auth-api.yaml](./contracts/auth-api.yaml)
2. **Update resource endpoints** per [contracts/resources-api.yaml](./contracts/resources-api.yaml)
3. **Create login UI** (Alpine.js component with email OTP form)
4. **Add visual indicators** for shared vs. user resources in settings pages
5. **Test data isolation** with multiple user accounts

---

## References

- **Full Specification**: [spec.md](./spec.md)
- **Data Model**: [data-model.md](./data-model.md)
- **API Contracts**: [contracts/auth-api.yaml](./contracts/auth-api.yaml), [contracts/resources-api.yaml](./contracts/resources-api.yaml)
- **Technical Research**: [research.md](./research.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Mailgun API Docs**: https://documentation.mailgun.com/en/latest/api-sending.html
- **PyJWT Docs**: https://pyjwt.readthedocs.io/
- **Authlib OIDC Guide**: https://docs.authlib.org/en/latest/client/frameworks.html
