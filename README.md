# TRAVESÍA — The World Is Yours to Explore

**The World Is Yours to Explore.**

TRAVESÍA brings destination discovery, trip planning, transport comparisons, shared group planning and travel companions into one interactive experience. The interface is built around an editorial destination-postcard hero, a clickable illustrated world atlas, a small expressive Bloop travel buddy, playful travel scenes and practical tools that carry a trip from its first idea to the final expense split.

## What is in the project

### Explore the world
- Full-width illustrated atlas with six clickable pins: Goa, Kyoto, Antarctica, Sydney, Rome and Bali. If online map tiles are unavailable, a bundled illustrated world map keeps discovery interactive without a GPU requirement.
- Destination postcards below the map; the selected-place preview stays inside the map so the map and destination details read as one experience.
- Destination imagery, descriptions and map-based exploration. Images are attributed or labelled as illustrative where appropriate.

### Plan the trip
- Trip Studio for editable itineraries, dates, budgets and trip preferences.
- Mobility tools for route and transport comparisons, with estimates clearly identified.
- Stays & Experiences for flights, rail, hotels, food, cafés, gaming cafés and activities.
- Route-aware flight comparisons via Google Flights, plus no-key ixigo Flights and KAYAK alternatives. Optional in-app offer search uses Amadeus only when server credentials are configured.
- Official IRCTC and IRCTC-listed ixigo hand-offs for train search/checkout. TRAVESÍA does not take payment or claim a ticket has been booked.
- Trip Pulseboard for provider-labelled weather, budget fit, travel context and locally saved snapshots.

### Bring the group together
- Squad Plans with shareable trip codes and separate editor access.
- Split Expenses with editable participant names, optional profile photos, expense categories, custom split participants, paise-accurate calculations and settlement suggestions showing who should pay whom.
- Thirteen distinct friend avatars: the six user-supplied Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione artworks appear first, followed by the seven original TRAVESÍA companions. New friends receive different characters by default; old generic traveller selections migrate automatically. Characters are unique within a trip of up to 12 friends, can be changed per person, persist locally and sync with shared trips.
- Local snapshots and CSV export for keeping a copy of the trip ledger.

### Make the world feel alive
- Bloop, a small expressive aqua octopus in a persistent bottom-right dock. Its eyes follow pointer movement, it blinks when tapped, and its chat opens in a compact popover.
- Companion Studio with seven original animated companions: Bloop, Sprout, Pip, Roo, Mira, Orbit and Paws.
- Portal Run, a playful floating-island and destination-portal challenge with animated travel postcards, collectibles and a saved best score.
- Storyboard Workshop for consent-based travel-video frame sampling and caption/storyboard drafting. It is optional and requires an account, FFmpeg/FFprobe and a configured visual-analysis provider.
- Cinematic scene banners on Trip Studio, Mobility, World Scene Lab, Companion Studio, Squad Plans, Saved Worlds, Split Expenses, Trip Pulseboard, Stays & Experiences and Account, each with its own imagery, scene selector, subtle camera parallax and a route-aware action. Discover and Explore are intentionally left unchanged.
- Cinematic page-entry transitions, scroll reveals, card tilt, pointer lighting and a scroll-progress line. Motion respects reduced-motion settings.
- On Discover, the floating postcards dynamically show the two destinations not currently selected. Clicking any postcard replaces the central image and copy; when Kyoto or Antarctica is selected, Goa becomes a floating one-click return option. The bottom selector remains available and the manual choice is protected from immediate auto-rotation.

## Brand and configuration compatibility

The final product name is **TRAVESÍA** and its tagline is **The World Is Yours to Explore.** Existing `CITYPULSEX_*` environment-variable names, database/session identifiers and API compatibility keys are intentionally retained so existing configuration and stored data continue to work. These are internal compatibility names, not the displayed product brand.

## Run it on Windows

1. Install Python 3.11 or newer.
2. Extract the ZIP and open the `TRAVESÍA` folder in VS Code.
3. Double-click `run_windows.bat`, or open PowerShell in the folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

4. The app reads `.env` automatically through `services/env_config.py`; `run_windows.bat` creates it from `.env.example` when missing. Set `CITYPULSEX_ADMIN_EMAIL` and a strong `CITYPULSEX_ADMIN_PASSWORD` for first admin provisioning. Keep `COOKIE_SECURE=0` only for local HTTP development.
5. Open **http://127.0.0.1:5000**. Authentication uses opaque random tokens stored hashed in SQLite; a Flask signed-session secret is not used.

## Run it on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

Then open **http://127.0.0.1:5000**.

## Optional service connections

- **Companion replies and Storyboard Workshop:** configure `LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL` on the server only. The built-in local guide works without credentials. The storyboard tool needs a vision-capable model and explicit consent before sending sampled frames.
- **Live flight offers:** configure authorised Amadeus credentials. Without them, TRAVESÍA uses external flight-search hand-offs rather than invented fares.
- **Maps and satellite imagery:** MapTiler is optional; NASA GIBS is the no-key, lower-detail satellite layer.
- **Weather:** MET Norway requires a real operator contact in its User-Agent. Open-Meteo's free API is restricted to permitted non-commercial use; review licensing before deployment.
- **Shared-trip persistence:** set `CITYPULSEX_DB` to durable storage on the host. Configure HTTPS and `COOKIE_SECURE=1` in production.

Never put provider secrets in frontend JavaScript or commit real secrets to Git. Setup details are in `docs/PROVIDER_SETUP.md` and `docs/PRODUCTION_DEPLOYMENT.md`.

## Verification

Run the local checks from the project root:

```bash
python -m pytest -q
node --test frontend/tests/*.test.cjs
python scripts/verify_glb_animation_browser.py
python scripts/verify_cinematic_refresh_browser.py
python scripts/verify_v7_character_postcards.py
python scripts/verify_booking_handoffs_browser.py
python scripts/verify_portal_run_browser.py
python scripts/verify_trip_pulseboard_browser.py
```

The browser suite checks the postcard hero, Bloop eye movement and chat, Friend 1's bundled travel portrait and all other crew avatars, the Portal Run travel scene, the illustrated map fallback, all six destination pins, the selected-place overlay, destination filters and mobile layout. The previous orbital globe was intentionally removed; this release does not need WebGL or a GPU for Explore. The full Flask HTTP/auth suite is mandatory: missing Flask/Werkzeug now stops collection with an actionable error instead of silently skipping nine tests. Run `verify_windows.bat` after installing dependencies in `requirements-dev.txt`.

## Honest operating boundaries

TRAVESÍA is a complete runnable project package, but some capabilities depend on outside services. IRCTC and ixigo links are provider hand-offs, not in-app ticket issuance. External airline, hotel and activity links do not constitute inventory held by TRAVESÍA. Live Amadeus in-app flight offers require credentials. Weather and map layers depend on providers and network access. The travel planner's sample budgets and route estimates are planning aids, not provider quotes. No user accounts, API keys or private reference videos are bundled.


## Booking workflow and world atlas
TRAVESÍA now provides no-key flight searches through Google Flights and ixigo Flights, and train searches through official IRCTC and IRCTC-listed ixigo. Actual checkout, provider login, payment and ticket confirmation remain on those provider sites. For an in-app flight inventory feed, configure Amadeus credentials; in-app ticket issuance additionally requires a production consolidator/issuer arrangement.

Explore uses a bundled illustrated atlas with clickable destination pins and an in-map place preview. Online Leaflet maps can enhance the experience when network tiles are reachable; the local atlas remains available without GPU hardware or map API credentials.


## Full verification on Windows
Double-click `verify_windows.bat`. It creates `.venv`, installs Flask/Werkzeug/Pytest/Playwright, installs Chromium, runs the complete Python API suite, Node expense tests, and browser tests for the visual refresh, companions, Portal Run, provider hand-offs and Trip Pulseboard. The current build container could not download Flask/Werkzeug because package-index DNS is blocked. The 15 Flask HTTP/auth tests are therefore pending and must pass on a network-enabled machine or the included GitHub Actions workflow before a production-verified release is declared.

## Provider onboarding and production approvals
See `docs/PROVIDER_ONBOARDING_PLAN.md` for the documented IRCTC affiliate/associate route, direct-PSP alternative and Amadeus production/ticket-issuance requirements. The `/api/providers/status` response exposes these gates. External booking hand-offs remain available while provider agreements are pending.


### Visual finish v4
Bloop is intentionally small at the bottom-right (48 px desktop / 42 px mobile, 38 px on very narrow phones). The mascot is a cute aqua octopus with pointer-following eyes, a click-look reaction and an eye-only blink. The homepage uses destination postcards, Portal Run is a tropical floating-island diorama, and Explore keeps its selected-place card on the map with six destination cards below. Friend 1 has a distinct bundled traveller portrait, and the crew image fallbacks are local assets.


## Friend characters and secondary-page motion
The Split Expenses picker includes 13 local character scenes. Used characters are disabled for the other friends in the same trip, and the server validates uniqueness when a shared trip is created or updated. The six supplied images preserve their original backgrounds inside uniform square stages. CSS scene motion animates the complete frame with slow camera drift, a depth-blurred copy of the same scene and a moving light sweep. This is not a generated Studio Ghibli restyle or frame-by-frame rig of the supplied characters. Public distribution should use artwork only where the project owner has the necessary rights or permissions.

The secondary pages each have a dedicated image-led travel scene with a next-scene selector, page-specific action, pointer-responsive perspective and an automatic scene change. The two discovery views, Discover and Explore, are intentionally not given these extra banners or layout changes.


## V7 — transparent friend cutouts and direct postcard selection

- The six images supplied for Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione are now bundled as transparent PNG cutouts. The picker and Split Expenses crew frames show the isolated figure rather than the original square/portrait photo background.
- Each cutout has its own CSS 2.5D idle motion and hover depth. These are animated transparent image cutouts, not newly rigged 3D meshes. The seven original TRAVESÍA companion characters retain their existing rigged GLB models and animation clips.
- Friend frames use full-colour art even when another friend has selected that character; the used character remains visibly marked and disabled to prevent duplicate assignment.
- Clicking the floating Kyoto or Antarctica postcard directly swaps that destination into the large central hero scene. Its image, title, copy, index and selected state update together; manual choice pauses automatic rotation briefly.
- Discover and Explore layouts were left unchanged.

The six supplied character images remain owner-provided artwork. Before redistributing the project publicly, confirm that you have the necessary rights or permissions for each character image.


## V8 — uniform animated character stages

- Every friend portrait and every choice in the picker now uses the same square stage (104×104 px desktop, 92×92 px compact screens).
- Transparent character art uses `object-fit: contain` within that stage, preserving the original proportions and keeping the image clear of names and buttons.
- All 13 characters have distinct idle motion; reduced-motion preferences are respected.
- The original seven TRAVESÍA 3D companion rigs remain available. Discover and Explore are unchanged.


## V10 — original-background animated character scenes

- Restored the six uploaded full-scene images (Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione) in place of the transparent cutouts. The original backgrounds are kept; Bulbasaur's source was trimmed only to remove the search-result footer around the white-background image.
- Each image stays whole inside the same 104×104 px desktop / 92×92 px mobile square stage with `object-fit: contain`. A blurred copy of the same scene fills the surrounding space without removing or replacing the original background.
- Added full-image camera drift, subtle color grading, a moving light sweep and distinct timing per character. These are CSS motion effects applied to the image and its background; they are not a Ghibli-style pixel-art transformation or newly rigged character animation.
- The seven original TRAVESÍA companions and their GLB rigs remain available. Unique 13-character assignment and shared-trip validation are unchanged. Discover and Explore remain untouched.


## Backend operations and GitHub release

- The Flask app initializes the SQLite schema at WSGI startup. Health checks verify the schema, and SQLite uses WAL mode plus a busy timeout.
- Registration/login and expensive public endpoints have persistent hashed rate-limit buckets. Authenticated logout and the storyboard upload require CSRF; API mutations reject cross-origin browser requests. Shared-trip updates require a separate editor token and the last-seen update timestamp.
- Create a verified SQLite backup with `python scripts/backup_database.py`; restore while the app is stopped with `python scripts/restore_database.py BACKUP.sqlite3 --confirm-replace`. See `docs/DATABASE_BACKUPS.md`.
- GitHub Actions runs the Flask API/security suite, frontend tests, Playwright browser regressions and a production Docker build. The full Flask integration suite is mandatory in CI.
- Follow `GITHUB_UPLOAD_GUIDE.md` for repository setup and `docs/PRODUCTION_DEPLOYMENT.md` for Render. Production requires owner-supplied secrets, a persistent disk, backups, provider credentials/approvals where applicable and a hosted smoke test.

The V11 backend release intentionally preserves the V10 `frontend/` tree; no frontend markup, styles, scripts, images or 3D assets were changed in this backend-hardening pass.

## V11 repository-ready backend hardening (frontend frozen)
V11 retains the V10 `frontend/` byte-for-byte and adds backend/operations hardening only: automatic SQLite schema initialization, persistent hashed rate limiting, CSRF-protected logout, same-origin mutation checks, login session rotation, conflict-safe shared-trip writes, verified database backup/restore tools, and GitHub Actions/Dependabot. See `docs/VERIFICATION_REPORT.md` for exact checks and outstanding gates; see `GITHUB_UPLOAD_GUIDE.md` to create and push your repository.

The current offline build runner completed 43 dependency-light Python tests, 27 Node tests and 55 browser checks. The 15 Flask HTTP/auth tests, full cinematic browser suite and Docker build are mandatory GitHub Actions gates and have not been claimed as locally passed. Live provider credentials/agreements and hosted deployment remain account-specific setup tasks.


Account registration currently creates member accounts without email verification, and self-service password reset/account recovery is not implemented. Do not open public registration for a commercial launch until an email delivery provider and account recovery flow are configured and independently tested.
