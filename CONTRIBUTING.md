# Contributing

- Keep TRAVESÍA global, playful, accessible and transparent about data source and freshness.
- Use original or properly licensed character art/models; don't bundle unofficial Marvel/Disney/DC/Pokémon/etc. character assets.
- Keep the homepage guide still by default. Animate only after a clear action, and test actual rendered clip playback, foot/tentacle contact and reset/return-to-idle behaviour.
- Never fabricate live fares, bookings, weather, satellite source dates, model scores or provider readiness.
- Preserve server-side secrets, CSRF and shared-trip authorisation. Add regression tests for access-control changes.
- For video storyboard work, process only with consent, enforce upload/duration limits, use temporary storage and make clear that frames go to the configured provider. Never claim audio analysis or video rendering unless those features are actually present.
- Run Python tests, JavaScript syntax checks, expense-ledger tests and browser tests. Clearly report anything not run.

- The V11 backend-hardening release freezes the V10 frontend. Backend, deployment, security and test improvements must not modify `frontend/` without a separate product request. Verify this with the frontend SHA-256 manifest or review the Git diff.
- Add backend tests for database startup/migrations, rate limits, CSRF, same-origin checks, session revocation and shared-trip concurrency. Do not weaken tests to make a failing endpoint appear healthy.
- Run `python -m pytest -q tests`, `node --test frontend/tests/*.test.cjs` and the Playwright regression scripts before submitting a release.
