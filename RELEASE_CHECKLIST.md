> **Branding note (7 November 2026):** This package is the TRAVESÍA rebrand of the V11 GitHub-ready release. The product-facing identity and documentation are updated; original feature behavior and internal `CITYPULSEX_*` compatibility keys are retained. The historical V11 frontend-freeze checks describe the source V11 release before this brand-only update.

# TRAVESÍA V11 Release Checklist

## Frontend freeze
- [x] Keep the V10 frontend unchanged for this release.
- [x] Compare every file under `frontend/` against the V10 source archive using SHA-256; all files match.
- [x] Preserve Discover, Explore, destination postcards, character art, companion rigs and every existing page.

## Backend and data integrity
- [x] Initialize/migrate the SQLite schema at WSGI startup.
- [x] Check required schema tables in `/api/health`.
- [x] Enable SQLite foreign keys, WAL mode and busy timeout.
- [x] Add persistent hashed rate-limit buckets for authentication and expensive endpoints.
- [x] Require CSRF for logout and reject cross-origin browser API mutations.
- [x] Rotate prior login session tokens.
- [x] Require an expected update timestamp for shared-trip writes and return 409 on stale versions.
- [x] Add SQLite online backup, guarded restore and integrity checks.
- [x] Add tests for backup/restore and backend security rules.

## Automated checks executed in this runner
- [x] Dependency-light Python tests: 43 passed.
- [x] Node frontend unit tests: 27 passed.
- [x] Browser booking hand-offs: 10 passed.
- [x] Browser Portal Run: 7 passed.
- [x] Browser companion GLB animations: 14 passed.
- [x] Browser Trip Pulseboard: 9 passed.
- [x] Focused browser postcards/character scenes: 15 passed.
- [x] Python compilation and YAML parsing.
- [x] Verify frontend hashes are unchanged.

**Completed local test cases: 125** (43 Python + 27 Node + 55 Chromium). The 15 Flask HTTP/auth tests, full cinematic browser run and Docker build remain CI gates.

## CI gates — must pass after GitHub push
- [ ] Run all 58 Python tests, including 15 Flask HTTP/auth integration tests.
- [ ] Run the full cinematic browser suite; local execution exceeded this runner's time limit.
- [ ] Build the production Docker image.
- [ ] Confirm Dependabot and GitHub Actions checks are enabled for the repository.

## Provider and live-service gates
- [ ] Configure and verify Amadeus test credentials before enabling in-app flight offers.
- [ ] Obtain production ticket-issuer/consolidator approval before issuing flight tickets.
- [ ] Complete IRCTC-approved PSP/affiliate arrangements before enabling any in-app rail booking.
- [ ] Configure an authorised LLM endpoint before enabling hosted companion/storyboard analysis.
- [ ] Configure and verify the map/weather providers and their terms, attribution, rate limits and contact details.

## Hosting and public release
- [ ] Push to a private GitHub repository first; inspect staged files and keep `.env`, databases, WAL/SHM files, uploads, exports and backups out of Git.
- [ ] Verify redistribution rights for user-supplied Pokémon/Marvel/Spider-Man/Harry Potter character artwork before any public repository release. MIT does not grant those rights.
- [ ] Provision the Render service using `render.yaml`; configure production secrets in the host secret manager.
- [ ] Verify HTTPS, secure cookies, trusted proxy configuration and durable database storage.
- [ ] Run deployed smoke checks, two-account authorization tests, persistence/restart tests and a backup restore.
- [ ] Complete an independent security/privacy review before commercial launch.
