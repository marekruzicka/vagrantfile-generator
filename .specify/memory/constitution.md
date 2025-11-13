<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0
Modified principles:
  - Principle III: "Test Coverage for Critical Paths" → "Pragmatic User-Focused Testing"
    (Reduced scope: frontend user flows via chrome-devtools MCP, external integrations only)
Added sections: N/A
Removed sections: N/A
Templates requiring updates:
  ✅ .specify/templates/plan-template.md (validated - compatible)
  ✅ .specify/templates/spec-template.md (validated - compatible)
  ✅ .specify/templates/tasks-template.md (validated - compatible)
  ⚠ .specify/templates/commands/*.md (directory does not exist - not applicable)
Follow-up TODOs: None
-->

# Vagrantfile Generator Constitution

## Core Principles

### I. API-First Architecture

All features MUST be designed with API-first approach. The backend exposes RESTful APIs that are consumed by the frontend. This ensures:
- Clear separation of concerns between presentation and business logic
- APIs are independently testable via contract tests
- Multiple frontends can be supported without backend changes
- API documentation (OpenAPI/Swagger) is automatically generated and maintained

**Rationale**: Enables flexible frontend implementations while maintaining a stable, well-documented backend contract. Critical for the project's goal of providing a modern web interface that can evolve independently.

### II. Container-Native Development

All development and deployment MUST use containerization (Podman preferred, Docker compatible). This ensures:
- Consistent development environments across all contributors
- No "works on my machine" issues
- Hot-reloading for both frontend and backend during development
- Production-like environment locally via compose files
- Clear separation of development (`compose-dev.yml`) and production (`compose-prod.yml`) configurations

**Rationale**: Reduces onboarding friction, ensures consistency, and allows developers to focus on code rather than environment setup. The Makefile wrapper simplifies common operations.

### III. Pragmatic User-Focused Testing

Testing MUST focus on what matters: user-facing functionality and external integrations. Avoid over-testing internal implementation details. This includes:
- Frontend user flows tested via Chrome DevTools MCP (user point of view)
- Integration tests ONLY for external service interactions (e.g., API calls, third-party services)
- No requirement for unit tests of internal business logic
- Manual testing is acceptable for personal project features

**Rationale**: This is a personal project. Time is better spent on features than exhaustive test suites. Focus testing effort where it provides the most value: ensuring users can successfully complete their tasks and external integrations don't break.

### IV. Progressive Enhancement with Modern Web Standards

Frontend MUST use HTML5, Alpine.js 3.x, and Tailwind CSS 3.x with focus on:
- Semantic HTML as foundation
- Progressive enhancement (works without JavaScript for core features where possible)
- Responsive design supporting desktop, tablet, and mobile
- Accessibility (ARIA attributes, keyboard navigation)
- No framework lock-in beyond Alpine.js (lightweight, vanilla JS compatible)

**Rationale**: Keeps the frontend lightweight, maintainable, and accessible. Alpine.js provides reactivity without the complexity of larger frameworks, aligning with the project's goal of simplicity and cross-platform support.

### V. User-Centric Configuration Management

All features MUST support the complete user workflow:
- Create, read, update, delete (CRUD) for all configuration entities
- Real-time validation with immediate user feedback
- Project organization and persistence
- Preview before generation (Vagrantfile preview)
- Export ready-to-use configurations

**Rationale**: The application's core value is ease of use. Users should be able to create complex Vagrant configurations without manual file editing, with confidence that the output is correct.

## Development Workflow

**Source Control**: Git with feature branches following `[###-feature-name]` pattern where applicable.

**Branching Strategy**:
- `master` branch is the stable production branch
- Feature branches for new capabilities
- Hotfix branches for critical production issues

**Local Development**:
- Use `make dev` for one-command startup (builds and runs dev environment)
- Backend runs on http://localhost:8000 with FastAPI auto-reload
- Frontend runs on http://localhost:5173 with Vite hot-reload
- Changes to code are immediately reflected without container rebuild

**Code Organization**:
- Backend: `backend/src/` with models, services, and API endpoints
- Frontend: `frontend/src/` with components, views, and modals
- Tests: `backend/tests/` organized by type (contract, integration)
- Documentation: `docs/` for user-facing guides, `.specify/` for development templates

## Quality Gates

**Pre-Commit Requirements**:
- Code SHOULD follow language-specific standard conventions (not strictly enforced)
- Major linting errors SHOULD be addressed (minor issues acceptable)
- External integrations SHOULD have basic integration tests
- Core user flows tested via chrome-devtools MCP when time permits

**Review Requirements**:
- Changes SHOULD be validated in containerized environment (use `make dev`)
- API changes SHOULD update OpenAPI documentation (FastAPI auto-generates)
- Frontend changes SHOULD be visually tested on desktop (mobile testing when relevant)
- Breaking changes SHOULD be noted in CHANGELOG.md

**Release Criteria**:
- Core functionality works in containerized environment
- No show-stopping bugs
- README reflects major changes
- Docker images build successfully

## Governance

This constitution defines the architectural principles and quality standards for the Vagrantfile Generator project. All development decisions MUST align with these principles.

**Amendment Process**:
- Proposed amendments MUST be documented with rationale
- Major changes (removing/redefining principles) require stakeholder review
- Minor additions/clarifications can be made by maintainers
- All amendments MUST update the version number and LAST_AMENDED_DATE
- Amendment impact on existing code and templates MUST be assessed

**Versioning Policy**:
- MAJOR version: Backward incompatible governance changes, principle removals/redefinitions
- MINOR version: New principles added, material expansions to guidance
- PATCH version: Clarifications, wording improvements, typo fixes

**Compliance Review**:
- Constitution compliance MUST be checked during feature planning
- Deviations MUST be explicitly justified and documented
- Templates in `.specify/templates/` MUST align with these principles
- The `.github/copilot-instructions.md` provides day-to-day development guidance and MUST remain consistent with this constitution

**Version**: 1.1.0 | **Ratified**: 2025-11-13 | **Last Amended**: 2025-11-13
