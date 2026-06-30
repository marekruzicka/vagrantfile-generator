# Changelog

## [0.5.3] - 2026-06-30

### Bug Fixes
* fix(helm): sync chart appVersion to 1.16.1

## [0.5.2] - 2026-06-30

### Bug Fixes
* fix(helm): improve landing page handling and SPA fallback

## [0.5.1] - 2026-06-30

### Bug Fixes
* fix(helm): sync chart appVersion to 1.16.0

## [0.5.0] - 2026-06-27

### Features
* feat: version API endpoint, footer unification, env var injection

### Bug Fixes
* fix(helm): sync chart appVersion to 1.15.0

## [0.4.5] - 2026-06-26

### Bug Fixes
* fix(helm): sync chart appVersion to 1.14.5

## [0.4.4] - 2026-06-26

### Bug Fixes
* fix(helm): sync chart appVersion to 1.14.4

## [0.4.3] - 2026-06-26

### Bug Fixes
* fix(helm): sync chart appVersion to 1.14.3

## [0.4.2] - 2026-06-25

### Bug Fixes
* fix: update image tag handling for backend and frontend deployments to follow appVersion by default

## [0.4.1] - 2026-06-25

### Bug Fixes
* fix(helm): sync chart appVersion to 1.14.2

## [0.4.0] - 2026-06-19

### Features
- feat(helm): support existingClaim and static PV binding

### Fixed
- fix: retry helm-semver after deleting stale tag
- fix: retry helm-semver release with PAT for git push
- fix: retry helm-semver release with GHCR auth
- fix: trigger initial helm-semver chart release
- fix: Mailgun EU region endpoint - add configurable MAILGUN_API_URL

