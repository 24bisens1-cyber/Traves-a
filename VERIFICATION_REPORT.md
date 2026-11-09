# TRAVESÍA V11 — Backend hardening and Git-ready verification

**Release:** V11 backend / deployment preparation
**Date:** 7 November 2026
**Frontend baseline:** V10, byte-for-byte unchanged in this release

## Scope and frontend preservation

This release intentionally changes backend, operations, tests, documentation and repository configuration only. The `frontend/` directory was SHA-256 compared against the V10 source archive before packaging; every frontend file matched exactly. No HTML, CSS, JavaScript, character artwork, 3D model or frontend layout was modified.

## Backend and operations work included

- Initialize and migrate the SQLite schema automatically when the WSGI application starts; the health endpoint checks for required tables.
- Enable SQLite foreign keys, WAL mode and a 15-second busy timeout.
- Add persistent fixed-window request limits for registration, login, shared-trip APIs, flight search, companion chat and storyboard requests. Rate-limit identities are hashed before storage; raw IP/email values are not written to the bucket table.
- Require CSRF validation for authenticated sign-out and reject cross-origin browser API mutations.
- Rotate the previous session token on successful login.
- Require `expected_updated_at` for shared-trip edits, serialize writes and return a conflict rather than overwriting newer data.
- Apply production cookie security defaults, HSTS on HTTPS requests and additional response headers. Trust forwarded client/protocol headers only when `CITYPULSEX_TRUST_PROXY=1` is explicitly enabled behind the configured single proxy.
- Add SQLite online-backup and guarded restore tools, integrity checks and backup/restore tests.
- Include a GitHub Actions workflow with mandatory Flask/API tests, browser regressions, frontend syntax/unit tests and a production Docker build; add Dependabot configuration and a Git upload guide.
- Correct test dependency installation so Pillow is present in development/CI requirements.

## Checks that completed in this build environment

| Suite/check | Result |
|---|---:|
| Dependency-light Python tests, including database backup/restore | 43 passed |
| Node frontend unit tests | 27 passed |
| Chromium booking hand-off checks | 10 passed |
| Chromium Portal Run checks | 7 passed |
| Chromium original companion GLB checks | 14 passed |
| Chromium Trip Pulseboard checks | 9 passed |
| Chromium focused postcards/character scene checks | 15 passed |
| Python compilation | Passed |
| Render, Docker Compose and GitHub Actions YAML parsing | Passed |
| Frontend SHA-256 comparison against V10 | Exact match; no frontend files changed |

**Completed test cases: 125** (43 Python + 27 Node + 55 returned Chromium checks). Compilation, YAML parsing and frontend hash comparison are additional checks, not included in that total.

## Gates not executed or not completed here

1. **Flask HTTP/auth integration:** 15 tests are present and mandatory, but were not executable in this isolated runner because Flask/Werkzeug could not be downloaded from PyPI (package-index DNS unavailable). They are not marked as passed or skipped. The GitHub Actions workflow installs `requirements-dev.txt` and runs `python -m pytest -q tests`; this gate must turn green after you push the repository.
2. **Cinematic full-browser suite:** `scripts/verify_cinematic_refresh_browser.py` exceeded this runner's time limit. It is included in the GitHub Actions browser job. A timeout is not counted as a pass.
3. **Docker image build:** Docker is not installed in this runner. The workflow builds the production Docker image on GitHub Actions.
4. **Hosted deployment and smoke test:** no Render account/workspace, domain or production secrets were supplied, so no external service was deployed. Use `render.yaml`, then run `python scripts/smoke_deployed.py https://YOUR-SERVICE.onrender.com`.
5. **Live provider verification:** no Amadeus, MapTiler or hosted LLM credentials were supplied. Flight/rail external search hand-offs remain available; in-app provider feeds remain visibly unavailable until configured and authorised. Ticket issuance still requires provider/consolidator approval.

## Required actions before a public production launch

- Push this repository to a GitHub repository you control and wait for all Actions jobs to pass. Fix any CI failures before tagging a release.
- Keep the repository private until you have verified redistribution rights for the six supplied character-scene images and any other third-party media. The MIT license covers original project code only; it does not grant rights to those characters or images.
- Configure Render secrets and a durable persistent disk, HTTPS, backups and monitoring. Test restart persistence and a restore before launch.
- Obtain and configure the provider credentials/agreements needed for any in-app commercial travel inventory or ticketing.
- Perform an independent production security/privacy review and test two separate user accounts against the deployed service.

This report distinguishes code implemented in the package from checks that could not run in this environment and approvals that only external providers can grant.

## Account lifecycle limitation

Registration currently creates a member account without email verification. Self-service password reset/account recovery is not implemented. These require a transactional email provider and additional frontend flows; they remain launch gates and are intentionally not added in this frontend-frozen release.
