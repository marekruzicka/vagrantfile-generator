# Changelog

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

