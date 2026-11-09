# TRAVESÍA — Final Release Guide

This package contains TRAVESÍA — The World Is Yours to Explore: the Flask application, interactive illustrated world atlas, seven locally bundled rigged companions, cinematic postcard motion layer, Portal Run, Trip Studio, Mobility, Trip Pulseboard, Companion Studio, Squad Plans, Split Expenses, Stays & Experiences, provider adapters, security checks and deployment setup.

## Windows setup

1. Install Python 3.11 or newer.
2. Extract the ZIP.
3. Open the extracted `TRAVESÍA` folder in VS Code.
4. Double-click `run_windows.bat`; it creates `.venv`, installs the Flask/Werkzeug application dependencies, creates `.env` from `.env.example` if needed and starts the server.
5. Open `http://127.0.0.1:5000` in your browser.

For full verification, install Node.js 20 LTS or newer and double-click `verify_windows.bat`. It installs the development requirements and Playwright Chromium, runs the complete Python HTTP/auth test suite, Node expense tests and browser acceptance checks. On macOS/Linux, follow the commands in `START_HERE.txt`.

## Local configuration and account security

The Flask app reads `.env` automatically using the dependency-free loader in `services/env_config.py`. Set a unique `CITYPULSEX_ADMIN_EMAIL` and a strong `CITYPULSEX_ADMIN_PASSWORD` for first admin provisioning. Keep `COOKIE_SECURE=0` for localhost HTTP only; set `COOKIE_SECURE=1` behind HTTPS in production. The app uses opaque random session tokens hashed in SQLite, not Flask's signed-cookie session mechanism. Do not set the obsolete `CITYPULSEX_SECRET_KEY`; it is not used.

Never commit `.env`, real credentials or provider secrets. For production use HTTPS, durable database storage, unique admin credentials, and a tested backup/recovery process.

## Motion and travel companion

The homepage uses destination photography, a selectable postcard sequence, layered depth, scroll-linked artwork motion, pointer-responsive scene lighting and smooth section reveals. Explore uses a bundled illustrated world atlas with six clickable destination pins and an in-map selected-place preview. Online Leaflet tiles are optional; local atlas exploration does not require GPU hardware or a map API key.

Bloop is a small aqua octopus dock at the bottom-right. It has pointer-following pupils, a click/blink reaction and a compact chat popover. Split Expenses includes a distinct local traveller portrait for Friend 1; all default crew portraits have local asset paths and fallbacks. Companion Studio contains seven local rigged GLBs with animation clips.

## Travel provider boundaries

- Flight search works without a TRAVESÍA key through route-aware Google Flights, ixigo Flights and KAYAK hand-offs. Optional in-app flight offers require authorised Amadeus credentials.
- Train search/checkout opens official IRCTC or IRCTC-listed ixigo. Provider sign-in, payment and PNR confirmation remain with the provider; TRAVESÍA does not purchase or issue the ticket.
- Hotels, cafés, activities and event searches use external provider hand-offs unless a supported data provider is configured.
- Trip budgets and local route examples are planning aids, not provider quotes.

## Storyboard Workshop

The optional video tool accepts MP4/MOV/WEBM/M4V, limits uploads to 25 MB and three minutes, requires authentication, CSRF and explicit consent, and depends on FFmpeg/FFprobe plus a configured vision-capable provider. It samples up to six frames; audio is not processed. It creates a text storyboard, not a rendered or editable video. Temporary inputs and frames are removed after the request.

## Release verification

The current build container executed 29 Python tests (excluding the Flask HTTP/auth module), 8 Node expense tests and 69 Chromium browser checks successfully. The nine Flask HTTP/auth integration tests remain pending because Flask/Werkzeug could not be installed in the network-isolated build container. They are mandatory in the included `verify_windows.bat` and GitHub Actions workflow; missing dependencies now produce an actionable error rather than a silent skip. See `docs/VERIFICATION_REPORT.md` for exact results and commands.

A complete production verification additionally requires running the full Flask test suite after dependency installation, configuring/approving any optional providers, and testing deployment-specific HTTPS, account isolation and persistent storage.
