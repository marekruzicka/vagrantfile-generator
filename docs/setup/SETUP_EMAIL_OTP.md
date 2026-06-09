# Email OTP Setup and Testing Guide

This guide covers setting up and testing Email OTP authentication using Mailgun.

## Prerequisites

- Mailgun account (free tier available)
- Docker/Podman installed
- Access to backend environment variables

## Setup Steps

### 1. Create Mailgun Account

1. Go to https://www.mailgun.com/
2. Sign up for a free account
3. Verify your email address

### 2. Get Mailgun Credentials

#### Option A: Production (Custom Domain)

1. Add and verify your domain in Mailgun dashboard
2. Configure DNS records (SPF, DKIM, CNAME)
3. Navigate to **Settings → API Keys**
4. Copy your **Private API Key**
5. Note your **Domain** (e.g., `mg.yourdomain.com`)

#### Option B: Development (Sandbox Domain)

1. Go to **Sending → Domains**
2. Use the sandbox domain provided (e.g., `sandboxXXXXXXXX.mailgun.org`)
3. Add authorized recipients (emails that can receive test messages)
4. Navigate to **Settings → API Keys**
5. Copy your **Private API Key**

### 3. Configure Environment Variables

Add to your `.env` file or `compose-dev.yml`:

```bash
# Deployment Mode
DEPLOYMENT_MODE=public

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32

# Mailgun Configuration
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=sandboxXXXXXXXX.mailgun.org  # or mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@sandboxXXXXXXXX.mailgun.org

# Backend URLs
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8080

# Optional: OTP Customization
OTP_LENGTH=6
OTP_EXPIRATION_MINUTES=15
OTP_MAX_ATTEMPTS=3
OTP_RATE_LIMIT_MAX_REQUESTS=5
OTP_RATE_LIMIT_WINDOW_HOURS=1

# Optional: Test User (for development/testing)
# When enabled, allows login with a static OTP code
TEST_USER_ENABLED=false
TEST_USER_EMAIL=test@example.com
TEST_USER_OTP=123456
```

### Test User (Development Only)

For development and testing purposes, you can enable a built-in test user that:

- Uses a static OTP code (default: `123456`)
- Bypasses email sending (no Mailgun required)
- Bypasses rate limiting

**Enable Test User:**

```bash
# Add to .env or backend environment
TEST_USER_ENABLED=true
TEST_USER_EMAIL=test@example.com  # Default
TEST_USER_OTP=123456              # Default
```

**Using Test User:**

1. Navigate to login page
2. Enter `test@example.com` (or your configured test email)
3. Click "Send Login Code" - no email will be sent
4. Enter `123456` (or your configured test OTP)
5. Click "Verify Code"

⚠️ **Security Warning**: Never enable test user in production! The static OTP provides no security.

### 4. Generate JWT Secret

```bash
openssl rand -hex 32
```

Copy the output and use it as your `JWT_SECRET_KEY`.

### 5. Start the Application

```bash
# Using podman-compose
podman-compose -f compose-dev.yml up -d

# Or using docker
docker compose -f compose-dev.yml up -d
```

### 6. Verify Configuration

Check backend logs to confirm Mailgun is configured:

```bash
docker compose logs backend | grep -i mailgun
```

Expected output:

```
Mailgun configuration detected - Email OTP authentication enabled
```

## Testing

### Test 1: Request OTP

1. **Open Browser**: Navigate to http://localhost:8080
2. **Click Login/Signup**
3. **Enter Email**: Use an authorized recipient email (if using sandbox)
4. **Click "Send Code"**

**Expected Result**:

- Success message: "Code sent to your email"
- Email received within 1-2 minutes

### Test 2: Verify OTP

1. **Check Email**: Find the 6-digit code
2. **Enter Code**: Type the code in the verification field
3. **Click "Verify"**

**Expected Result**:

- Redirect to main application
- JWT token stored in localStorage
- User profile visible in UI

### Test 3: API Testing with curl

#### Request OTP

```bash
curl -X POST http://localhost:8000/api/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected Response**:

```json
{
  "message": "OTP sent to test@example.com",
  "email": "test@example.com",
  "expires_in_minutes": 15
}
```

#### Verify OTP

```bash
curl -X POST http://localhost:8000/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "code": "123456"}'
```

**Expected Response**:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "auth_provider": "email",
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

#### Test Authenticated Endpoint

```bash
TOKEN="your-jwt-token-here"

curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Test 4: Rate Limiting

Make 6 OTP requests within 1 hour with the same email:

```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/auth/otp/request \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}'
  echo -e "\n"
  sleep 2
done
```

**Expected Result**:

- First 5 requests: Success (200)
- 6th request: Rate limit error (429)

```json
{
  "detail": "Rate limit exceeded. Please try again in X minutes."
}
```

### Test 5: OTP Expiration

1. Request an OTP
2. Wait 15+ minutes
3. Try to verify with the code

**Expected Result**: Error - "OTP expired or invalid"

### Test 6: Invalid Code

1. Request an OTP
2. Enter wrong code 3 times

**Expected Result**:

- First 2 attempts: "Invalid code" error
- 3rd attempt: OTP invalidated, must request new code

## Troubleshooting

### Email Not Received

**Problem**: OTP email doesn't arrive

**Solutions**:

1. **Check Spam Folder**

2. **Verify Authorized Recipients** (Sandbox mode):

   ```
   Mailgun Dashboard → Sending → Domains → Authorized Recipients
   ```

3. **Check Mailgun Logs**:

   - Go to Mailgun Dashboard → Sending → Logs
   - Look for your email delivery status

4. **Check Backend Logs**:

   ```bash
   docker compose logs backend | grep -i "otp\|mailgun"
   ```

5. **Test Mailgun API Directly**:
   ```bash
   curl -s --user 'api:YOUR_MAILGUN_API_KEY' \
     https://api.mailgun.net/v3/YOUR_DOMAIN/messages \
     -F from='noreply@YOUR_DOMAIN' \
     -F to='test@example.com' \
     -F subject='Test' \
     -F text='Test message'
   ```

### Rate Limit Issues

**Problem**: Getting rate limited too quickly

**Solution**: Adjust rate limit settings:

```bash
OTP_RATE_LIMIT_MAX_REQUESTS=10  # Increase from 5 to 10
OTP_RATE_LIMIT_WINDOW_HOURS=2   # Increase window to 2 hours
```

**Manual Reset** (Development only):

```bash
rm backend/data/auth/ratelimit_*.json
docker compose restart backend
```

### Configuration Errors

**Problem**: "Mailgun not configured" warning in logs

**Solution**: Verify environment variables are set:

```bash
# Check in running container
docker compose exec backend env | grep MAILGUN
```

Expected output:

```
MAILGUN_API_KEY=key-xxxxxxxx
MAILGUN_DOMAIN=sandboxXXXX.mailgun.org
MAILGUN_FROM_EMAIL=noreply@sandboxXXXX.mailgun.org
```

### Invalid Token Error

**Problem**: "Invalid or expired token" when accessing API

**Solutions**:

1. **Check Token Format**: Should be `Bearer <token>`

   ```bash
   curl -H "Authorization: Bearer eyJhbGci..." http://localhost:8000/api/auth/me
   ```

2. **Verify JWT Secret**: Same secret in backend environment

3. **Check Token Expiration**: Default is 24 hours
   ```bash
   # Decode JWT (without verification)
   echo "eyJhbGci..." | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .
   ```

## Email Template

The OTP email uses this template (configurable in `backend/src/services/email_service.py`):

```
Subject: Your Login Code

Your verification code is: 123456

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.
```

## Security Considerations

### Production Best Practices

1. **Use Custom Domain**: Not Mailgun sandbox
2. **Enable DKIM/SPF**: Improves deliverability and security
3. **Strong JWT Secret**: Minimum 32 bytes, randomly generated
4. **HTTPS Only**: Always use HTTPS in production
5. **Rate Limiting**: Keep default limits (5 requests/hour)
6. **Monitor Logs**: Watch for suspicious activity

### Development vs Production

| Feature     | Development | Production    |
| ----------- | ----------- | ------------- |
| Domain      | Sandbox     | Custom domain |
| HTTPS       | Optional    | Required      |
| JWT Secret  | Simple      | Strong random |
| Rate Limits | Relaxed     | Strict        |
| Email Logs  | Visible     | Private       |

## Integration with Other Auth Methods

Email OTP can coexist with OIDC providers:

```bash
# Enable both Email OTP and Google OAuth
MAILGUN_API_KEY=key-xxx
MAILGUN_DOMAIN=mg.example.com
MAILGUN_FROM_EMAIL=noreply@example.com

OIDC_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
OIDC_GOOGLE_CLIENT_SECRET=GOCSPX-xxx
```

Users can choose their preferred method on the login page.

## Next Steps

- [Setup Google OAuth](./SETUP_GOOGLE_OAUTH.md)
- [Setup GitHub OAuth](./SETUP_GITHUB_OAUTH.md)
- [Setup GitLab OAuth](./SETUP_GITLAB_OAUTH.md)
- [Complete Authentication Guide](../AUTHENTICATION.md)
