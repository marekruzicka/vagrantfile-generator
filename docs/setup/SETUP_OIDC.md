# OIDC/OAuth Setup Guide

Complete guide for setting up OAuth authentication with Google, GitHub, and GitLab.

## Overview

Vagrantfile Generator supports three OAuth providers:
- **Google** (OpenID Connect)
- **GitHub** (OAuth 2.0)
- **GitLab** (OAuth 2.0, supports self-hosted)

You can enable one, some, or all providers simultaneously.

## Prerequisites

- Docker/Podman installed
- Public domain or localhost for development
- Access to provider developer consoles

## Common Setup Steps

### 1. Configure Base URLs

Set these environment variables for all OIDC providers:

```bash
# Backend URL (where callbacks will be handled)
BASE_URL=http://localhost:8000              # Development
BASE_URL=https://api.yourdomain.com         # Production

# Frontend URL (where users will be redirected after login)
FRONTEND_URL=http://localhost:8080          # Development
FRONTEND_URL=https://yourdomain.com         # Production
```

### 2. Generate JWT Secret

```bash
openssl rand -hex 32
```

### 3. Set Deployment Mode

```bash
DEPLOYMENT_MODE=public
JWT_SECRET_KEY=<generated-secret-from-step-2>
```

## Provider-Specific Setup

### Google OAuth (OpenID Connect)

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Enter project name (e.g., "Vagrantfile Generator")
4. Click **Create**

#### Step 2: Enable Google+ API

1. Navigate to **APIs & Services** → **Library**
2. Search for "Google+ API"
3. Click **Enable**

#### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (for public apps) or **Internal** (for G Suite)
   - App name: "Vagrantfile Generator"
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue**
   - Scopes: Add `openid`, `email`, `profile`
   - Test users: Add your email (for testing)
   - Click **Save and Continue**

4. Create OAuth client ID:
   - Application type: **Web application**
   - Name: "Vagrantfile Generator"
   - Authorized redirect URIs:
     - Development: `http://localhost:8000/api/auth/callback/google`
     - Production: `https://api.yourdomain.com/api/auth/callback/google`
   - Click **Create**

5. Copy **Client ID** and **Client Secret**

#### Step 4: Configure Environment

```bash
OIDC_GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxx
```

---

### GitHub OAuth

#### Step 1: Create OAuth App

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in details:
   - **Application name**: Vagrantfile Generator
   - **Homepage URL**: 
     - Development: `http://localhost:8080`
     - Production: `https://yourdomain.com`
   - **Authorization callback URL**:
     - Development: `http://localhost:8000/api/auth/callback/github`
     - Production: `https://api.yourdomain.com/api/auth/callback/github`
   - Click **Register application**

#### Step 2: Generate Client Secret

1. Click **Generate a new client secret**
2. Copy the secret immediately (shown only once)
3. Copy the **Client ID** from the top

#### Step 3: Configure Environment

```bash
OIDC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
OIDC_GITHUB_CLIENT_SECRET=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### GitLab OAuth (gitlab.com)

#### Step 1: Create GitLab Application

1. Go to [GitLab Applications](https://gitlab.com/-/profile/applications)
2. Fill in details:
   - **Name**: Vagrantfile Generator
   - **Redirect URI**:
     - Development: `http://localhost:8000/api/auth/callback/gitlab`
     - Production: `https://api.yourdomain.com/api/auth/callback/gitlab`
   - **Confidential**: ✓ (checked)
   - **Scopes**: Select `read_user`
   - Click **Save application**

#### Step 2: Copy Credentials

1. Copy **Application ID** (this is your Client ID)
2. Copy **Secret**

#### Step 3: Configure Environment

```bash
OIDC_GITLAB_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_CLIENT_SECRET=gloas-xxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_URL=https://gitlab.com  # Optional, defaults to gitlab.com
```

---

### GitLab OAuth (Self-Hosted)

For self-hosted GitLab instances:

#### Step 1: Create Application in Self-Hosted GitLab

1. Go to your GitLab instance: `https://gitlab.yourcompany.com/-/profile/applications`
2. Follow same steps as gitlab.com
3. Use your self-hosted instance URLs for redirect URIs

#### Step 2: Configure Environment

```bash
OIDC_GITLAB_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_CLIENT_SECRET=gloas-xxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_URL=https://gitlab.yourcompany.com  # Your GitLab instance
```

## Complete Configuration Example

### Development (All Providers)

```bash
# Deployment
DEPLOYMENT_MODE=public
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Base URLs
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8080

# Google OAuth
OIDC_GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxx

# GitHub OAuth
OIDC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
OIDC_GITHUB_CLIENT_SECRET=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# GitLab OAuth
OIDC_GITLAB_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_CLIENT_SECRET=gloas-xxxxxxxxxxxxxxxxxxxxxxxx
OIDC_GITLAB_URL=https://gitlab.com
```

### Production (All Providers)

```bash
# Deployment
DEPLOYMENT_MODE=public
JWT_SECRET_KEY=<strong-random-secret>

# Base URLs
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Google OAuth
OIDC_GOOGLE_CLIENT_ID=<production-client-id>.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-<production-secret>

# GitHub OAuth
OIDC_GITHUB_CLIENT_ID=<production-client-id>
OIDC_GITHUB_CLIENT_SECRET=<production-secret>

# GitLab OAuth
OIDC_GITLAB_CLIENT_ID=<production-client-id>
OIDC_GITLAB_CLIENT_SECRET=<production-secret>
OIDC_GITLAB_URL=https://gitlab.com
```

## Testing

### Start Application

```bash
docker compose -f compose-dev.yml up -d
```

### Check Configuration

```bash
# View backend logs
docker compose logs backend | grep -i oidc

# Expected output for each configured provider:
# Google OAuth provider registered
# GitHub OAuth provider registered
# GitLab OAuth provider registered (https://gitlab.com)
```

### Test Each Provider

#### 1. Test via UI

1. Open http://localhost:8080
2. Click provider button (Google/GitHub/GitLab)
3. Complete OAuth flow on provider site
4. Verify redirect back to application
5. Check you're logged in (user profile visible)

#### 2. Test via API

**Initiate OAuth flow**:
```bash
# Google
curl -v http://localhost:8000/api/auth/oidc/google

# GitHub
curl -v http://localhost:8000/api/auth/oidc/github

# GitLab
curl -v http://localhost:8000/api/auth/oidc/gitlab
```

Expected: 302 redirect to provider's authorization URL

**Check user info after login**:
```bash
TOKEN="<token-from-url-after-login>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

Expected response:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "auth_provider": "google",  # or "github" or "gitlab"
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z"
}
```

## Troubleshooting

### Common Issues

#### redirect_uri_mismatch

**Problem**: OAuth provider shows "redirect_uri_mismatch" error

**Solution**: 
1. Check callback URL in provider settings exactly matches:
   ```
   http://localhost:8000/api/auth/callback/{provider}
   ```
2. No trailing slash
3. Correct protocol (http vs https)
4. Correct port number

#### invalid_client

**Problem**: "invalid_client" error during OAuth flow

**Solution**:
1. Verify Client ID is correct
2. Verify Client Secret is correct
3. Check for extra spaces in environment variables
4. Regenerate client secret if needed

#### Provider not configured

**Problem**: Backend logs show "Provider not configured" warning

**Solution**:
```bash
# Check environment variables are set
docker compose exec backend env | grep OIDC_GOOGLE
docker compose exec backend env | grep OIDC_GITHUB
docker compose exec backend env | grep OIDC_GITLAB

# Restart backend after adding variables
docker compose restart backend
```

#### Access denied

**Problem**: User sees "access denied" after authorizing

**Possible Causes**:
1. **Google**: App not approved, user not in test users list
2. **GitHub**: App suspended or user denied access
3. **GitLab**: Insufficient scopes selected

**Solution**: Review OAuth app settings and ensure required scopes are granted

### Testing Multiple Providers

Test user can authenticate with different providers:

```bash
# Test flow
1. Login with Google → Create user A
2. Logout
3. Login with GitHub → Create user B (different user)
4. Logout
5. Login with Google again → Login as user A (same user)
```

Each provider creates a separate user account based on email.

## Security Considerations

### Production Checklist

- [ ] Use HTTPS for all URLs (BASE_URL and FRONTEND_URL)
- [ ] Strong JWT secret (32+ bytes, randomly generated)
- [ ] Verify redirect URIs match exactly
- [ ] Review OAuth app permissions/scopes
- [ ] Enable OAuth app in production mode (not testing)
- [ ] Restrict OAuth app to specific domains if possible
- [ ] Monitor OAuth provider quotas and limits
- [ ] Keep client secrets secure (never commit to git)
- [ ] Rotate secrets periodically

### Privacy Considerations

Data collected from providers:
- **Email**: Required for user identification
- **Name**: Optional, for display purposes
- **Provider User ID**: Internal identifier from provider

No passwords are stored. User can revoke access via provider settings.

## Next Steps

- [Email OTP Setup](./SETUP_EMAIL_OTP.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Complete Authentication Docs](../AUTHENTICATION.md)
