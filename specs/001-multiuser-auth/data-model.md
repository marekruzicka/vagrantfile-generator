# Data Model: Multi-User Authentication

**Feature**: 001-multiuser-auth  
**Date**: 2025-11-13  
**Purpose**: Define all entities, their attributes, relationships, and validation rules

---

## Entity Overview

This feature introduces 4 new entities to support multi-user authentication and 1 updated entity for deployment mode awareness.

| Entity | Storage Location | Lifecycle | Purpose |
|--------|------------------|-----------|---------|
| UserProfile | `/data/users/{user-id}/profile.json` | Permanent | User identity and metadata |
| OTPRequest | `/data/auth/otp-requests.json` | Temporary (15 min) | Email OTP verification |
| RateLimitRecord | `/data/auth/rate-limits.json` | Temporary (1 hr rolling) | Prevent OTP abuse |
| SessionToken | JWT (browser storage) | Temporary (24 hr) | Authenticated session |
| DeploymentConfig | Environment variables | Static | Deployment mode settings |

---

## 1. UserProfile

### Purpose
Represents an authenticated user in public deployment mode. Created on first successful authentication (OTP or OIDC).

### Storage
- **File**: `/data/users/{user-id}/profile.json`
- **Format**: JSON
- **Permissions**: Read-write by application only

### Schema

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "auth_provider": "email",
  "created_at": "2025-11-13T14:30:00Z",
  "last_login": "2025-11-13T15:45:00Z"
}
```

### Attributes

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `user_id` | string (UUID v4) | Yes | Must be valid UUID v4 format | Unique user identifier, randomly generated |
| `email` | string | Yes | Valid email format, max 255 chars | User's email address (used for login) |
| `name` | string | No | Max 255 chars | Display name (from OIDC or email prefix) |
| `auth_provider` | string | Yes | One of: `email`, `google`, `github`, `gitlab` | How user authenticated |
| `created_at` | string (ISO 8601) | Yes | Valid ISO 8601 datetime | When user first authenticated |
| `last_login` | string (ISO 8601) | Yes | Valid ISO 8601 datetime | Most recent login timestamp |

### Validation Rules

1. **user_id**: Must be UUID v4 format (e.g., `550e8400-e29b-41d4-a716-446655440000`)
2. **email**: Must pass RFC 5322 email validation, case-insensitive storage (lowercase)
3. **auth_provider**: Must be one of the supported values
4. **Timestamps**: Must be UTC, ISO 8601 format with Z suffix

### Relationships

- **1:N** with Projects (one user has many projects in `/data/users/{user-id}/projects/`)
- **1:N** with custom Boxes, Plugins, Provisioners, Triggers

### State Transitions

```
[No Profile] 
    ↓ (First successful authentication)
[Profile Created] 
    ↓ (Subsequent logins)
[Profile Updated] (last_login timestamp)
```

### Indexes / Lookups

- Primary lookup: By `user_id` (directory path)
- Secondary lookup: By `email` (requires scanning `/data/users/*/profile.json` - acceptable for small scale)

---

## 2. OTPRequest

### Purpose
Temporary record of an email OTP code for verification. Expires after 15 minutes.

### Storage
- **File**: `/data/auth/otp-requests.json`
- **Format**: JSON (dictionary keyed by email)
- **Permissions**: Read-write by application only
- **Cleanup**: Every 5 minutes via background task

### Schema

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

### Attributes

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `code` | string (6 digits) | Yes | Exactly 6 numeric digits | OTP code sent via email |
| `created_at` | string (ISO 8601) | Yes | Valid ISO 8601 datetime | When OTP was generated |
| `expires_at` | string (ISO 8601) | Yes | Valid ISO 8601 datetime, always created_at + 15 min | Expiration timestamp |
| `attempts` | integer | Yes | 0-5 | Number of failed verification attempts |

### Validation Rules

1. **code**: Must be exactly 6 digits, generated using `secrets` module (cryptographically secure)
2. **expiration**: Always 15 minutes from creation (`created_at + timedelta(minutes=15)`)
3. **attempts**: Max 5 attempts per OTP, then require new code
4. **Cleanup**: Delete entry when `expires_at < now()`

### Relationships

- **1:1** with email address (one active OTP per email at a time)

### State Transitions

```
[No OTP]
    ↓ (User requests code)
[OTP Generated & Sent]
    ↓ (User enters code)
[OTP Verified] → Delete entry → Create Session
    OR
[OTP Expired] → Delete entry
    OR
[Too Many Attempts] → Delete entry → Require new request
```

---

## 3. RateLimitRecord

### Purpose
Track OTP request timestamps per email to enforce rate limiting (5 requests per hour).

### Storage
- **File**: `/data/auth/rate-limits.json`
- **Format**: JSON (dictionary keyed by email)
- **Permissions**: Read-write by application only
- **Cleanup**: Remove entries older than 1 hour during each check

### Schema

```json
{
  "limits": {
    "user@example.com": {
      "requests": [
        "2025-11-13T14:05:00Z",
        "2025-11-13T14:10:00Z",
        "2025-11-13T14:15:00Z"
      ]
    }
  }
}
```

### Attributes

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `requests` | array of strings (ISO 8601) | Yes | Each timestamp must be valid ISO 8601 | Timestamps of OTP requests within last hour |

### Validation Rules

1. **Window**: Only store requests from last 1 hour (`now() - timedelta(hours=1)`)
2. **Max Requests**: If `len(requests) >= 5`, reject new request
3. **Cleanup**: Filter out timestamps older than 1 hour on each check

### Relationships

- **1:1** with email address (one rate limit record per email)

### State Transitions

```
[No Record]
    ↓ (First OTP request)
[Record Created] (1 timestamp)
    ↓ (Subsequent requests)
[Record Updated] (add timestamp, prune old ones)
    ↓ (If 5 requests in last hour)
[Rate Limited] → Reject request with 429 error
    ↓ (After 1 hour)
[Oldest timestamp expires] → Allow new requests
```

---

## 4. SessionToken (JWT)

### Purpose
Stateless authentication token issued after successful OTP or OIDC login. Valid for 24 hours.

### Storage
- **Client-side**: Browser localStorage (`session_token` key)
- **Transmission**: HTTP Authorization header (`Bearer {token}`)
- **Format**: JWT (JSON Web Token)

### JWT Payload Schema

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "auth_provider": "email",
  "iat": 1699887000,
  "exp": 1699973400
}
```

### Claims

| Claim | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `user_id` | string (UUID v4) | Yes | Must be valid UUID v4 | User identifier |
| `email` | string | Yes | Valid email format | User's email address |
| `name` | string | No | Max 255 chars | Display name |
| `auth_provider` | string | Yes | One of: `email`, `google`, `github`, `gitlab` | Authentication method used |
| `iat` | integer (Unix timestamp) | Yes | Must be <= current time | Issued at timestamp |
| `exp` | integer (Unix timestamp) | Yes | Must be > current time, always iat + 24 hours | Expiration timestamp |

### Validation Rules

1. **Signature**: Must be signed with HS256 algorithm using `JWT_SECRET_KEY`
2. **Expiration**: Reject if `exp < now()` (automatically handled by JWT library)
3. **Algorithm**: Only accept HS256 (prevent algorithm confusion attacks)
4. **Claims**: Must include all required claims

### Relationships

- **N:1** with UserProfile (many tokens can exist for one user across devices/browsers)

### State Transitions

```
[No Token]
    ↓ (Successful OTP or OIDC verification)
[Token Issued] (stored in localStorage)
    ↓ (Every API request)
[Token Validated] → Allow access
    OR
[Token Expired] → Return 401, redirect to login
    OR
[User Logs Out] → Remove from localStorage
```

---

## 5. DeploymentConfig

### Purpose
Configuration determining authentication requirements and data access patterns.

### Storage
- **Environment Variables**: Set via Docker Compose, Podman Compose, or shell
- **Format**: Key-value pairs

### Schema

```bash
DEPLOYMENT_MODE=self-hosted  # or "public"
MAILGUN_API_KEY=key-abc123
MAILGUN_DOMAIN=mg.example.com
JWT_SECRET_KEY=random-32-char-string
```

### Attributes

| Variable | Type | Required | Validation | Description |
|----------|------|----------|------------|-------------|
| `DEPLOYMENT_MODE` | string | No (default: `self-hosted`) | One of: `self-hosted`, `public` | Determines auth requirements |
| `MAILGUN_API_KEY` | string | Yes (public mode) | Non-empty | Mailgun API key for sending emails |
| `MAILGUN_DOMAIN` | string | Yes (public mode) | Valid domain format | Verified Mailgun sending domain |
| `JWT_SECRET_KEY` | string | Yes (public mode) | Min 32 characters | Secret for signing JWT tokens |
| `GOOGLE_CLIENT_ID` | string | No | Non-empty | Google OIDC client ID (P3) |
| `GOOGLE_CLIENT_SECRET` | string | No | Non-empty | Google OIDC client secret (P3) |
| `GITHUB_CLIENT_ID` | string | No | Non-empty | GitHub OAuth app ID (P3) |
| `GITHUB_CLIENT_SECRET` | string | No | Non-empty | GitHub OAuth app secret (P3) |
| `GITLAB_CLIENT_ID` | string | No | Non-empty | GitLab OAuth app ID (P3) |
| `GITLAB_CLIENT_SECRET` | string | No | Non-empty | GitLab OAuth app secret (P3) |

### Validation Rules

1. **DEPLOYMENT_MODE**: Must be exactly `self-hosted` or `public` (case-sensitive)
2. **JWT_SECRET_KEY**: Minimum 32 characters, should be cryptographically random
3. **Email/domain**: Must be valid email/domain format
4. **Secrets**: Never log or expose in error messages

### Behavior Impact

| Mode | Authentication | Data Access | Projects Location |
|------|----------------|-------------|-------------------|
| `self-hosted` | None required | Full read-write to `/data/shared/` | `/data/shared/projects/` |
| `public` | Required (OTP or OIDC) | User: RW `/data/users/{id}/`, RO `/data/shared/` | `/data/users/{user-id}/projects/` |

---

## Data Flow Diagrams

### OTP Authentication Flow

```
User                    Backend                      Mailgun             Storage
  |                        |                            |                    |
  |---[1] Request OTP----->|                            |                    |
  |                        |---[2] Check rate limit--->|                    |
  |                        |<--[3] OK (< 5 requests)---|                    |
  |                        |---[4] Generate OTP------->|                    |
  |                        |---[5] Save OTP------------>|------[6] Write--->|
  |                        |---[7] Send email---------->|                    |
  |<--[8] "Code sent"------|                            |<--[9] Delivered---|
  |                        |                            |                    |
  |--[10] Enter code------>|                            |                    |
  |                        |---[11] Load OTP----------->|<-----[12] Read----|
  |                        |<--[13] Validate OTP--------|                    |
  |                        |---[14] Create user-------->|------[15] Write--->|
  |                        |---[16] Issue JWT---------->|                    |
  |<--[17] Return token----|                            |                    |
```

### Resource Access Flow (Public Mode)

```
User (authenticated)        Backend                    Storage
  |                           |                            |
  |--[1] List plugins-------->|                            |
  |                           |--[2] Load shared---------->|<--[3] /data/shared/plugins/
  |                           |--[4] Load user------------>|<--[5] /data/users/{id}/plugins/
  |                           |--[6] Merge + mark shared-->|
  |<--[7] Combined list-------|                            |
  |                           |                            |
  |--[8] Create plugin------->|                            |
  |                           |--[9] Check permission----->|
  |                           |--[10] Save to user dir---->|---[11] /data/users/{id}/plugins/
  |<--[12] Created------------|                            |
  |                           |                            |
  |--[13] Delete shared------>|                            |
  |<--[14] 403 Forbidden------|                            |
```

---

## Validation Summary

### Pre-Save Validation (Backend)

1. **UserProfile**: Email format, UUID v4 for user_id, valid auth_provider
2. **OTPRequest**: 6-digit code, 15-minute expiration, max 5 attempts
3. **RateLimitRecord**: Prune timestamps > 1 hour old, enforce 5 request limit
4. **SessionToken**: Valid JWT signature, not expired, required claims present
5. **DeploymentConfig**: Valid mode string, required secrets in public mode

### Post-Load Validation

1. **Expired OTPs**: Remove from `/data/auth/otp-requests.json` if `expires_at < now()`
2. **Expired Rate Limits**: Remove timestamps > 1 hour from `/data/auth/rate-limits.json`
3. **Expired Tokens**: Reject with 401 if `exp < now()`

---

## Notes on Data Organization

- **Shared resources** (`/data/shared/`) are read-only system resources in public mode, created by manually copying JSON files to the directory before deployment
- **User resources** (`/data/users/{user-id}/`) are personal to each authenticated user in public mode
- **No admin users**: All authenticated users have equal privileges (CRUD on own resources, read-only on shared)
- **Shared resource preparation**: Developer manually moves desired boxes/plugins/provisioners/triggers to `/data/shared/` before deploying in public mode

## Migration Considerations

### From Current State (No Auth)

1. Move `/data/boxes/`, `/data/plugins/`, `/data/provisioners/`, `/data/triggers/`, `/data/projects/` to `/data/shared/`
2. Create `/data/auth/` directory
3. Create empty `/data/auth/otp-requests.json` with `{"requests": {}}`
4. Create empty `/data/auth/rate-limits.json` with `{"limits": {}}`
5. No user migration needed (users created on first login in public mode)

### Backward Compatibility

- Self-hosted mode accesses `/data/shared/` directly (same behavior as before migration)
- No breaking changes for existing deployments using default (self-hosted) mode

---

**Data Model Complete**: All entities defined with schemas, validation rules, and relationships. Ready for API contract generation.
