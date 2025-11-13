# Technical Research: Multi-User Authentication

**Feature**: 001-multiuser-auth  
**Date**: 2025-11-13  
**Purpose**: Resolve technical unknowns for implementing hybrid authentication (Email OTP + OIDC) with file-based storage

---

## 1. OIDC Client Library

### Decision: **authlib**

### Rationale:
- Comprehensive OAuth 2.0 and OIDC implementation (spec-compliant)
- Native FastAPI/Starlette integration via `authlib.integrations.starlette_client`
- Handles provider discovery, token exchange, userinfo retrieval automatically
- Actively maintained with security updates
- Supports all three target providers (Google, GitHub, GitLab) out of the box

### Alternatives Considered:
- **oauthlib**: Lower-level, requires more boilerplate, lacks OIDC-specific helpers
- **python-social-auth**: Django-focused, heavyweight for FastAPI
- **requests-oauthlib**: Good for simple OAuth but not OIDC-aware

### Implementation Notes:
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
```

**Gotcha**: Redirect URIs must be registered with each provider and match exactly (including http vs https)

---

## 2. JWT Library

### Decision: **PyJWT** (via `pyjwt[crypto]`)

### Rationale:
- Industry standard, used by millions of applications
- Simple API for encoding/decoding tokens
- Supports HS256 (HMAC), RS256 (RSA), and other algorithms
- Excellent error messages for token validation failures
- Well-documented and actively maintained

### Alternatives Considered:
- **python-jose**: Initially considered but PyJWT is more actively maintained
- **authlib.jose**: Good but adds dependency weight when only JWT needed
- **josepy**: Focused on ACME protocol, overkill for simple JWT

### Implementation Notes:
```python
import jwt
from datetime import datetime, timedelta

def create_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

**Gotcha**: Always specify `algorithms=['HS256']` in decode() to prevent algorithm confusion attacks

---

## 3. OTP Storage (File-Based)

### Decision: **JSON files with time-based cleanup and atomic writes**

### Rationale:
- Aligns with project's file-based architecture
- Simple to implement and debug (human-readable)
- No external dependencies (Redis, database)
- Atomic writes prevent corruption during concurrent access
- Periodic cleanup prevents file bloat

### Structure:
```json
{
  "requests": {
    "user@example.com": {
      "code": "123456",
      "created_at": "2025-11-13T14:30:00Z",
      "expires_at": "2025-11-13T14:45:00Z",
      "attempts": 0
    }
  }
}
```

### Implementation Pattern:
```python
import json
import fcntl  # File locking for atomic writes
from pathlib import Path
from datetime import datetime, timedelta

OTP_FILE = Path("/app/data/auth/otp-requests.json")

def save_otp(email: str, code: str):
    OTP_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data
    data = {"requests": {}}
    if OTP_FILE.exists():
        with open(OTP_FILE, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for read
            data = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    # Add new OTP
    data["requests"][email] = {
        "code": code,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        "attempts": 0
    }
    
    # Atomic write with exclusive lock
    with open(OTP_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for write
        json.dump(data, f, indent=2)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def cleanup_expired_otps():
    """Run periodically to remove expired OTPs"""
    if not OTP_FILE.exists():
        return
    
    with open(OTP_FILE, 'r+') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        data = json.load(f)
        
        now = datetime.utcnow()
        data["requests"] = {
            email: otp 
            for email, otp in data["requests"].items()
            if datetime.fromisoformat(otp["expires_at"]) > now
        }
        
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Gotcha**: Use file locking (`fcntl.flock`) to prevent race conditions. Run cleanup task every 5 minutes via background scheduler.

### Alternatives Considered:
- **In-memory only (dict)**: Lost on restart, unacceptable for production
- **SQLite**: Adds database dependency, overkill for temporary data
- **Pickle files**: Not human-readable, harder to debug

---

## 4. Rate Limiting (File-Based)

### Decision: **Token bucket algorithm with JSON file persistence**

### Rationale:
- Flexible (can burst within limits)
- File-based aligns with architecture
- Efficient cleanup (only store timestamps within window)
- Simple to understand and debug

### Structure:
```json
{
  "limits": {
    "user@example.com": {
      "window_start": "2025-11-13T14:00:00Z",
      "requests": [
        "2025-11-13T14:05:00Z",
        "2025-11-13T14:10:00Z"
      ]
    }
  }
}
```

### Implementation Pattern:
```python
RATE_LIMIT_FILE = Path("/app/data/auth/rate-limits.json")
MAX_REQUESTS = 5
WINDOW_HOURS = 1

def check_rate_limit(email: str) -> bool:
    """Returns True if under limit, False if exceeded"""
    RATE_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {"limits": {}}
    if RATE_LIMIT_FILE.exists():
        with open(RATE_LIMIT_FILE, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=WINDOW_HOURS)
    
    # Get or initialize user's request history
    user_data = data["limits"].get(email, {"requests": []})
    
    # Filter to requests within window
    recent_requests = [
        req for req in user_data["requests"]
        if datetime.fromisoformat(req) > cutoff
    ]
    
    if len(recent_requests) >= MAX_REQUESTS:
        return False  # Rate limit exceeded
    
    # Add current request
    recent_requests.append(now.isoformat())
    data["limits"][email] = {"requests": recent_requests}
    
    # Save updated limits
    with open(RATE_LIMIT_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(data, f, indent=2)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    return True  # Within limit
```

**Gotcha**: Cleanup old entries during each check to prevent file bloat. Consider adding a background task for periodic full cleanup.

### Alternatives Considered:
- **Fixed window**: Simpler but allows burst at window boundaries (10 requests in 2 minutes if split across windows)
- **Leaky bucket**: More complex to implement correctly
- **Redis**: Not aligned with file-based architecture

---

## 5. Mailgun Integration

### Decision: **requests library** with Mailgun REST API

### Rationale:
- Zero additional dependencies (requests already in project)
- Simple HTTP POST to Mailgun API
- Full control over request/response handling
- Mailgun Python SDK is thin wrapper anyway
- Easier to mock for testing

### Implementation:
```python
import requests
import os

MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_BASE_URL = 'https://api.eu.mailgun.net/v3'

def send_otp_email(email: str, code: str):
    response = requests.post(
        f"{MAILGUN_BASE_URL}/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Vagrantfile Generator <noreply@{MAILGUN_DOMAIN}>",
            "to": [email],
            "subject": "Your login code",
            "text": f"Your verification code is: {code}\\n\\nThis code expires in 15 minutes.",
            "html": f"<p>Your verification code is: <strong>{code}</strong></p><p>This code expires in 15 minutes.</p>"
        }
    )
    
    if response.status_code != 200:
        raise EmailDeliveryError(f"Failed to send email: {response.text}")
    
    return response.json()
```

**Gotcha**: Always use EU base URL (`https://api.eu.mailgun.net`) for GDPR compliance. Store API key securely in environment variables, never in code.

### Alternatives Considered:
- **mailgun-python SDK**: Extra dependency, thin wrapper with minimal value
- **smtplib with Mailgun SMTP**: Works but REST API is faster and more reliable

---

## 6. Session Token Storage (Browser)

### Decision: **localStorage** for session tokens

### Rationale:
- Simple JavaScript API (`localStorage.setItem/getItem`)
- Persists across browser restarts (good for 24hr tokens)
- Works seamlessly with local development (no HTTPS required)
- Sufficient security for personal project use case
- Easy to implement and debug

### Implementation:
```javascript
// Store token after successful login
function saveToken(token) {
    localStorage.setItem('session_token', token);
}

// Retrieve token for API requests
function getToken() {
    return localStorage.getItem('session_token');
}

// Remove token on logout
function logout() {
    localStorage.removeItem('session_token');
    window.location.href = '/login';
}

// Add to all API requests
async function apiCall(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
    };
    
    const response = await fetch(endpoint, { ...options, headers });
    
    if (response.status === 401) {
        logout();  // Token expired or invalid
    }
    
    return response;
}
```

**Gotcha**: 
- localStorage is accessible to JavaScript (vulnerable to XSS)
- For personal project, acceptable risk given pragmatic security stance
- Tokens should still have short expiration (24hr) to limit exposure

### Alternatives Considered:
- **HttpOnly cookies**: More secure but requires HTTPS, complicates local development
- **sessionStorage**: Lost on browser restart, poor UX for 24hr tokens

---

## 7. FastAPI Authentication Middleware

### Decision: **Dependency injection with optional authentication**

### Rationale:
- Granular control (some endpoints require auth, others don't)
- Testable (can mock dependencies easily)
- Clear intent in endpoint signatures
- Deployment-mode aware (skip auth in self-hosted mode)
- Better than global middleware for mixed auth requirements

### Implementation Pattern:
```python
from fastapi import Depends, HTTPException, Request
from typing import Optional
import os

DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "self-hosted")

async def get_current_user(request: Request) -> Optional[dict]:
    """Dependency: Extract user from token (optional in self-hosted mode)"""
    
    if DEPLOYMENT_MODE == "self-hosted":
        return None  # No auth required
    
    # Public mode: require authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return {
            "user_id": payload["user_id"],
            "email": payload["email"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# Usage in endpoints
@app.get("/api/projects")
async def list_projects(user: Optional[dict] = Depends(get_current_user)):
    """Returns projects - behavior changes based on deployment mode"""
    
    if user:
        # Public mode: return user's projects only
        return load_user_projects(user["user_id"])
    else:
        # Self-hosted mode: return all projects
        return load_shared_projects()

@app.post("/api/projects")
async def create_project(
    project_data: dict,
    user: Optional[dict] = Depends(get_current_user)
):
    """Create project - user context injected by dependency"""
    if user:
        save_path = f"/data/users/{user['user_id']}/projects/"
    else:
        save_path = "/data/shared/projects/"
    
    return create_project_file(save_path, project_data)
```

**Gotcha**: Use `Optional[dict]` for user parameter to support both deployment modes. Always check `if user:` before accessing user-specific data.

### Alternatives Considered:
- **Global middleware**: Less flexible, harder to exempt specific endpoints (login page, health checks)
- **Decorator pattern**: Works but less Pythonic than FastAPI dependencies
- **Manual checks in each endpoint**: Repetitive, error-prone

---

## Security Checklist

Before implementation, ensure:

- [ ] JWT secret key is 32+ characters, randomly generated
- [ ] JWT tokens include `exp` (expiration) and `iat` (issued at) claims
- [ ] OTP codes are cryptographically random (use `secrets.token_urlsafe(6)`, not `random`)
- [ ] Rate limiting enforced before sending emails (prevent abuse)
- [ ] Email templates don't leak implementation details
- [ ] File permissions on `/data/auth/` are restrictive (600 or 700)
- [ ] CORS configured correctly (allow frontend origin only)
- [ ] Environment variables never committed to git (.gitignore)
- [ ] Error messages don't leak user enumeration info ("Invalid credentials" not "User not found")

---

## Environment Variables

```bash
# Required for public mode
DEPLOYMENT_MODE=public
MAILGUN_API_KEY=your-api-key
MAILGUN_DOMAIN=mg.yourdomain.com
JWT_SECRET_KEY=<32+ character random string>

# OIDC (optional, for P3 implementation)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITLAB_CLIENT_ID=...
GITLAB_CLIENT_SECRET=...
```

---

## Recommended File Structure

```
backend/data/
  auth/
    otp-requests.json      # Temporary OTP codes (cleanup every 5min)
    rate-limits.json       # Rate limit tracking (cleanup every 1hr)
  shared/
    [existing resources]
  users/
    {uuid-v4}/
      profile.json         # User metadata
      projects/
      boxes/
      plugins/
      provisioners/
      triggers/
```

---

## Next Steps

1. Implement email OTP flow (P1):
   - OTP generation and storage
   - Mailgun integration
   - Rate limiting
   - JWT token issuance

2. Implement session management:
   - localStorage token storage
   - Token validation dependency
   - Logout endpoint

3. Implement permission service:
   - User-specific directory paths
   - Permission checks in service layer
   - Resource merging (shared + user)

4. Add OIDC flows (P3):
   - Provider registration with authlib
   - Callback handlers
   - Token exchange

5. Frontend integration:
   - Login page
   - Auth client (token management)
   - Visual indicators for resources

---

**Research Complete**: All technical unknowns resolved. Ready to proceed to Phase 1 (design & contracts).
