# Privacy

This project stores a minimal set of user data and uses only functional browser storage to provide the authenticated experience. This page explains what is stored, why, and how you can clear it.

## What we store about you (server-side)

- email: your email address (normalized to lowercase). Used as a unique identifier for your account.
- name: optional display name provided by the identity provider (OIDC) or derived from the email address when not provided.
- auth_provider: one of `email`, `google`, `github`, or `gitlab` indicating how you authenticated.

These fields are stored in the application backend. We do not store other personal information (no phone numbers, addresses, payment details, or additional profile fields) on the server.

We will never use these fields to contact you (we do not send marketing messages), and we will not provide your data to third parties under any scenario except where legally compelled.

## What we store in your browser (client-side)

- `auth_token` (localStorage): a JWT session token used to authenticate API requests. The token is short‑lived (24 hours by default) and is required to use the public (multi‑user) mode of the app.
- `user_profile` (localStorage): a cached copy of your basic profile (email, name, provider) used to render the UI faster.
- `vagrantfile-generator-config` (localStorage): your app preferences/configuration saved locally (UI settings, limits, etc.).
- `oauth_session` (HTTP cookie): short‑lived cookie used only during the OIDC (social login) redirect to maintain OAuth state (CSRF protection). It expires quickly (10 minutes by default).

All browser storage used by this application is strictly functional — there are no analytics, advertising, or tracking cookies included by this project.

## Why we store this information

- Server-side user profile: required to identify and persist each user's projects and preferences on the server.
- `auth_token` and `oauth_session`: required to authenticate you and to complete the login flow. These are necessary for the service to work.
- `user_profile` and `vagrantfile-generator-config`: saved to improve UI responsiveness and remember your preferences.

## Retention

- Server-side `profile.json` is retained until the user is removed (administrator action) or the deployment's data retention policy is applied. Session JWT tokens expire automatically (24 hours by default).
- Browser storage persists until the token expires, the user logs out, or the user clears their browser storage.

## Your controls

- To end your session: use the app `Logout` control which clears the token and profile from your browser.
- To remove local preferences: clear your browser site data or use the `Clear storage` option in the app settings (if available).
- To request deletion of server-side profile data, contact the site administrator for the deployment.

## Third-party providers

When you use social login (Google, GitHub, GitLab) you are redirected to the provider. Those providers may set their own cookies while you interact with them. This project does not set any tracking cookies and does not include analytics or advertising libraries. You should consult the identity provider's privacy policy for details about cookies they set on their domains.

## Changes to this notice

This page may be updated over time; the project aims to keep customer data handling minimal and transparent.
