# Authentication Guide

This document describes authentication setup and configuration for Vagrantfile Generator.

## Deployment Modes

### Self-Hosted Mode (Default)

```bash
DEPLOYMENT_MODE=self-hosted  # or omit (defaults to self-hosted)
```

- No authentication required
- All API endpoints are publicly accessible
- All resources stored in `/data/shared/`
- ⚠️ Do not expose to the internet without additional security measures

### Public Mode

```bash
DEPLOYMENT_MODE=public
```

- Authentication required for all endpoints (except login)
- User-specific data isolation
- Session management with JWT tokens
- Email OTP and/or OAuth authentication

## Authentication Methods

Public mode supports multiple methods. At least one must be configured:

### Email OTP

Users receive a 6-digit code via email (Mailgun). See [SETUP_EMAIL_OTP.md](./SETUP_EMAIL_OTP.md) for setup.

### OAuth Providers

- **Google** — [SETUP_OIDC.md](./SETUP_OIDC.md#google-oauth)
- **GitHub** — [SETUP_OIDC.md](./SETUP_OIDC.md#github-oauth)
- **GitLab** (including self-hosted) — [SETUP_OIDC.md](./SETUP_OIDC.md#gitlab-oauth)

## Required Environment Variables

### Public Mode

```bash
DEPLOYMENT_MODE=public
JWT_SECRET=<your-jwt-secret>                  # Generate with: openssl rand -hex 32
SESSION_COOKIE_SECRET=<your-cookie-secret>    # Generate with: openssl rand -hex 32
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### Email OTP (optional)

```bash
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
```

### OAuth (at least one required)

```bash
OIDC_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
OIDC_GITHUB_CLIENT_ID=Iv1.xxxxx
OIDC_GITHUB_CLIENT_SECRET=xxxxx
OIDC_GITLAB_CLIENT_ID=xxxxx
OIDC_GITLAB_CLIENT_SECRET=xxxxx
```

## Security

- **Rate limiting**: 5 OTP requests per hour per email address
- **Sessions**: JWT tokens expire after 24 hours by default
- **Passwordless**: No passwords stored — email OTP and OAuth only
- **Secrets**: Never commit JWT_SECRET or SESSION_COOKIE_SECRET to version control

## Data Isolation

In public mode, resources are stored per-user:

```
/data/
  shared/     # Read-only system resources (boxes, plugins, etc.)
  users/
    {user-id}/ # User's private resources
  auth/       # OTP codes and rate limit data
```

## Troubleshooting

### Email OTP not received

1. Check Mailgun configuration: `echo $MAILGUN_API_KEY`
2. Check Mailgun dashboard for delivery logs
3. Verify email is in Mailgun's authorized recipients (sandbox mode)
4. Check spam folder
5. Review backend logs: `docker compose logs backend | grep -i mailgun`

### OIDC login fails

1. Verify callback URLs match exactly in provider settings
2. Check environment variables are set correctly
3. Review backend logs: `docker compose logs backend | grep -i oidc`
4. Common errors: `redirect_uri_mismatch` (URL mismatch), `invalid_client` (wrong credentials)

### Rate limit (429 errors)

Increase limits if needed:
```bash
OTP_RATE_LIMIT_MAX_REQUESTS=10
OTP_RATE_LIMIT_WINDOW_HOURS=2
```

### Session expires too quickly

```bash
JWT_EXPIRATION_HOURS=48  # Increase from default 24 hours
```

## Migration: Self-Hosted → Public

1. **Backup**: `cp -r backend/data backend/data.backup`
2. **Move resources to shared** (optional):
   ```bash
   mkdir -p backend/data/shared/{boxes,plugins,provisioners,triggers}
   cp backend/data/boxes/*.json backend/data/shared/boxes/
   ```
3. **Configure auth** as described above
4. **Set** `DEPLOYMENT_MODE=public`
5. **Restart**: `docker compose down && docker compose up -d`
