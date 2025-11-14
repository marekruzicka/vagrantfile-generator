# Authentication Guide

This document describes the authentication system in Vagrantfile Generator, including setup, configuration, and usage.

## Table of Contents

- [Overview](#overview)
- [Deployment Modes](#deployment-modes)
- [Authentication Methods](#authentication-methods)
- [Email OTP Setup](#email-otp-setup)
- [OIDC/OAuth Setup](#oidcoauth-setup)
- [Security Features](#security-features)
- [Data Isolation](#data-isolation)
- [Troubleshooting](#troubleshooting)

## Overview

Vagrantfile Generator supports two deployment modes with different authentication requirements:

- **Self-Hosted Mode**: No authentication, single-user, local development
- **Public Mode**: Full authentication, multi-user, production deployments

## Deployment Modes

### Self-Hosted Mode (Default)

```bash
DEPLOYMENT_MODE=self-hosted  # or omit (defaults to self-hosted)
```

**Characteristics:**
- No authentication required
- All API endpoints are publicly accessible
- All resources are stored in `/data/shared/`
- Suitable for local development or single-user environments
- ⚠️ **Do not expose to the internet without additional security measures**

### Public Mode

```bash
DEPLOYMENT_MODE=public
```

**Characteristics:**
- Authentication required for all endpoints (except login/signup)
- User-specific data isolation
- Session management with JWT tokens
- Email OTP and/or OAuth authentication
- Suitable for production, multi-user deployments

## Authentication Methods

Public mode supports multiple authentication methods. At least one must be configured:

### 1. Email OTP (One-Time Password)

Users receive a 6-digit code via email to authenticate.

**Flow:**
1. User enters email address
2. Backend generates 6-digit OTP
3. Email sent via Mailgun
4. User enters OTP code
5. Backend verifies code and issues JWT token

**Configuration:**
```bash
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com

# Optional customization
OTP_LENGTH=6                    # Default: 6
OTP_EXPIRATION_MINUTES=15       # Default: 15
OTP_MAX_ATTEMPTS=3              # Default: 3
```

### 2. Google OAuth (OpenID Connect)

Users authenticate using their Google account.

**Configuration:**
```bash
OIDC_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
```

**Setup Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://your-domain.com/api/auth/callback/google`
6. Copy Client ID and Client Secret to environment variables

### 3. GitHub OAuth

Users authenticate using their GitHub account.

**Configuration:**
```bash
OIDC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
OIDC_GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Setup Steps:**
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Set Authorization callback URL: `https://your-domain.com/api/auth/callback/github`
4. Copy Client ID and Client Secret to environment variables

### 4. GitLab OAuth

Users authenticate using their GitLab account (supports self-hosted GitLab).

**Configuration:**
```bash
OIDC_GITLAB_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_URL=https://gitlab.com  # Optional, defaults to gitlab.com
```

**Setup Steps:**
1. Go to GitLab Settings → Applications
2. Create new application
3. Set Redirect URI: `https://your-domain.com/api/auth/callback/gitlab`
4. Select scopes: `read_user`
5. Copy Application ID (Client ID) and Secret to environment variables

## Email OTP Setup

### Mailgun Configuration

1. **Sign up for Mailgun**: https://www.mailgun.com/
2. **Verify your domain** or use Mailgun's sandbox domain (for testing)
3. **Get API credentials**:
   - Navigate to Settings → API Keys
   - Copy your Private API key
4. **Configure environment variables**:
   ```bash
   MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxx
   MAILGUN_DOMAIN=mg.yourdomain.com  # or sandbox domain
   MAILGUN_FROM_EMAIL=noreply@yourdomain.com
   ```

### Alternative Email Providers

Currently, Vagrantfile Generator supports Mailgun exclusively. To use other providers:

1. Implement a new email service in `backend/src/services/email_service.py`
2. Update the service to support your provider's API
3. Add required environment variables
4. Submit a pull request! 🎉

## OIDC/OAuth Setup

### Base URL Configuration

OIDC/OAuth requires proper URL configuration for callbacks:

```bash
BASE_URL=https://your-domain.com        # Backend URL
FRONTEND_URL=https://your-domain.com    # Frontend URL
```

**Important Notes:**
- URLs must match exactly (including protocol: http/https)
- No trailing slashes
- Must be accessible from user browsers (public DNS or localhost for development)

### Development Setup

For local development:

```bash
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8080

# Configure OAuth providers with localhost callback URLs:
# http://localhost:8000/api/auth/callback/{provider}
```

### Production Setup

For production deployments:

```bash
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Configure OAuth providers with production callback URLs:
# https://api.yourdomain.com/api/auth/callback/{provider}
```

## Security Features

### Rate Limiting

Email OTP requests are rate-limited using a token bucket algorithm:

```bash
OTP_RATE_LIMIT_MAX_REQUESTS=5     # Default: 5 requests
OTP_RATE_LIMIT_WINDOW_HOURS=1     # Default: 1 hour window
```

**Behavior:**
- Each email address has 5 OTP requests per hour
- Exceeded limit returns HTTP 429 (Too Many Requests)
- Limit resets after 1 hour from first request

### Session Management

JWT tokens are used for session management:

```bash
JWT_SECRET_KEY=<your-secret-key>   # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256                # Default: HS256
JWT_EXPIRATION_HOURS=24            # Default: 24 hours
```

**JWT Token Structure:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "auth_provider": "email|google|github|gitlab",
  "iat": 1234567890,
  "exp": 1234654290
}
```

**Security Best Practices:**
- Use a strong, random JWT secret (minimum 32 bytes)
- Never commit JWT_SECRET_KEY to version control
- Use environment variables or secret management systems
- Rotate JWT secret periodically in production

### Password Security

Vagrantfile Generator uses **passwordless authentication**:
- ✅ No passwords to store or hash
- ✅ No password reset flows needed
- ✅ Reduced attack surface
- ✅ Better user experience

## Data Isolation

### Storage Structure

```
/data/
  ├── shared/              # Read-only resources for all users
  │   ├── boxes/
  │   ├── plugins/
  │   ├── provisioners/
  │   └── triggers/
  ├── users/               # User-specific resources
  │   ├── {user-id-1}/
  │   │   ├── boxes/
  │   │   ├── plugins/
  │   │   ├── projects/
  │   │   ├── provisioners/
  │   │   └── triggers/
  │   └── {user-id-2}/
  │       └── ...
  └── auth/                # Authentication data
      ├── otp_*.json       # OTP codes (ephemeral)
      └── ratelimit_*.json # Rate limit tracking
```

### Resource Ownership

Each resource has:
- `is_shared`: Boolean flag (true for shared resources)
- `owner_id`: User ID (null for shared resources)

**Permission Rules:**
- ✅ All users can view shared resources
- ✅ Users can view their own resources
- ✅ Users can edit/delete only their own resources
- ❌ Shared resources are read-only for all users
- ❌ Users cannot edit other users' resources

### UI Indicators

- Shared resources display a "Shared" badge
- Tooltips explain why resources are read-only
- Visual distinction (grayed edit buttons for shared resources)

## Troubleshooting

### Email OTP Not Working

**Problem:** Users don't receive OTP emails

**Solutions:**
1. Check Mailgun configuration:
   ```bash
   # Verify environment variables are set
   echo $MAILGUN_API_KEY
   echo $MAILGUN_DOMAIN
   ```

2. Check Mailgun dashboard for delivery logs
3. Verify email address is not in Mailgun's suppression list
4. Check spam folder
5. Review backend logs for Mailgun API errors:
   ```bash
   docker compose logs backend | grep -i mailgun
   ```

### OIDC Login Not Working

**Problem:** OAuth redirect fails or returns errors

**Solutions:**
1. Verify callback URLs match exactly in provider settings:
   ```
   Expected: https://your-domain.com/api/auth/callback/{provider}
   Check: OAuth provider dashboard → Redirect URIs
   ```

2. Check environment variables:
   ```bash
   echo $BASE_URL
   echo $FRONTEND_URL
   echo $OIDC_GOOGLE_CLIENT_ID  # or GITHUB/GITLAB
   ```

3. Review backend logs for OIDC errors:
   ```bash
   docker compose logs backend | grep -i oidc
   ```

4. Common errors:
   - **redirect_uri_mismatch**: Callback URL doesn't match OAuth app settings
   - **invalid_client**: Client ID or Secret is incorrect
   - **access_denied**: User denied permission or app is not approved

### Rate Limit Issues

**Problem:** Users getting 429 errors too frequently

**Solutions:**
1. Increase rate limit:
   ```bash
   OTP_RATE_LIMIT_MAX_REQUESTS=10  # Increase from 5 to 10
   ```

2. Adjust time window:
   ```bash
   OTP_RATE_LIMIT_WINDOW_HOURS=2   # Increase from 1 to 2 hours
   ```

3. Clear rate limit manually (development only):
   ```bash
   rm backend/data/auth/ratelimit_*.json
   ```

### Session Expiration

**Problem:** Users logged out unexpectedly

**Solutions:**
1. Increase JWT expiration:
   ```bash
   JWT_EXPIRATION_HOURS=48  # Increase from 24 to 48 hours
   ```

2. Check system time on server (JWT uses timestamps)
3. Verify JWT_SECRET_KEY hasn't changed (invalidates all existing tokens)

### Debugging Tools

**Check deployment mode:**
```bash
curl http://localhost:8000/api/config/deployment
```

**Verify authentication (should return 401 in public mode):**
```bash
curl http://localhost:8000/api/projects
```

**Check authentication status:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/auth/me
```

**View backend logs:**
```bash
docker compose logs -f backend
```

**Enable debug logging:**
```bash
# In compose file, add to backend environment:
LOG_LEVEL=DEBUG
```

## API Reference

### Authentication Endpoints

#### Request OTP
```http
POST /api/auth/otp/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Response:
```json
{
  "message": "OTP sent to user@example.com",
  "expires_in": 900
}
```

#### Verify OTP
```http
POST /api/auth/otp/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "auth_provider": "email"
  }
}
```

#### OIDC Login
```http
GET /api/auth/oidc/{provider}
```

Redirects to OAuth provider for authentication.

#### OIDC Callback
```http
GET /api/auth/callback/{provider}?code=xxx&state=xxx
```

Handles OAuth callback, creates/updates user, returns JWT token in redirect.

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer YOUR_TOKEN
```

Response:
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "auth_provider": "google",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z"
}
```

## Migration Guide

### From Self-Hosted to Public Mode

1. **Backup data**:
   ```bash
   cp -r backend/data backend/data.backup
   ```

2. **Create shared resources directory**:
   ```bash
   mkdir -p backend/data/shared/{boxes,plugins,provisioners,triggers}
   ```

3. **Move existing resources to shared** (optional):
   ```bash
   cp backend/data/boxes/*.json backend/data/shared/boxes/
   cp backend/data/plugins/*.json backend/data/shared/plugins/
   # etc...
   ```

4. **Configure authentication** (see sections above)

5. **Update environment variables**:
   ```bash
   DEPLOYMENT_MODE=public
   JWT_SECRET_KEY=<generated-secret>
   # Add other required variables
   ```

6. **Restart application**:
   ```bash
   docker compose down
   docker compose up -d
   ```

7. **Verify deployment mode**:
   ```bash
   curl http://localhost:8000/api/config/deployment
   ```

### From Public to Self-Hosted Mode

1. **Update environment variable**:
   ```bash
   DEPLOYMENT_MODE=self-hosted
   ```

2. **Restart application**:
   ```bash
   docker compose down
   docker compose up -d
   ```

**Note:** User-specific data in `/data/users/` will not be accessible in self-hosted mode. Only shared resources are used.

## Support

For issues, questions, or feature requests:
- **GitHub Issues**: https://github.com/yourusername/vagrantfile-generator/issues
- **Documentation**: See other guides in `/docs/` directory
- **Logs**: Always check `docker compose logs backend` for detailed error messages
