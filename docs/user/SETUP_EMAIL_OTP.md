# Email OTP Setup (Mailgun)

## Prerequisites

- Mailgun account ([free tier available](https://www.mailgun.com/))
- Docker or Podman

## 1. Get Mailgun Credentials

### Production (custom domain)

1. Add and verify your domain in Mailgun dashboard
2. Configure DNS records (SPF, DKIM, CNAME)
3. Go to **Settings → API Keys**
4. Copy your **Private API Key**

### Development (sandbox domain)

1. Go to **Sending → Domains**
2. Use the provided sandbox domain (e.g., `sandboxXXXXXXXX.mailgun.org`)
3. Add authorized recipients under the domain
4. Go to **Settings → API Keys** and copy your **Private API Key**

## 2. Configure Environment Variables

```bash
DEPLOYMENT_MODE=public
JWT_SECRET=<generated-secret>               # openssl rand -hex 32
SESSION_COOKIE_SECRET=<generated-secret>    # openssl rand -hex 32

MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=sandboxXXXXXXXX.mailgun.org  # or mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com

BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8080
```

### Optional OTP settings

```bash
OTP_LENGTH=6                    # Default: 6
OTP_EXPIRATION_MINUTES=15       # Default: 15
OTP_MAX_ATTEMPTS=3              # Default: 3
OTP_RATE_LIMIT_MAX_REQUESTS=5   # Default: 5 per hour
OTP_RATE_LIMIT_WINDOW_HOURS=1   # Default: 1 hour window
```

## 3. Start the Application

```bash
docker compose up -d
```

Check backend logs to confirm Mailgun is configured:

```bash
docker compose logs backend | grep -i mailgun
# Expected: "Mailgun configuration detected - Email OTP authentication enabled"
```

## 4. Verify

1. Open http://localhost:8080
2. Enter your email and click "Send Code"
3. Check your inbox for the 6-digit OTP
4. Enter the code and click "Verify"

## Test Users (Development Only)

For development without Mailgun, enable static OTP test users:

```bash
TEST_USER_ENABLED=true
TEST_USER_EMAIL_1=test@example.com
TEST_USER_OTP_1=123456
TEST_USER_EMAIL_2=test2@example.com     # for multi-user testing
TEST_USER_OTP_2=123456
```

⚠️ **Never enable test users in production.**

## Troubleshooting

### Email not received

1. Check spam folder
2. Verify authorized recipients (sandbox mode): Mailgun Dashboard → Sending → Domains → Authorized Recipients
3. Check Mailgun logs: Dashboard → Sending → Logs
4. Check backend logs: `docker compose logs backend | grep -i "otp\|mailgun"`
5. Test Mailgun directly:
   ```bash
   curl -s --user 'api:YOUR_API_KEY' \
     https://api.mailgun.net/v3/YOUR_DOMAIN/messages \
     -F from='noreply@YOUR_DOMAIN' \
     -F to='test@example.com' \
     -F subject='Test' \
     -F text='Test message'
   ```

### "Mailgun not configured" in logs

Verify environment variables are set:
```bash
docker compose exec backend env | grep MAILGUN
```

### Rate limited

Increase limits or reset manually (dev only):
```bash
rm backend/data/auth/ratelimit_*.json
docker compose restart backend
```

## Production Checklist

- [ ] Use a custom domain (not sandbox)
- [ ] Enable DKIM and SPF
- [ ] Use strong, randomly generated JWT and cookie secrets
- [ ] Enable HTTPS
- [ ] Keep default rate limits (5 requests/hour)
- [ ] Monitor backend logs for suspicious activity
