![logo](./docs/pics/logo_light.png#gh-light-mode-only)
![logo](./docs/pics/logo_dark.png#gh-dark-mode-only)

# Overview [![Build, Publish & Release](https://github.com/marekruzicka/vagrantfile-generator/actions/workflows/release.yml/badge.svg)](https://github.com/marekruzicka/vagrantfile-generator/actions/workflows/release.yml) ![Latest Release](https://img.shields.io/github/v/release/marekruzicka/vagrantfile-generator.svg)

A modern web-based application for generating Vagrantfiles with an intuitive interface.  
Create and manage multiple virtual machines, configure networking, provisioners, triggers, plugins, and generate working Vagrant configurations with ease.

Take a [Quick Tour](./docs/APP_OVERVIEW.md) through app inteface.

## Features

- **🚀 Modern Interface**: Clean, responsive web interface that works on any device
- **📦 Multiple VMs**: Create and edit multiple virtual machines with custom memory, CPUs, boxes, and network settings
- **🌐 Advanced Networking**: Static IPs, DHCP, port forwarding, and private networks between VMs
- **🔧 Provisioners**: Add shell scripts for VM setup (anisble to come)
- **⚙️ Plugins & Triggers**: Install Vagrant plugins and configure triggers for pre/post Vagrant actions
- **💾 Project Management**: Save and organize your Vagrant configurations
- **✅ Real-time Validation**: Immediate feedback on configuration errors
- **📝 Production-Ready Output**: Generate syntactically correct, ready-to-use Vagrantfiles
- **📱 Cross-Platform**: Works on desktop, tablet, and mobile devices

## Requirements

Docker or Podman installed on your system
Modern web browser (Chrome, Firefox, Safari, Edge)
Available port 8080 for the self-hosted quick start (developer Compose also uses port 8000)

## Deployment Modes

Vagrantfile Generator supports two deployment modes:

### Self-Hosted Mode (Default)

Perfect for local development or personal use. No authentication required.

- ✅ No configuration needed
- ✅ All features available immediately
- ✅ Data stored locally in `/data` directory
- ⚠️ Not suitable for multi-user or public deployments

### Public Mode

Designed for multi-user environments with full authentication.

- 🔒 User authentication required (Email OTP + Google/GitHub/GitLab OAuth)
- 👥 Multi-user support with data isolation
- 🔐 Session management with JWT tokens
- 📧 Email OTP delivery via Mailgun
- 🌐 OIDC/OAuth integration with external providers

**Required Environment Variables for Public Mode:**

```bash
# Deployment
DEPLOYMENT_MODE=public

# JWT Configuration
JWT_SECRET=<your-jwt-secret>  # Generate with: openssl rand -hex 32
SESSION_COOKIE_SECRET=<your-session-cookie-secret>  # Generate with: openssl rand -hex 32

# Backend URLs (required for OIDC)
BASE_URL=https://your-domain.com
FRONTEND_URL=https://your-domain.com

# Email OTP (optional - falls back to OIDC only if not configured)
MAILGUN_API_KEY=<your-mailgun-api-key>
MAILGUN_DOMAIN=<your-mailgun-domain>
MAILGUN_FROM_EMAIL=noreply@your-domain.com

# OIDC Providers (at least one required)
OIDC_GOOGLE_CLIENT_ID=<google-oauth-client-id>
OIDC_GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>

OIDC_GITHUB_CLIENT_ID=<github-oauth-client-id>
OIDC_GITHUB_CLIENT_SECRET=<github-oauth-client-secret>

OIDC_GITLAB_CLIENT_ID=<gitlab-oauth-client-id>
OIDC_GITLAB_CLIENT_SECRET=<gitlab-oauth-client-secret>
OIDC_GITLAB_URL=https://gitlab.com  # Optional, defaults to gitlab.com
```

See [AUTHENTICATION.md](./docs/AUTHENTICATION.md) for detailed authentication setup guide.

## Quick Start

### For Users (Running the App)

```bash
# Download latest compose.yml
curl -fsSLO https://raw.githubusercontent.com/marekruzicka/vagrantfile-generator/refs/heads/master/compose.yml

# Start the application with Podman or Docker
podman-compose up -d
# or: docker compose up -d

# Open your browser: http://localhost:8080
```

This uses prebuilt GHCR `latest` images and runs in self-hosted mode. The backend is not exposed directly; API requests go through the frontend at `/api`.

### For Developers (Local Development)

```bash
# Clone the repository
git clone https://github.com/marekruzicka/vagrantfile-generator.git
cd vagrantfile-generator

# Run native setup script
./setup-local-dev.sh

# Open in VS Code and press F5 to start debugging
# Or smoke-test local container builds with compose-dev.yml:
make up
make logs
make down
```

See [LOCAL_DEVELOPMENT.md](./docs/LOCAL_DEVELOPMENT.md) for detailed development setup.

## How to Use

1. **Start the application** using the quick start command above
2. **Open your browser** and go to http://localhost:8080
3. **Click on shiny things** - it's pretty self explanatory

## Support & Documentation

- **Local Development**: See [LOCAL_DEVELOPMENT.md](./docs/LOCAL_DEVELOPMENT.md) for native development setup
- **Deployment Modes**: See [ENVIRONMENTS.md](./docs/ENVIRONMENTS.md) for native dev, Compose, and Helm environment roles
- **Authentication Setup**: See [AUTHENTICATION.md](./docs/AUTHENTICATION.md) for multi-user configuration
- **Contributing**: See [CONTRIBUTING.md](./CONTRIBUTING.MD) for contribution guidelines
- **Architecture**: See [APP_OVERVIEW.md](./docs/APP_OVERVIEW.md) for a tour of the application
- **Issues**: Report bugs and feature requests through [GitHub Issues](https://github.com/marekruzicka/vagrantfile-generator/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details.
