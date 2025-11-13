# Vagrantfile-generator Development Guidelines

## Active Technologies
- HTML5, Alpine.js 3.x, Tailwind CSS 3.x + Alpine.js, Markdown parsing, containerization
- Python 3.11+ (backend), JavaScript ES6+ syntax (frontend, vanilla JS with classic script loading, Alpine.js 3.x) + FastAPI (backend API framework), Alpine.js 3.x (frontend reactivity), Tailwind CSS 3.x (UI styling), authlib (OIDC client), PyJWT (JWT tokens), requests (Mailgun API), pydantic (validation) (001-multiuser-auth)
- File-based JSON storage (`/data/` directory structure with `/data/shared/`, `/data/users/{user-id}/`, `/data/auth/`) (001-multiuser-auth)

## Project Structure
```
backend/
frontend/
```
## Code Style
HTML5, Alpine.js 3.x, Tailwind CSS 3.x: Follow standard conventions

## Runtime
containers - podman, podman-compose (utilize Makefile)

## Testing
chrome-devtools MCP

## Recent Changes
- 001-multiuser-auth: Added Python 3.11+ (backend), JavaScript ES6+ (frontend with Alpine.js 3.x) + FastAPI (backend API framework), Alpine.js 3.x (frontend reactivity), Tailwind CSS 3.x (UI styling), authlib (OIDC client), python-jose (JWT), requests (Mailgun API), pydantic (validation)
