## TRAVESÍA brand update — 2026-11-07
- Renamed the final product identity to **TRAVESÍA — The World Is Yours to Explore.**
- Updated the browser title, app brand lockup, help label, user-facing copy, README, setup guides and project documentation.
- Renamed the extracted project folder and globe-mark asset filename.
- Preserved the existing frontend features, page structure, API behavior, stored data identifiers and `CITYPULSEX_*` configuration keys for compatibility.

# Changelog

## TRAVESÍA Full Lifelike Release — 2026-10-28
- Set Bloop, an original plush-octopus GLB with 12-joint skinning and seven clips, as the homepage's full-body assistant. The homepage stays still until interaction; destination selection runs Walk/Turn/Wave.
- Added recent-turn context to server-side AI chat and a consent-gated authenticated visual-video storyboard endpoint/UI, using temporary FFmpeg keyframes and optional vision-capable provider.
- Removed Civic Pulse/Nagpur module, legacy routes, duplicated API starter, civic datasets/scripts/tests and stale civic documentation. World Scene Lab stays travel/scenario focused.
- Kept Portal Run, global world map, companion studio, Trip Pulseboard, travel hand-offs and secure shared trips.
- Added/updated release contracts and browser animation verification; Docker image installs FFmpeg for optional storyboard analysis.
- External provider connectivity and production deployment remain explicitly dependent on configuration and network access.

## TRAVESÍA Cinematic Refresh — 2026-11-06
- Connected the homepage canvas to the procedural WebGL globe renderer and surfaced six selectable destination hotspots (Goa, Kyoto, Antarctica, Sydney, Rome and Bali).
- Added a layered cinematic globe stage with orbit rings, ambient particles, floating scene labels and a responsive atmospheric light field, matching the supplied visual references' depth and motion.
- Added page-entry transitions, scroll reveals, pointer-lit card tilt and a scroll progress indicator across the product. Reduced-motion preferences remain respected.
- Optimised the globe's render loop to cap pixel density and update at a controlled frame cadence.
- Refined customer-facing copy so the interface reads like a travel product rather than an AI demo; technical provider and privacy requirements remain documented accurately.
- Revalidated 19 Python contract/provider tests, 8 Node ledger tests, 14 companion animation checks, 9 landing-scene smoke checks, 7 Portal Run checks and 9 Trip Pulseboard checks.


## 2026-11-06 — Booking fallbacks and globe compatibility
- Added a textured interactive Canvas2D globe fallback for browsers/CI environments that block WebGL; hotspots, drag rotation and destination selection remain available.
- Expanded the browser test to verify rendered pixels, pointer rotation, hotspot actions and optional required-WebGL mode.
- Added route/date Google Flights plus ixigo flight-search hand-offs, and official IRCTC plus IRCTC-listed ixigo train-search/checkout hand-offs.
- Clarified provider-side authentication, payment, ticket issuance and the production partner approvals required for native ticketing.
- Exposed Google Flights, ixigo Flights, official IRCTC and IRCTC-listed ixigo in the backend capability/provider-status responses.
- Added reproducible Windows and GitHub Actions full-test paths; this container passed 22 dependency-light Python, 8 Node and 55 Chromium checks (85 total). The nine Flask HTTP/auth tests are included but await dependency installation in CI/local package-enabled Python.


## TRAVESÍA Visual Direction Update — 2026-11-06
- Replaced the black orbital landing globe and science-style Portal Run presentation with a photo-led destination postcard hero and a floating-island travel scene.
- Reduced Bloop to a compact bottom-right aqua octopus companion (48 px desktop / 42 px mobile; 38 px on narrow phones) with pointer-following pupils, blink interaction and a small chat popover.
- Rebuilt Explore as a wide illustrated atlas: selected-place preview inside the map, six destination postcards below, working category filters and a bundled offline map fallback.
- Updated contract tests, Windows verification, CI workflow and release documentation to reflect the current interface; no WebGL/GPU-only requirement remains for Explore.
- Latest visual refresh verification: 24 Python tests passed / one Flask integration module skipped, 8 Node tests passed and 64 Chromium browser checks passed.


## TRAVESÍA Cinematic Finish v3 — final polish
- Reduced Bloop to a transparent 48 px desktop / 42 px mobile tap target (38 px on narrow phones), removed the halo and status badge, and kept the original cute aqua octopus artwork. Pointer-following pupils, click-look, eye-only blink and subtle tentacle waves remain.
- Added cursor-led camera depth to the tropical Portal Run diorama while retaining the playable seven-charm flow and respecting reduced-motion settings.
- Cache-busted the stylesheet so a browser does not reuse the previous oversized companion or orbital-scene styling.

## 2026-11-07 — Setup, crew portrait and dynamic-scene hardening
- Replaced Friend 1's broken default `bloop.webp` reference (the file was not present) with a new original local traveller portrait, `frontend/assets/companions/friend-one.svg`.
- Added explicit local default portraits for all four initial Split Expenses participants and a safe local-image fallback for missing or invalid profile-photo URLs. Browser verification now waits for all portraits to load and checks their natural image dimensions.
- Added a dependency-free `.env` reader and load it before Flask reads application configuration; the setup scripts create `.env` from `.env.example` when needed.
- Added a local environment preflight, VS Code run/debug tasks, and a clearer first-run/full-verification guide.
- Changed Flask HTTP/auth tests to fail with an actionable dependency message instead of silently skipping when Flask/Werkzeug are unavailable.
- Strengthened the visual browser check to verify actual scroll-linked artwork movement and the loaded Friend 1 portrait.
- Re-ran 29 Python tests (excluding the Flask HTTP/auth module), 8 Node expense tests and 69 Chromium browser checks successfully. The nine Flask HTTP/auth tests remain pending because the container cannot reach the package index; the included Windows and GitHub Actions paths install and run them on a network-enabled environment.


## TRAVESÍA Friend Character Library & Secondary Page Motion — 2026-11-07
- Added six locally bundled portraits cropped from the user's supplied references: Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione. Kept all seven original TRAVESÍA companions.
- Added a 13-option friend character picker. Each friend can choose a character; assignments are unique across a 1–12 person crew, used characters are locked for other friends, and assignments persist across refreshes and shared-trip sync.
- Added character-specific idle animation styles and a shared-trip API allowlist/duplicate check.
- Added individual cinematic travel-scene banners with scene cycling, pointer parallax and context-specific actions on Trip Studio, Mobility, World Scene Lab, Companion Studio, Squad Plans, Saved Worlds, Split Expenses, Trip Pulseboard, Stays & Experiences and Account. Discover and Explore are intentionally unchanged.
- Fixed duplicate in-flight Wikipedia lookup handling so offline Explore enrichment returns the local fallback without an uncaught browser promise rejection; the Explore UI and layout are unchanged.
- Updated CI and Windows verification to run both frontend Node test files.
- Verification: 15/15 Node tests and 67/67 Chromium browser checks passed; the nine Flask HTTP/auth tests remain pending because this container cannot resolve the Python package index.


## 2026-11-07 · Destination postcards and friend character fix

- Fixed Flask static routes for `friend-characters.js`, `cinematic.js`, and `cinematic.css`; these missing routes caused the generic friend-avatar fallback and removed cinematic page styling/motion in the real app.
- Kyoto and Antarctica floating postcards are now keyboard-accessible buttons. Clicking either transitions the centre postcard image and title to that destination. Manual selection is held for 18 seconds before the ambient rotation resumes.
- Friend avatar defaults now use the six user-supplied character artworks first (Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione), followed by the seven original TRAVESÍA companions. The retired generic traveller is removed from the picker and old saved `traveller` values migrate to unique defaults.
- Added regression tests for Flask static asset routes, postcard-to-centre transitions, character defaults and legacy migration.
- Removed the interim generic traveller portrait asset; the friend-character picker now uses only the six supplied character artworks and the seven original TRAVESÍA companions.
- Final validation: 34 dependency-light Python tests, 16 Node tests and 110 browser regression checks passed (70 cinematic/homepage, 14 companion rigs, 10 booking hand-offs, 7 Portal Run and 9 Trip Pulseboard). The separate nine-test Flask HTTP/auth module remains pending because Flask/Werkzeug are not installed in this offline runner.


## TRAVESÍA V7 — Transparent character cutouts & clickable postcard scenes — 2026-11-07
- Replaced the six square RGB avatar files with tightly cropped transparent PNG cutouts derived from the supplied Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione images.
- Updated Split Expenses friend frames and the character picker to use `object-fit: contain`, transparent backgrounds, no circular clipping and full-figure presentation.
- Added per-character 2.5D idle movement, subtle tilt, depth shadows and full-colour locked states. The six cutouts are not represented as newly rigged 3D meshes; the seven original TRAVESÍA companions retain their existing animated GLB rigs.
- Added descriptive alt text for each cutout and retained the unique 13-choice/12-friend assignment rules.
- Verified direct clicks on both floating Kyoto and Antarctica postcards with browser pointer clicks; each swaps the centre image, heading, description and active state without requiring the bottom selector.
- Discover and Explore were not redesigned or repositioned.
- V7 verification: 38 dependency-light Python tests, 17 Node tests and 48 Chromium browser checks passed (103 executed checks). Nine Flask HTTP/auth tests remain pending until Flask/Werkzeug can be installed in a network-enabled environment.


## TRAVESÍA V8 — uniform animated character stages — 2026-11-07
- Replaced the uneven portrait layout with one consistent square character stage for every friend tile and every character-picker option: 104×104 px desktop and 92×92 px at compact widths.
- Set all character art to the same 90%-of-stage contain fit so tall and wide figures stay inside the frame without being stretched or clipped.
- Added individual idle motion to all 13 choices: six supplied transparent character cutouts and seven original TRAVESÍA companions. The original companions retain their 3D GLB rigs.
- Added responsive square-frame and animation checks to the focused Chromium test and Python source tests. Discover and Explore were not changed.
- Verification: 40 dependency-light Python tests, 17 Node tests, 12 focused character/postcard browser tests, 14 original companion animation tests, 10 booking checks, 7 Portal Run checks and 9 Trip Pulseboard checks passed (109 executed checks). The nine Flask HTTP/auth tests remain pending because Flask/Werkzeug cannot be installed in this isolated runner.


## TRAVESÍA V9 — Goa return postcards & character backdrop scenes — 2026-11-07
- Floating destination postcards are now always the two destinations not selected in the centre. Selecting Kyoto or Antarctica brings Goa into a floating card so it can be selected directly to return to Goa; selecting Goa restores Kyoto and Antarctica as the two alternatives.
- A postcard swap updates the small card image, alt text, label, data target, tooltip and accessible label together with the central scene.
- Added a unique soft background palette, animated glow layer and sparkle layer to each of the 13 friend character tiles while preserving identical 104 px desktop / 92 px compact square stages and contain-fit transparent art.
- Strengthened the six supplied-character idle motions without distorting their source artwork. Reduced-motion preferences remain respected.
- Added Node regression tests for all three postcard permutations, no-duplicate active cards, image/caption target updates, all 13 themed backgrounds, shared square sizing and animation mappings.
- Verification in this runner: 40 dependency-light Python tests and 25 Node tests passed. The focused Chromium run could not be launched through browser navigation in this runner (`ERR_BLOCKED_BY_ADMINISTRATOR`); the updated repeatable Chromium script is `scripts/verify_v7_character_postcards.py` and now covers the full Goa ↔ Kyoto ↔ Antarctica return cycle and the 13 animated backdrop tiles. The nine Flask HTTP/auth tests remain pending until Flask/Werkzeug are installed in a network-enabled environment.


## TRAVESÍA V9 — Goa return postcard cycle & animated character backdrops — 2026-11-07
- The floating destination cards now always display the two destinations not currently selected in the main scene. When Kyoto or Antarctica is selected, Goa appears as a floating card and can be clicked to return directly to Goa; the other card shows the remaining destination.
- Direct postcard clicks update the centre image, title, description, active destination state and both floating alternatives together. The bottom destination selector remains available.
- Every friend character now uses the same square stage (104×104 px desktop / 92×92 px compact) with a unique softly coloured background, animated glow and sparkle layer.
- All 13 character choices have distinct idle motion. Six supplied cutouts use CSS 2.5D animation; the seven original TRAVESÍA companions retain their animated GLB rigs.
- Discover and Explore were left unchanged.
- V9 verification: 40 Python tests, 25 Node tests, 15 focused postcard/character browser checks, 14 companion animation checks, 10 booking checks, 7 Portal Run checks and 9 Trip Pulseboard checks passed (120 executed checks). The nine Flask HTTP/auth tests remain pending until Flask/Werkzeug can be installed in a network-enabled environment.


## TRAVESÍA V10 — original-background character scene motion — 2026-11-07
- Replaced the six transparent cutouts with the user's uploaded full-scene images. Their original backgrounds are preserved; Bulbasaur retains its white background with only screenshot UI chrome trimmed.
- All 13 character choices use the same square stage (104 px desktop / 92 px mobile). The complete six supplied images are contain-fit and remain undistorted.
- Added full-scene camera drift/zoom, a blurred depth copy of the same background, subtle colour treatment and a moving light sweep, with individual timing per character. Reduced-motion settings are respected.
- Kept the original seven TRAVESÍA character GLB rigs and the 13-character no-duplicate assignment logic. Discover and Explore are unchanged.
- Verification: 40 Python tests, 27 Node tests, 15 focused Chromium checks, 14 companion checks, 10 booking checks, 7 Portal Run checks and 9 Pulseboard checks passed (122 executed checks). Nine Flask HTTP/auth tests remain pending because Flask/Werkzeug could not be installed in this isolated environment.

## V11 — backend hardening and GitHub release preparation

- Initialize SQLite schema automatically at WSGI startup, including safe additive migration of existing installations. Health checks now verify required tables, not only database connectivity.
- Enable SQLite WAL mode and a busy timeout for more reliable persistence under threaded requests.
- Add persistent hashed rate-limit buckets for authentication, companion chat, storyboard uploads, flight search and shared-trip access/writes. Raw IP addresses and emails are not stored in the rate-limit table.
- Enforce CSRF validation for authenticated logout, same-origin checks for API mutations, secure-cookie defaults for production and HSTS on HTTPS requests.
- Rotate/revoke the previous session on successful sign-in. Shared-trip updates now require `expected_updated_at` to prevent stale overwrites.
- Add verified SQLite backup/restore scripts using the SQLite online backup API, integrity checks, atomic file replacement and restrictive file permissions.
- Expand API security tests, add backup/restore tests, include Pillow in the development test dependencies, and update GitHub Actions to install the complete test set, run mandatory Flask tests, run browser/frontend checks and build the production Docker image.
- Add GitHub upload, backup/restore and production security guidance. The frontend directory is preserved byte-for-byte from V10.
- External provider approvals, credentials, public deployment and independent security review remain owner/provider actions; the application does not fabricate those approvals.

## V11 — backend hardening and Git-ready release (7 November 2026)
- Preserved the V10 frontend byte-for-byte; verified SHA-256 equality for every file under `frontend/`.
- Fixed fresh-deployment SQLite schema initialization and added schema-aware health checks, WAL mode, foreign keys and busy timeout.
- Added persistent hashed rate limiting, logout CSRF enforcement, same-origin mutation checks, login session rotation and optimistic locking for shared-trip edits.
- Added verified SQLite online backup/restore commands and tests.
- Tightened Git ignore rules for database WAL/SHM files and added repository guide, Dependabot and least-privilege GitHub Actions workflow for mandatory Python API, browser, frontend and Docker checks.
- Verification in this runner: 43 Python tests, 27 Node tests and 55 browser regression checks passed; Python compilation, YAML parsing and frontend hash comparison passed. The 15 Flask HTTP/auth integration tests, full cinematic browser suite and Docker build remain mandatory GitHub Actions gates because dependencies/browser runtime/Docker were unavailable here.
