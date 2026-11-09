# Production deployment

1. Push this release to a repository owned/authorised by you; the project bundle does not deploy itself.
2. Provision the configured Render service from `render.yaml`. It uses Docker, a persistent disk mounted at `/app/instance`, HTTPS, `COOKIE_SECURE=1`, and one trusted Render proxy hop. The application initializes/migrates the SQLite schema before Gunicorn starts accepting traffic. Render persistent disks require a paid compute plan; confirm the current plan and cost in your workspace before applying the Blueprint.
3. Set `CITYPULSEX_ADMIN_EMAIL`, a unique `CITYPULSEX_ADMIN_PASSWORD` (16+ characters) and `CITYPULSEX_CONTACT_EMAIL` or a public `CITYPULSEX_CONTACT_URL` in the host's secret/environment settings. Set provider credentials only when your account is authorised. Never commit actual secrets. The application uses hashed opaque auth tokens rather than Flask signed-cookie sessions, so `CITYPULSEX_SECRET_KEY` is not used.
4. Optional: set `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`, `MAPTILER_API_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`. Keep the LLM endpoint HTTPS and use a model endpoint that supports vision if you want clip storyboards. Docker installs FFmpeg/FFprobe.
5. Verify `/api/health`, `/api/capabilities`, `/api/providers/status`, `/api/maps/config`, `/glb-viewer.js`, `/assets/companions3d/bloop.glb`.
6. Run `python scripts/smoke_deployed.py https://YOUR-SERVICE.onrender.com`, then full pytest/browser checks from GitHub Actions. Test two independent accounts, unauthorized shared-trip edit, valid editor token, stale edit conflict, login/logout/CSRF, rate limits, database persistence after restart and upload error/success paths.
7. Inspect provider attribution, cache timestamps, failure behavior and each relevant provider's account limits/terms. A successful build is not proof a live service is returning current data.


## Persistent data and operational controls

- The WSGI app initializes the schema on import/startup and applies additive SQLite migrations. `/api/health` checks for the required tables.
- SQLite is configured for WAL mode and a 15-second busy timeout. The Render Blueprint uses one web instance and a persistent disk; do not scale multiple independent instances against the same SQLite file.
- Rate-limit buckets are persisted in SQLite and store only hashes of their identity inputs. Keep edge/WAF rate limiting enabled for public traffic.
- Set `CITYPULSEX_TRUST_PROXY=1` only behind the configured trusted Render proxy hop. Do not enable it for a direct public Gunicorn/Docker bind.
- Back up before releases and periodically using `python scripts/backup_database.py`. Restore only while the web service is stopped; see `docs/DATABASE_BACKUPS.md`.
- Configure encrypted off-host backups and a recovery point objective. A Render persistent disk protects against ephemeral container restarts but is not a substitute for backups.


## Account lifecycle launch gate

The current authentication scope includes registration, login, logout, server-side sessions and roles. It does not include email ownership verification or a self-service password reset/recovery flow. Before public registration, integrate a transactional email service, implement short-lived hashed one-time tokens and expiry/replay protection, add the frontend flows in a separately authorised frontend release, and test email delivery and token misuse. This V11 backend-only release deliberately does not change the frozen frontend.
