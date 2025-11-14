# Tasks: Multi-User Support with Hybrid Authentication

**Feature**: 001-multiuser-auth  
**Input**: Design documents from `/specs/001-multiuser-auth/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story to enable independent implementation and testing

---

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1, US2, US3, US4, US5) - maps to spec.md priorities
- All tasks include exact file paths

---

## Phase 1: Setup & Infrastructure

**Purpose**: Project initialization, dependencies, and shared utilities

### Dependencies

- [X] T001 Add PyJWT to backend/requirements.txt (version 2.8.0)
- [X] T002 Add authlib to backend/requirements.txt (version 1.3.0)
- [X] T003 Add requests to backend/requirements.txt (version 2.31.0)
- [ ] T004 Install dependencies: `pip install -r backend/requirements.txt`

### Environment Configuration

- [X] T005 Create backend/.env.example with all auth-related variables (DEPLOYMENT_MODE, JWT_SECRET, MAILGUN_API_KEY, MAILGUN_DOMAIN, OIDC credentials)
- [X] T006 Add startup validation in backend/src/main.py to check MAILGUN_API_KEY configuration when DEPLOYMENT_MODE=public (log warning if missing, allow app to start with OTP disabled)
- [X] T007 Update compose-dev.yml to include new environment variables from backend/.env
- [X] T008 Update compose-prod.yml to include new environment variables

### Directory Structure

- [X] T009 Create backend/data/auth/ directory for OTP and rate limit storage
- [X] T010 Create backend/data/users/ directory for user-specific data
- [X] T011 Create backend/src/middleware/ directory for authentication middleware
- [X] T012 Create frontend/src/views/login/ directory for login page components

### Shared Utilities

- [X] T013 [P] Create backend/src/utils/deployment.py with get_deployment_mode() function
- [X] T014 [P] Create backend/src/utils/validators.py with email and UUID validation helpers
- [X] T015 [P] Create backend/src/api/config.py with GET /api/config/deployment-mode endpoint (returns {"mode": "self-hosted"|"public"})

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core authentication infrastructure needed by all user stories

### Models (Data Layer)

- [X] T016 [P] Create backend/src/models/user_profile.py with UserProfile pydantic model
- [X] T017 [P] Create backend/src/models/otp_request.py with OTPRequest pydantic model
- [X] T018 [P] Create backend/src/models/rate_limit.py with RateLimitRecord pydantic model
- [X] T019 [P] Create backend/src/models/session_token.py with SessionToken pydantic model (JWT claims structure)

### Core Services (Business Logic)

- [X] T020 Create backend/src/services/email_service.py with Mailgun integration (send_otp_email method)
- [X] T021 Create backend/src/services/session_service.py with JWT token generation and validation (create_token, verify_token methods)
- [X] T022 Create backend/src/services/permission_service.py with can_edit_resource and can_delete_resource methods

### Middleware

- [X] T023 Create backend/src/middleware/auth_middleware.py with get_current_user dependency (validates JWT, checks deployment mode)

### File Service Updates

- [X] T024 Update backend/src/services/file_service.py to add get_user_data_path method (returns /data/users/{user_id}/)
- [X] T025 Update backend/src/services/file_service.py to add get_shared_data_path method (returns /data/shared/)
- [X] T026 Update backend/src/services/file_service.py to add merge_resources method (combines shared + user resources with is_shared flag)

---

## Phase 3: User Story 1 - Self-Hosted Mode (P1)

**Goal**: Maintain backward compatibility - no authentication required, full access to shared resources

**Independent Test**: Deploy with DEPLOYMENT_MODE=self-hosted, access app without login, create/edit/delete resources in /data/shared/

### Implementation Tasks

- [X] T027 [US1] Update backend/src/middleware/auth_middleware.py to skip authentication when DEPLOYMENT_MODE=self-hosted
- [X] T028 [US1] Update backend/src/api/projects.py to use optional auth dependency (Depends(get_current_user) → Optional)
- [ ] T029 [US1] Update backend/src/api/boxes.py to use optional auth dependency
- [ ] T030 [P] [US1] Update backend/src/api/plugins.py to use optional auth dependency
- [ ] T031 [P] [US1] Update backend/src/api/provisioners.py to use optional auth dependency
- [ ] T032 [P] [US1] Update backend/src/api/triggers.py to use optional auth dependency
- [ ] T033 [P] [US1] Update backend/src/api/vms.py to use optional auth dependency
- [ ] T034 [US1] Update backend/src/services/project_service.py to use shared path when user_id is None
- [ ] T035 [P] [US1] Update backend/src/services/plugin_service.py to use shared path when user_id is None
- [ ] T036 [P] [US1] Update backend/src/services/global_provisioner_service.py to use shared path when user_id is None
- [ ] T037 [P] [US1] Update backend/src/services/global_trigger_service.py to use shared path when user_id is None

### Frontend Updates

- [ ] T038 [US1] Update frontend/src/index.html to skip login redirect when deployment mode is self-hosted (check via API endpoint)
- [ ] T039 [US1] Create frontend/src/js/deployment.js to fetch and cache deployment mode from backend

**Story 1 Complete**: ✅ Self-hosted mode working - no auth, full CRUD on shared resources

---

## Phase 4: User Story 2 - Email OTP Authentication (P1)

**Goal**: Public mode users authenticate via email OTP, get isolated user data

**Independent Test**: Deploy in public mode, request OTP, verify code, create user-specific project in /data/users/{user-id}/

### Backend - OTP Service

- [ ] T040 [US2] Create backend/src/services/otp_service.py with generate_otp method (6-digit random code using secrets module)
- [ ] T041 [US2] Add store_otp method to backend/src/services/otp_service.py (saves to /data/auth/otp-requests.json with email key)
- [ ] T042 [US2] Add verify_otp method to backend/src/services/otp_service.py (checks code, expiration, attempts)
- [ ] T043 [US2] Add cleanup_expired_otps method to backend/src/services/otp_service.py (removes entries with expires_at < now)

### Backend - Rate Limiting Service

- [ ] T044 [US2] Create backend/src/services/rate_limit_service.py with check_rate_limit method (token bucket algorithm, 5 requests/hour)
- [ ] T045 [US2] Add record_request method to backend/src/services/rate_limit_service.py (stores timestamp in /data/auth/rate-limits.json)
- [ ] T046 [US2] Add cleanup_old_records method to backend/src/services/rate_limit_service.py (removes entries older than 1 hour)

### Backend - User Service

- [ ] T047 [US2] Create backend/src/services/user_service.py with create_or_update_user method (creates profile.json in /data/users/{user-id}/)
- [ ] T048 [US2] Add get_user_by_id method to backend/src/services/user_service.py
- [ ] T049 [US2] Add get_user_by_email method to backend/src/services/user_service.py (scans /data/users/*/profile.json)
- [ ] T050 [US2] Add update_last_login method to backend/src/services/user_service.py

### Backend - Auth API Endpoints

### API Endpoints (Authentication)

**Dependencies**: T050-T054 require completion of T039-T049 (service layer must exist before API endpoints)

- [ ] T051 [US2] Create backend/src/api/auth.py with POST /api/auth/otp/request endpoint (rate limit check → generate OTP → send email → return success)
- [ ] T052 [US2] Add POST /api/auth/otp/verify endpoint to backend/src/api/auth.py (verify OTP → create/update user → generate JWT → return token + user)
- [ ] T053 [US2] Add GET /api/auth/me endpoint to backend/src/api/auth.py (validate JWT → return current user profile)
- [ ] T054 [US2] Add POST /api/auth/logout endpoint to backend/src/api/auth.py (instruct client to remove token)
- [ ] T055 [US2] Register auth router in backend/src/main.py (app.include_router(auth.router))

### Backend - Resource Isolation

- [ ] T056 [US2] Update backend/src/services/project_service.py to save to user directory when user_id provided (/data/users/{user_id}/projects/)
- [ ] T057 [P] [US2] Update backend/src/services/plugin_service.py to save to user directory when user_id provided
- [ ] T058 [P] [US2] Update backend/src/services/global_provisioner_service.py to save to user directory when user_id provided
- [ ] T059 [P] [US2] Update backend/src/services/global_trigger_service.py to save to user directory when user_id provided
- [ ] T060 [US2] Update backend/src/api/projects.py GET /api/projects to merge shared + user resources using file_service.merge_resources
- [ ] T061 [P] [US2] Update backend/src/api/plugins.py GET /api/plugins to merge shared + user resources
- [ ] T062 [P] [US2] Update backend/src/api/provisioners.py GET /api/provisioners to merge shared + user resources
- [ ] T063 [P] [US2] Update backend/src/api/triggers.py GET /api/triggers to merge shared + user resources

### Backend - Permission Enforcement

- [ ] T064 [US2] Update backend/src/api/projects.py PUT /api/projects/{id} to check is_shared flag and return 403 if true
- [ ] T065 [US2] Update backend/src/api/projects.py DELETE /api/projects/{id} to check is_shared flag and return 403 if true
- [ ] T066 [P] [US2] Update backend/src/api/plugins.py PUT /api/plugins/{id} to check is_shared flag and return 403 if true
- [ ] T067 [P] [US2] Update backend/src/api/plugins.py DELETE /api/plugins/{id} to check is_shared flag and return 403 if true
- [ ] T068 [P] [US2] Update backend/src/api/provisioners.py PUT /api/provisioners/{id} to check is_shared flag and return 403 if true
- [ ] T069 [P] [US2] Update backend/src/api/provisioners.py DELETE /api/provisioners/{id} to check is_shared flag and return 403 if true
- [ ] T070 [P] [US2] Update backend/src/api/triggers.py PUT /api/triggers/{id} to check is_shared flag and return 403 if true
- [ ] T071 [P] [US2] Update backend/src/api/triggers.py DELETE /api/triggers/{id} to check is_shared flag and return 403 if true

### Frontend - Login Page

- [ ] T072 [US2] Create frontend/src/views/login/login.html with email input form and "Send Code" button
- [ ] T073 [US2] Create frontend/src/views/login/login.js with Alpine.js component for OTP request (calls POST /api/auth/otp/request)
- [ ] T072a [US2] Add visual indicator to frontend/src/views/login/login.html showing greyed-out email OTP option when Mailgun is not configured (check via API endpoint or catch 503 error)
- [ ] T074 [US2] Add OTP code input field (6 digits) to frontend/src/views/login/login.html
- [ ] T075 [US2] Add code countdown timer to frontend/src/views/login/login.html (15-minute expiration visual indicator)
- [ ] T076 [US2] Add verify button handler to frontend/src/views/login/login.js (calls POST /api/auth/otp/verify, stores token in localStorage)
- [ ] T077 [US2] Add error message display to frontend/src/views/login/login.html for invalid/expired codes
- [ ] T078 [US2] Add rate limit error message display to frontend/src/views/login/login.html
- [ ] T079 [US2] Add loading state indicators to frontend/src/views/login/login.html during OTP request/verification

### Frontend - Authentication State

- [ ] T080 [US2] Create frontend/src/js/auth.js with checkAuth() function (calls GET /api/auth/me, returns user or null)
- [ ] T081 [US2] Add redirectToLogin() function to frontend/src/js/auth.js (only if DEPLOYMENT_MODE=public)
- [ ] T082 [US2] Update frontend/src/index.html to call checkAuth() on load and redirect unauthenticated users in public mode
- [ ] T083 [US2] Add Authorization header to all API requests in frontend/src/js/api.js (Bearer token from localStorage)

### Frontend - Resource UI Updates

- [ ] T084 [US2] Update frontend/src/components/resource-list.html to display is_shared indicator (icon or badge)
- [ ] T085 [US2] Update frontend/src/components/resource-list.html to hide edit/delete buttons when is_shared=true
- [ ] T086 [US2] Add Tailwind CSS styles for read-only resource indicators in frontend/src/styles/main.css

**Story 2 Complete**: ✅ Email OTP working - users can authenticate, create isolated resources, see shared resources as read-only

---

## Phase 5: User Story 4 - Session Persistence (P2)

**Goal**: Session tokens valid for 24 hours, users stay logged in across browser sessions

**Independent Test**: Log in, close browser, reopen within 24 hours, verify still authenticated

### Implementation Tasks

- [ ] T087 [US4] Verify backend/src/services/session_service.py sets JWT expiration to 24 hours (datetime.utcnow() + timedelta(hours=24))
- [ ] T088 [US4] Update frontend/src/js/auth.js to handle 401 responses (expired token) by redirecting to login
- [ ] T089 [US4] Add token expiration check to frontend/src/js/auth.js checkAuth() (decode JWT, compare exp claim to current time)
- [ ] T090 [US4] Test session persistence: log in, close browser, reopen after 6 hours, verify session still valid
- [ ] T091 [US4] Test session expiration: wait 25+ hours, verify redirect to login on next API call

**Story 4 Complete**: ✅ Sessions persist for 24 hours - users don't need to re-authenticate on browser reopen

---

## Phase 6: User Story 5 - Data Isolation (P1)

**Goal**: Enforce user data isolation - no cross-user access to private resources

**Independent Test**: Create two users (Alice, Bob), each creates resources, verify neither can access the other's data

### Backend - Cross-User Access Prevention

- [ ] T092 [US5] Update backend/src/services/project_service.py get_project method to check owner_id matches current user (return 404 if mismatch)
- [ ] T093 [P] [US5] Update backend/src/services/plugin_service.py get_plugin method to check owner_id matches current user
- [ ] T094 [P] [US5] Update backend/src/services/global_provisioner_service.py to check owner_id matches current user
- [ ] T095 [P] [US5] Update backend/src/services/global_trigger_service.py to check owner_id matches current user
- [ ] T096 [US5] Add owner_id field to all resource responses in backend/src/api/projects.py (null for shared, user_id for user resources)
- [ ] T097 [P] [US5] Add owner_id field to all resource responses in backend/src/api/plugins.py
- [ ] T098 [P] [US5] Add owner_id field to all resource responses in backend/src/api/provisioners.py
- [ ] T099 [P] [US5] Add owner_id field to all resource responses in backend/src/api/triggers.py

### Frontend - Visual Indicators

- [ ] T100 [US5] Add "Shared Resource" badge to frontend/src/components/resource-card.html when is_shared=true
- [ ] T101 [US5] Add tooltip to shared resource badge explaining read-only access
- [ ] T102 [US5] Update frontend/src/components/resource-list.html to visually separate shared vs user resources (different sections or borders)
- [ ] T103 [US5] Test cross-user isolation: verify user A cannot access user B's resources via direct API calls

**Story 5 Complete**: ✅ Data isolation enforced - users can only access their own resources + shared resources (read-only)

---

## Phase 7: User Story 3 - OIDC Social Login (P3)

**Goal**: Users can authenticate via Google, GitHub, or GitLab

**Independent Test**: Click "Continue with Google", complete OAuth flow, verify session created

### Backend - OIDC Service

### OIDC Service Implementation

- [ ] T104 [US3] Create backend/src/services/oidc_service.py with register_providers method (configures authlib OAuth for google, github, gitlab)
- [ ] T105 [US3] Add get_authorization_url method to backend/src/services/oidc_service.py (returns provider redirect URL)
- [ ] T106 [US3] Add exchange_code_for_token method to backend/src/services/oidc_service.py (exchanges auth code for access token)
- [ ] T107 [US3] Add get_user_info method to backend/src/services/oidc_service.py (fetches user profile from provider)

### Backend - OIDC Endpoints

- [ ] T108 [US3] Add GET /api/auth/oidc/{provider} endpoint to backend/src/api/auth.py (initiates OIDC flow, redirects to provider)
- [ ] T109 [US3] Add GET /api/auth/callback/{provider} endpoint to backend/src/api/auth.py (handles callback, exchanges code, creates user, returns token)
- [ ] T110 [US3] Add provider validation to OIDC endpoints (only allow google, github, gitlab)
- [ ] T111 [US3] Add error handling for OIDC provider unavailable (503 response)

### Frontend - OIDC Buttons

- [ ] T112 [P] [US3] Add "Continue with Google" button to frontend/src/views/login/login.html
- [ ] T113 [P] [US3] Add "Continue with GitHub" button to frontend/src/views/login/login.html
- [ ] T114 [P] [US3] Add "Continue with GitLab" button to frontend/src/views/login/login.html
- [ ] T115 [US3] Add OIDC button click handlers to frontend/src/views/login/login.js (redirect to /api/auth/oidc/{provider})
- [ ] T116 [US3] Update frontend/src/index.html to handle ?token= query parameter from OIDC callback (store in localStorage, redirect to main app)

### Configuration

- [ ] T117 [US3] Update backend/.env.example with OIDC provider credentials (OIDC_GOOGLE_CLIENT_ID, OIDC_GITHUB_CLIENT_ID, etc.)
- [ ] T118 [US3] Update compose-dev.yml and compose-prod.yml with OIDC environment variables

**Story 3 Complete**: ✅ OIDC working - users can authenticate via Google, GitHub, or GitLab

---

### Phase 8: Polish & Documentation (25 tasks)

**Dev-Time Data Preparation**

- [ ] T120 [US1] Move existing data to `/data/shared/` for shared resource preparation (one-time dev task: organize boxes/plugins/provisioners/triggers before first public deployment)

**Error Handling**

### Error Handling

- [ ] T119 [P] Add global exception handler to backend/src/main.py for HTTPException (consistent error response format)
- [ ] T121 [P] Add global exception handler for validation errors (422 responses with field details)
- [ ] T122 Add frontend error boundary in frontend/src/js/app.js to catch and display API errors

### Background Tasks

- [ ] T123 Create backend/src/tasks/cleanup.py with periodic cleanup task (expired OTPs, old rate limits)
- [ ] T124 Register cleanup task in backend/src/main.py using FastAPI BackgroundTasks (run every 5 minutes)

### Logging & Observability

- [ ] T125 [P] Add authentication event logging to backend/src/services/otp_service.py (OTP sent, verified, failed)
- [ ] T126 [P] Add permission denial logging to backend/src/services/permission_service.py
- [ ] T127 [P] Add rate limit hit logging to backend/src/services/rate_limit_service.py (log email when limit exceeded for abuse monitoring)
- [ ] T128 Add request logging middleware to backend/src/middleware/logging_middleware.py (log user_id, endpoint, status code)

### Documentation

- [ ] T129 Update README.md with deployment mode configuration instructions
- [ ] T130 Update README.md with authentication setup (Mailgun API key, OIDC credentials)
- [ ] T131 Create docs/AUTHENTICATION.md with detailed auth flow diagrams and troubleshooting

### Testing & Validation

- [ ] T132 Test self-hosted mode: deploy with DEPLOYMENT_MODE=self-hosted, verify no login required
- [ ] T133 Test email OTP flow: request code, verify delivery, enter code, verify session created
- [ ] T134 Test rate limiting: send 6 OTP requests rapidly, verify 6th is rejected
- [ ] T135 Test data isolation: create two users, verify each can only access own resources
- [ ] T136 Test shared resource read-only: attempt to edit shared resource, verify 403 error
- [ ] T137 Test session expiration: wait 24+ hours, verify redirect to login
- [ ] T138 Test OIDC flow: authenticate via Google/GitHub/GitLab, verify session created

### Deployment

- [ ] T139 Update compose-prod.yml to include all required environment variables
- [ ] T140 Create backend/data/shared/README.md explaining shared resources directory
- [ ] T141 Create backend/data/users/README.md explaining user-specific directories
- [ ] T142 Verify all endpoints documented in Swagger UI at http://localhost:8000/docs

---

## Dependencies & Execution Order

### Critical Path (Sequential)

1. **Phase 1 (Setup)** → Must complete before all other phases
2. **Phase 2 (Foundational)** → Must complete before user stories
3. **Phase 3 (US1)** + **Phase 4 (US2)** → Can run in parallel after Phase 2
4. **Phase 5 (US4)** → Depends on Phase 4 (needs JWT tokens from US2)
5. **Phase 6 (US5)** → Depends on Phase 4 (needs user context from US2)
6. **Phase 7 (US3)** → Depends on Phase 2 (needs session service) but independent of other stories
7. **Phase 8 (Polish)** → After all user stories complete

### User Story Dependencies

```
Phase 1 (Setup) ────────────────────────────┐
                                            │
Phase 2 (Foundational) ─────────────────────┤
                                            │
                    ┌───────────────────────┴──────────────┐
                    │                                      │
Phase 3 (US1: Self-Hosted) ──┐         Phase 4 (US2: Email OTP)
                              │                           │
                              │         ┌─────────────────┴────────────┐
                              │         │                              │
                              │   Phase 5 (US4: Sessions)   Phase 6 (US5: Isolation)
                              │         │                              │
                              │         └─────────────────┬────────────┘
                              │                           │
                              └───────────┬───────────────┘
                                          │
                         Phase 7 (US3: OIDC) ─────────┐
                                          │           │
                                    Phase 8 (Polish) ─┴──────────────
```

### Parallel Execution Opportunities

**Within Phase 2 (Foundational)**:
- T014-T017: All models can be created in parallel
- T018-T020: Services can be created in parallel

**Within Phase 3 (US1)**:
- T028-T031: API endpoint updates can be done in parallel
- T033-T035: Service updates can be done in parallel

**Within Phase 4 (US2)**:
- T055-T057: User directory service updates (plugins, provisioners, triggers)
- T059-T061: Resource merging API updates
- T064-T069: Permission checks in APIs (different files)

**Within Phase 6 (US5)**:
- T089-T091: Service owner_id checks
- T093-T095: API owner_id field additions

**Within Phase 7 (US3)**:
- T107-T109: OIDC button additions (different providers)

**Within Phase 8 (Polish)**:
- T114-T115: Exception handlers
- T119-T120: Logging additions

---

## Implementation Strategy

### MVP (Minimum Viable Product)

**Scope**: User Story 1 (Self-Hosted Mode) only
- **Tasks**: T001-T037 (37 tasks)
- **Deliverable**: Application works exactly as before, no authentication, backward compatible
- **Timeline**: 1-2 days
- **Test**: Deploy, create project, verify saved to /data/shared/

### Increment 1: Email OTP

**Scope**: User Story 2 (Email OTP Authentication)
- **Tasks**: T038-T082 (45 tasks)
- **Deliverable**: Public mode with email OTP, user isolation, shared resources
- **Timeline**: 3-5 days
- **Test**: Deploy in public mode, authenticate via email, create user resources

### Increment 2: Session Management

**Scope**: User Story 4 (Session Persistence)
- **Tasks**: T083-T087 (5 tasks)
- **Deliverable**: 24-hour sessions, auto-redirect on expiration
- **Timeline**: 1 day
- **Test**: Log in, wait several hours, verify still authenticated

### Increment 3: Data Isolation

**Scope**: User Story 5 (Cross-User Security)
- **Tasks**: T088-T098 (11 tasks)
- **Deliverable**: Enforced user isolation, visual indicators
- **Timeline**: 2 days
- **Test**: Two users, verify cannot access each other's resources

### Increment 4: Social Login

**Scope**: User Story 3 (OIDC)
- **Tasks**: T099-T113 (15 tasks)
- **Deliverable**: Google/GitHub/GitLab authentication
- **Timeline**: 2-3 days
- **Test**: Authenticate via each provider

### Final Polish

**Scope**: Phase 8 (Error handling, logging, docs)
- **Tasks**: T114-T135 (22 tasks)
- **Deliverable**: Production-ready deployment
- **Timeline**: 2-3 days

---

## Summary

**Total Tasks**: 142
**Breakdown by Phase**:
- Phase 1 (Setup): 15 tasks (T001-T015, added T006 Mailgun validation with logging)
- Phase 2 (Foundational): 12 tasks (T016-T027)
- Phase 3 (US1 - Self-Hosted): 13 tasks (T027-T040, note T027 was renumbered from duplicate)
- Phase 4 (US2 - Email OTP): 47 tasks (T041-T087, added T072a for OTP disabled UI, T074 for input field)
- Phase 5 (US4 - Sessions): 5 tasks (T088-T092)
- Phase 6 (US5 - Isolation): 11 tasks (T093-T103, includes T101-T102 that were T0101-T0103)
- Phase 7 (US3 - OIDC): 15 tasks (T104-T118)
- Phase 8 (Polish): 24 tasks (T119-T142, includes T120 dev-time data prep, T127 rate limit logging)

**Parallelizable Tasks**: 42 tasks marked with [P]

**Independent Test Criteria**:
- ✅ US1: Access app without login, full CRUD on shared resources
- ✅ US2: Email OTP flow, user resources in /data/users/{id}/, shared resources read-only
- ✅ US4: Session valid 24 hours, survives browser close
- ✅ US5: Users cannot access each other's resources
- ✅ US3: Social login via Google/GitHub/GitLab

**Recommended Approach**: Implement incrementally in order: MVP (US1) → Email OTP (US2) → Sessions (US4) → Isolation (US5) → OIDC (US3) → Polish
