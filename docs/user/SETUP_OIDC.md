# OIDC/OAuth Setup

Setup guides for Google, GitHub, and GitLab OAuth authentication.

## Prerequisites

- Public domain or localhost (for development)
- Access to the provider's developer console

## Common Configuration

```bash
DEPLOYMENT_MODE=public
JWT_SECRET=<generated-secret>               # openssl rand -hex 32
SESSION_COOKIE_SECRET=<generated-secret>    # openssl rand -hex 32
BASE_URL=http://localhost:8000              # or https://api.yourdomain.com
FRONTEND_URL=http://localhost:8080          # or https://yourdomain.com
```

---

## Google OAuth

### 1. Create Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g., "Vagrantfile Generator")
3. Enable **Google+ API** in APIs & Services → Library

### 2. Create OAuth Credentials

1. Go to **APIs & Services → Credentials** → Create Credentials → OAuth client ID
2. Configure OAuth consent screen (User Type: External, add `openid`, `email`, `profile` scopes)
3. Create Web application credentials with redirect URI:
   - Development: `http://localhost:8000/api/auth/callback/google`
   - Production: `https://api.yourdomain.com/api/auth/callback/google`

### 3. Configure

```bash
OIDC_GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxx
```

---

## GitHub OAuth

### 1. Create OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers) → OAuth Apps → New OAuth App
2. Set callback URL:
   - Development: `http://localhost:8000/api/auth/callback/github`
   - Production: `https://api.yourdomain.com/api/auth/callback/github`

### 2. Configure

```bash
OIDC_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
OIDC_GITHUB_CLIENT_SECRET=<generated-secret>
```

---

## GitLab OAuth

### 1. Create Application

1. Go to [GitLab Applications](https://gitlab.com/-/profile/applications) (or your self-hosted instance)
2. Set redirect URI:
   - Development: `http://localhost:8000/api/auth/callback/gitlab`
   - Production: `https://api.yourdomain.com/api/auth/callback/gitlab`
3. Select scope: `read_user`

### 2. Configure

```bash
OIDC_GITLAB_CLIENT_ID=<application-id>
OIDC_GITLAB_CLIENT_SECRET=<secret>
OIDC_GITLAB_URL=https://gitlab.com  # Optional, for self-hosted instances
```

---

## Verification

1. Start the app: `docker compose up -d`
2. Check backend logs: `docker compose logs backend | grep -i oidc`
   - Expected: "Google OAuth provider registered", etc.
3. Open http://localhost:8080 and click the provider button
4. Complete OAuth flow on the provider's site
5. Verify you're redirected back and logged in

## Troubleshooting

### redirect_uri_mismatch

The callback URL in provider settings must exactly match `{BASE_URL}/api/auth/callback/{provider}` — no trailing slash, correct protocol and port.

### invalid_client

Verify Client ID and Secret are correct with no extra spaces. Regenerate the secret if needed.

### Provider not configured

```bash
docker compose exec backend env | grep OIDC_
docker compose restart backend  # after adding variables
```

## Security Checklist

- [ ] Use HTTPS for all URLs in production
- [ ] Strong, randomly generated JWT and cookie secrets
- [ ] Verify redirect URIs match exactly
- [ ] Keep client secrets secure — never commit to git
- [ ] Rotate secrets periodically
- [ ] Restrict OAuth app to specific domains where possible
