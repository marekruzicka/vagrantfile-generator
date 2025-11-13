# Feature Specification: Multi-User Support with Hybrid Authentication

**Feature Branch**: `001-multiuser-auth`  
**Created**: 2025-11-13  
**Status**: Draft  
**Input**: User description: "Add self-hosted/public mode, including multi-user support, with hybrid authentication (OIDC + Email OTP)"

## Clarifications

### Session 2025-11-13

- Q: Which email service configuration should be used for OTP delivery? → A: Mailgun only (requires API key for all environments including local dev)
- Q: How should user IDs be generated for new users in public mode? → A: Generate UUID v4 on first authentication (random, globally unique)
- Q: How should temporary OTP codes and rate-limiting data be stored? → A: In-memory with file-based persistence (survives restarts, consistent with project architecture)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Self-Hosted Mode Usage (Priority: P1)

A developer or small team wants to use the Vagrantfile Generator locally or on their internal server without authentication overhead. They deploy the application and immediately start creating projects, managing boxes, plugins, provisioners, and triggers with full control over all resources.

**Why this priority**: This is the simplest deployment mode and maintains backward compatibility with current usage patterns. It ensures existing users can continue using the application without disruption.

**Independent Test**: Deploy application with default configuration, access at localhost:8080, create a project with VMs, save it, and verify it persists in the shared data directory. No login required.

**Acceptance Scenarios**:

1. **Given** application deployed with DEPLOYMENT_MODE=self-hosted (or unset), **When** user accesses the application, **Then** they immediately see the main interface without login screen
2. **Given** user in self-hosted mode, **When** they create/edit/delete any resource (boxes, plugins, provisioners, triggers, projects), **Then** all operations succeed without permission errors
3. **Given** user in self-hosted mode, **When** they restart the application, **Then** all their data persists in `/data/shared/` directory

---

### User Story 2 - Email OTP Authentication (Priority: P1)

A user wants to access a public deployment of the Vagrantfile Generator. They enter their email address, receive a 6-digit code via email, enter it within 15 minutes, and gain access to the application. They can now create personal projects and custom resources that only they can see and edit, while also browsing a catalog of shared system resources.

**Why this priority**: Email OTP is the simplest authentication method to implement and test locally (no OAuth app registration needed). Provides 100% user coverage and establishes the core authentication infrastructure that OIDC will build upon. Must be working before OIDC implementation.

**Independent Test**: Deploy in public mode, request OTP for an email address, receive code via email, verify code, confirm session created and user can access the application.

**Acceptance Scenarios**:

1. **Given** application deployed with DEPLOYMENT_MODE=public, **When** unauthenticated user accesses the application, **Then** they are redirected to login page with email input field
2. **Given** user on login page, **When** they enter their email address and click "Send Code", **Then** they receive a 6-digit OTP via email within 1 minute
3. **Given** user received OTP, **When** they enter the correct code within 15 minutes, **Then** they are authenticated and can access the application
4. **Given** user received OTP, **When** they enter an incorrect code, **Then** they see an error message and can retry (up to 5 attempts)
5. **Given** user received OTP, **When** 15 minutes have passed, **Then** the code expires and they must request a new one
6. **Given** user requesting OTP, **When** they make more than 5 requests within 1 hour, **Then** they are rate-limited with appropriate error message
7. **Given** authenticated user, **When** they create a project or custom resource, **Then** it is saved to their personal directory (`/data/users/{user-id}/`)
8. **Given** authenticated user, **When** they list resources (boxes, plugins, etc.), **Then** they see both shared system resources (read-only) and their personal resources (editable)
9. **Given** authenticated user, **When** they attempt to edit or delete a shared system resource, **Then** operation is blocked with appropriate error message

---

### User Story 3 - Social Login Authentication (Priority: P3)

A user wants to access a public deployment using their existing developer account. They visit the site, see a login page, click "Continue with GitHub" (or Google/GitLab), authorize the application, and are immediately logged in with the same capabilities as email OTP users.

**Why this priority**: OIDC social login provides convenience for users who prefer it, but requires OAuth app registration with each provider and is harder to test locally. Should be implemented after email OTP authentication is stable.

**Independent Test**: Deploy in public mode, navigate to login page, complete OIDC flow with any provider, verify user session created, create a personal project, verify it's saved in user-specific directory.

**Acceptance Scenarios**:

1. **Given** user on login page, **When** they click "Continue with [Provider]" and complete authorization, **Then** they are redirected back to the application with active session
2. **Given** authenticated user via OIDC, **When** they create a project or custom resource, **Then** it is saved to their personal directory (`/data/users/{user-id}/`)
3. **Given** authenticated user via OIDC, **When** they list resources, **Then** they see both shared system resources (read-only) and their personal resources (editable)

---

### User Story 4 - Session Persistence (Priority: P2)

An authenticated user (OIDC or OTP) closes their browser and returns the next day. Their session is still valid (within 24 hours), and they can continue working without re-authenticating.

**Why this priority**: Essential for good user experience - users shouldn't have to log in every time they visit.

**Independent Test**: Log in, close browser, reopen after several hours (but within 24 hours), verify session still active.

**Acceptance Scenarios**:

1. **Given** user authenticated via OIDC or OTP, **When** they receive a session token, **Then** the token is valid for 24 hours
2. **Given** user with valid session token, **When** they close and reopen their browser within 24 hours, **Then** they remain authenticated
3. **Given** user with expired session token (>24 hours), **When** they access the application, **Then** they are redirected to login page

---

### User Story 5 - Data Isolation in Public Mode (Priority: P1)

Two users (Alice and Bob) both have accounts on a public deployment. Alice creates a custom box definition for her specific use case. Bob cannot see, edit, or delete Alice's custom box. However, both Alice and Bob can see and use the shared system boxes provided by the administrator.

**Why this priority**: Core security requirement for multi-user deployments. Data leakage between users would be a critical vulnerability.

**Independent Test**: Create two user accounts, have each create personal resources, verify each user can only see/edit their own resources plus shared system resources.

**Acceptance Scenarios**:

1. **Given** two authenticated users (Alice and Bob), **When** Alice creates a custom resource, **Then** Bob cannot see it in his resource list
2. **Given** two authenticated users, **When** each creates a project, **Then** each user only sees their own projects
3. **Given** shared system resource exists in `/data/shared/` (added via manual file copying before deployment), **When** any user lists resources, **Then** they see the shared resource marked as read-only
4. **Given** user viewing shared system resource, **When** they attempt to delete it via the interface, **Then** the delete button is disabled or operation fails with permission error

---

### Edge Cases

- What happens when a user's OIDC provider account is deleted? (Session expires, they can log in again with different method)
- What happens when email delivery fails for OTP? (User sees timeout error after 2 minutes, can retry)
- What happens when JWT secret key is rotated? (All existing sessions invalidate, users must re-authenticate)
- What happens when user tries to access another user's resource by guessing the ID? (403 Forbidden error)
- What happens when two users create resources with same name? (Allowed - resources are namespaced by user ID in file paths)
- What happens when self-hosted mode is switched to public mode? (Existing data in `/data/shared/` becomes read-only system resources for all users. This is the intended method for preparing and testing shared resources before production deployment.)
- What happens when session expires while user is editing? (Next API call returns 401, frontend redirects to login with optional "session expired" message)

## Requirements *(mandatory)*

### Functional Requirements

#### Deployment Modes

- **FR-001**: System MUST support two deployment modes: "self-hosted" (default) and "public", controlled by `DEPLOYMENT_MODE` environment variable
- **FR-002**: In self-hosted mode, system MUST allow unrestricted access to all features without authentication
- **FR-003**: In public mode, system MUST require authentication for all operations except viewing the login page
- **FR-004**: System MUST use unified data directory structure for both modes with permission differences determined by deployment mode

#### Authentication (Public Mode)

- **FR-005**: System MUST support OIDC authentication with Google, GitHub, and GitLab as identity providers
- **FR-006**: System MUST support email-based one-time password (OTP) authentication as alternative to OIDC
- **FR-007**: OTP codes MUST be 6 digits, valid for 15 minutes, and sent via email using Mailgun API
- **FR-008**: System MUST rate-limit OTP requests to 5 attempts per email address per hour
- **FR-009**: System MUST issue session tokens valid for 24 hours upon successful authentication
- **FR-010**: Session tokens MUST be transmitted in Authorization header as Bearer tokens and stored in browser localStorage (Note: localStorage is not encrypted at rest; security relies on HTTPS for transmission and browser same-origin policy for access control)
- **FR-011**: System MUST validate session token on every authenticated API request
- **FR-012**: System MUST require Mailgun API key configuration for email delivery in all deployment environments

#### Data Organization

- **FR-013**: System MUST store shared/system resources in `/data/shared/` directory (boxes, plugins, provisioners, triggers, and optionally projects in self-hosted mode)
- **FR-014**: In public mode, system MUST store user-specific resources in `/data/users/{user-id}/` directories
- **FR-015**: In public mode, when listing resources, system MUST merge shared resources with user-specific resources
- **FR-016**: Shared resources MUST be marked with `is_shared: true` flag when returned to users in public mode
- **FR-017**: In self-hosted mode, system MUST store all projects in `/data/shared/projects/`
- **FR-018**: In public mode, system MUST store projects in `/data/users/{user-id}/projects/`
- **FR-019**: System MUST store temporary OTP codes and rate-limiting data in memory with file-based persistence to `/data/auth/` directory
- **FR-020**: System MUST persist OTP and rate-limiting data to survive application restarts

#### Permissions

- **FR-021**: In self-hosted mode, users MUST have read-write access to all resources in `/data/shared/`
- **FR-022**: In public mode, users MUST have read-only access to `/data/shared/` resources and MUST NOT be able to modify or delete shared system resources
- **FR-023**: In public mode, users MUST have read-write access to their own `/data/users/{user-id}/` resources
- **FR-024**: In public mode, users MUST NOT be able to access other users' resources
- **FR-025**: System MUST enforce permissions at the service layer, not just the UI layer
- **FR-025**: System MUST enforce permissions at the service layer, not just the UI layer

#### User Interface

- **FR-026**: In self-hosted mode, application MUST display main interface without login page
- **FR-027**: In public mode, unauthenticated users MUST be redirected to login page
- **FR-028**: Login page MUST display OIDC provider buttons (Google, GitHub, GitLab) and email OTP input field
- **FR-029**: Settings pages MUST use visual indicators to distinguish shared resources (read-only) from user resources (editable)
- **FR-030**: Resource UI controls MUST adapt to resource type: shared resources display view-only controls (no edit/delete buttons), while user resources display full CRUD controls (edit and delete buttons)

#### Session Management

- **FR-031**: System MUST create user profile on first successful authentication
- **FR-032**: User profile MUST include user ID (UUID v4), email, display name, and authentication provider
- **FR-033**: System MUST generate unique user ID as UUID v4 for each new user to prevent enumeration attacks
- **FR-034**: System MUST log out users by invalidating their session token (client-side removal)
- **FR-035**: System MUST provide endpoint to retrieve current authenticated user information

### Key Entities

- **User Profile**: Represents an authenticated user with unique ID (UUID v4), email address, display name, and authentication provider (google|github|gitlab|email). Stored in `/data/users/{user-id}/profile.json` in public mode. User ID is randomly generated to prevent enumeration attacks.
- **Session Token**: JWT containing user ID, email, name, authentication provider, issue time, and expiration time. Valid for 24 hours
- **OTP Request**: Temporary record of OTP code, associated email, expiration time (15 minutes), and attempt count. Rate-limited to 5 requests per hour per email. Stored in memory with file-based persistence to `/data/auth/otp-requests.json` to survive application restarts.
- **Rate Limit Record**: Tracks OTP request timestamps per email address for rate limiting enforcement. Stored in memory with file-based persistence to `/data/auth/rate-limits.json`.
- **Deployment Mode**: Configuration setting determining authentication requirements and permission model. Two values: "self-hosted" (no auth, full access) or "public" (auth required, isolated user data)
- **Resource**: Generic entity representing boxes, plugins, provisioners, triggers, or projects. Has `is_shared` flag in public mode indicating whether it's a system resource (read-only) or user resource (editable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Self-hosted mode users can start using the application within 30 seconds of deployment without any authentication setup
- **SC-002**: Public mode users can complete authentication via email OTP within 2 minutes (including email delivery time)
- **SC-003**: Public mode users can complete authentication via OIDC within 1 minute (including provider authorization)
- **SC-004**: 100% of API endpoints respect deployment mode settings (authentication enforced in public mode, not required in self-hosted mode)
- **SC-005**: 100% data isolation: no user can access another user's resources in public mode
- **SC-006**: Session tokens remain valid for 24 hours, allowing users to close and reopen browser without re-authenticating
- **SC-007**: Rate limiting prevents abuse: maximum 5 OTP requests per hour per email address
- **SC-008**: Users in public mode see combined view of shared system resources plus their personal resources within 500ms (server-side processing only, excluding network latency, for typical load: <100 personal resources + <500 shared resources)
- **SC-009**: Visual indicators (icons or labels with distinct colors) distinguish read-only shared resources from editable user resources with WCAG AA minimum contrast ratio (4.5:1 for text, 3:1 for icons)
