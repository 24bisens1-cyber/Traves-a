# Security and deployment notes

TRAVESÍA uses Werkzeug password hashing, random opaque server-side session tokens stored only as hashes in SQLite, HttpOnly session cookies, SameSite=Lax, optional Secure cookies, CSRF validation for authenticated state-changing actions, same-origin checks for API mutations, persistent IP/account rate-limit buckets, member/admin roles, and high-entropy shared-trip read codes plus separately hashed editor tokens. Shared-trip updates require an editor token and the last-seen version value; stale writes return HTTP 409. The server sets common security headers and never exposes provider secrets to browser JavaScript.

## Required production configuration

- Serve only over HTTPS and set `COOKIE_SECURE=1`.
- Set `CITYPULSEX_ENV=production` and `CITYPULSEX_TRUST_PROXY=1` only behind exactly one trusted reverse proxy that overwrites forwarded IP/protocol headers. Leave proxy trust disabled for direct/local runs.
- Configure `CITYPULSEX_DB` on a durable disk or use the included Render persistent-disk Blueprint. Take encrypted backups and test restore; a persistent disk is not a backup.
- Set a new `CITYPULSEX_ADMIN_EMAIL` and unique `CITYPULSEX_ADMIN_PASSWORD` (16+ characters) before the first production boot. The bootstrap creates the admin only if that address does not already exist; it does not silently promote a pre-existing member account.
- Configure secrets through the host's secret manager. Never commit `.env`, SQLite databases, exports, user uploads, provider keys or passwords.
- Keep rate limiting enabled. It is stored in SQLite so limits persist across application restarts. Also configure edge/WAF rate limiting for high-traffic deployments; app-level IP limits are a fallback, not a DDoS service.

## Security behaviours covered by tests

- Registration creates member accounts only; admin provisioning is server-side.
- Login and registration have persistent rate limits. Login rate limits are applied per IP and per normalized account identifier.
- Session cookies are HttpOnly and SameSite=Lax; production must set Secure.
- Logout and the authenticated storyboard upload require a matching CSRF token.
- API mutations reject cross-site Fetch Metadata and mismatched Origin headers when browsers provide them.
- Shared-trip read codes are high-entropy and read-only. Writes require a separate high-entropy editor token. The editor token is returned only at creation, is stored as a hash, and is never returned by the read endpoint.
- Shared-trip updates require `expected_updated_at`; conflicting writes return HTTP 409 rather than silently overwriting another collaborator.
- Request bodies are capped at 25 MB. Storyboard uploads require an account, CSRF token and explicit consent, are duration-limited, sampled with FFmpeg in a temporary directory and deleted when the request ends.

## Known account lifecycle limitations

Email verification and self-service password reset/account recovery are not implemented. Registration currently creates a member account immediately. Before opening registration to the public, integrate an approved transactional email provider, add short-lived one-time verification/reset tokens with hashed storage and CSRF-safe flows, and add independent tests. Do not send reset links or passwords through application logs.

## Before a public commercial launch

- Independently review authentication, session lifecycle, rate-limit tuning, account recovery, privacy/data retention, threat model, database permissions and incident response.
- Configure edge rate limiting, logging/monitoring, alerting, backups and a restore exercise.
- Test two independent users and two browser profiles, viewer/editor restrictions, stale-update conflicts, login/logout, CSRF, session expiry and database persistence after restart.
- Configure only licensed/approved providers. Show live prices, booking status, weather and imagery only when returned by a successful provider response with source/time metadata. Never present estimates or hand-offs as completed bookings.
- For the video storyboard endpoint, request consent before frames are sent to the configured AI provider. Provider data-processing terms apply; audio is not analysed.
- Confirm you have the legal rights to distribute all uploaded character artwork, brand names, photographs, music, models and other assets. The repository's code license does not grant rights to third-party characters or media.

## Reporting a vulnerability

Do not post secrets, session cookies, editor tokens, personal data or an exploitable vulnerability in a public issue. Use GitHub's private vulnerability reporting for the repository owner, or contact the maintainer privately before disclosure.
