<!--
Sync Impact Report:
Version change: NEW → 1.0.0
Added sections:
- Complete constitution framework with 5 core principles
- Technology Stack Standards section
- Development Workflow section
Templates requiring updates: ⚠ All templates updated for initial constitution
Follow-up TODOs: None
-->

# Vagrantfile Generator Constitution

## Core Principles

### I. Modular Architecture First
All features MUST be built using modular, component-based architecture. Components MUST be self-contained with clear boundaries and single responsibilities. HTML components use `data-include-html` for dynamic loading. Backend services follow clean separation between API, business logic, and data persistence layers.

*Rationale: The recent 93.2% file size reduction (896→61 lines) and successful 4-phase refactoring proved modular architecture dramatically improves maintainability, debugging, and development velocity.*

### II. Dependency Constraint (NON-NEGOTIABLE)
New dependencies are strictly LIMITED unless absolutely necessary. Existing tech stack (FastAPI, Alpine.js, Tailwind CSS, Podman) MUST be utilized and expanded before introducing new technologies. All dependency additions require explicit justification and impact assessment.

*Rationale: Lean dependency management reduces security surface, simplifies deployment, and prevents feature bloat that conflicts with the tool's focus on simplicity.*

### III. Container-First Development
All development and deployment MUST occur within containerized environments. Both development (`make dev`) and production deployments use Docker/Podman containers. Environment parity between development and production is mandatory.

*Rationale: Container-first ensures consistent environments, simplifies setup across different development machines, and provides production-ready deployment patterns.*

### IV. Frontend-Backend Separation with Clear Contracts
Frontend (HTML/Alpine.js/Tailwind) and backend (FastAPI/Python) MUST maintain clear API contracts. All communication occurs through well-defined REST endpoints. Backend changes requiring frontend updates MUST be backward compatible or include migration strategies.

*Rationale: Clear separation allows independent development, testing, and deployment of frontend and backend components while maintaining system integrity.*

### V. Progressive Enhancement with Graceful Degradation
User interface MUST work without JavaScript for core functionality, with Alpine.js providing enhanced interactivity. All critical paths (project creation, VM configuration, Vagrantfile generation) MUST be accessible even if client-side features fail.

*Rationale: Ensures accessibility, improves performance on low-end devices, and provides reliability when JavaScript fails to load or execute.*

## Technology Stack Standards

**Backend Requirements:**
- FastAPI for REST API with automatic OpenAPI documentation
- Python 3.11+ with Pydantic V2 for data validation
- JSON file persistence (no database unless scale demands it)
- Structured logging with appropriate levels

**Frontend Requirements:**
- HTML-first with modular component architecture
- Alpine.js for reactive state management (no framework complexity)
- Tailwind CSS for styling with custom component classes in `@layer components`
- Vite for development server and build tooling

**Infrastructure Requirements:**
- Container deployment using Docker/Podman compose
- Health checks for all services
- Environment variable configuration (no hardcoded values)
- Volume persistence for data and application state

## Development Workflow

**Architecture Evolution:**
- All architectural changes MUST follow the established 4-phase modular extraction process
- Component extraction requires testing at each phase
- Alpine.js state management patterns MUST be preserved across module boundaries

**Testing Requirements:**
- Contract testing between frontend and backend required for API changes
- Integration testing for multi-component workflows (project → VM → Vagrantfile generation)
- Visual regression testing for UI components

**Code Organization:**
- Backend: `src/api/`, `src/services/`, `src/models/` structure
- Frontend: `views/`, `components/`, `modals/` structure with `html-loader.js`
- Shared configuration in `docker-compose.yml` (single source of truth)

## Governance

This constitution supersedes all other development practices and guides technical decision-making. All feature development, architectural changes, and dependency additions MUST align with these principles.

**Amendment Process:**
- Constitution changes require documentation of impact on existing principles
- Version increments follow semantic versioning (MAJOR: breaking governance changes, MINOR: new principles/sections, PATCH: clarifications)
- All template files in `.specify/templates/` MUST be updated to reflect constitution changes

**Compliance Verification:**
- All PRs MUST verify alignment with modular architecture principles
- Dependency additions MUST include necessity justification
- Container deployment MUST be maintained for all changes

**Version**: 1.0.0 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-09-25