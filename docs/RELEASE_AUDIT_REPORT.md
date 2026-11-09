# TRAVESÍA V11 release audit — 7 November 2026

- **Product identity:** TRAVESÍA — The World Is Yours to Explore. Name retained.
- **Frontend freeze:** Every file in `frontend/` is SHA-256 identical to V10. This backend/operations release changes no frontend files.
- **Database boot:** SQLite schema creation and additive migrations run during WSGI app import/startup; health status checks the required tables.
- **Authentication:** Werkzeug password hashing; random opaque server-side session tokens stored only as hashes; 14-day session expiry; same-site cookies; login rotation; member-only self-registration; admin provisioning via server environment.
- **Mutation security:** CSRF-protected logout/storyboard upload, same-origin API mutation checks, separate shared-trip editor token, mandatory expected update version and 409 stale-write response.
- **Abuse controls:** Persistent hashed fixed-window rate-limit buckets cover login, registration, shared-trip endpoints and selected expensive APIs. Keep edge/WAF limits enabled for public traffic.
- **Data operations:** SQLite WAL, foreign keys, busy timeout, verified online backup and guarded restore scripts. Render Blueprint mounts a durable data path; backups remain a separate operational requirement.
- **External providers:** no-key flight and rail hand-offs remain available. Live Amadeus offers, in-app ticket issuance, approved IRCTC flows, LLM replies/storyboards and licensed map/weather sources require owner-provided accounts, keys and/or agreements.
- **Repository:** GitHub Actions workflow, least-privilege read token permissions, Dependabot, `.gitignore`, `.gitattributes`, Docker configuration, Render Blueprint and upload guide included.

## Checks returned successfully in this build environment

- 43 dependency-light Python tests passed.
- 27 Node tests passed.
- 55 Chromium regression checks passed across focused postcards/character scenes (15), booking hand-offs (10), Portal Run (7), original companion GLB animations (14) and Trip Pulseboard (9).
- Python compilation, YAML parsing and frontend hash comparison passed.

## Gates that remain open

- **Flask HTTP/auth integration:** 15 tests are present and mandatory but were not executable here because Flask/Werkzeug could not be downloaded from PyPI in this network-isolated runner. The GitHub Actions backend job installs `requirements-dev.txt` and runs the entire 58-test Python suite; it must turn green after push.
- **Cinematic browser job:** the full cinematic browser script hit this runner's time limit. It is included in GitHub Actions and is not counted as passed.
- **Docker image build:** Docker is not installed in this runner. The included workflow builds the production image on GitHub Actions.
- **Hosted deployment:** no Render workspace/domain/production secrets were provided. Configure `render.yaml`, then run the deployed smoke test.
- **Commercial provider operation:** credentials, partner approval and ticket-issuer agreements cannot be created by source code. Configure only services/accounts that the owner is authorised to use.
- **Security/product completeness:** account email verification and account recovery are not implemented; commission an independent security/privacy review and establish account recovery, data retention and incident response before public commercial launch.

## Distribution note

The six user-supplied images depict third-party entertainment characters. The repository is documented for private setup first; confirm the rights needed for redistribution before switching the GitHub repository to public. The project MIT license does not grant rights to those characters or images.
