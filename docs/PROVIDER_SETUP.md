# Provider setup and no-key booking alternatives

## Flights: live comparisons without a TRAVESÍA key
No TRAVESÍA API key is required for these hand-offs. The travel page offers a route-and-date live search through Google Flights and an ixigo Flights search page (enter the same route/dates there), plus a KAYAK metasearch alternative. Google Flights receives the selected route and dates in its search query; ixigo opens its flight search form. Compare the current fares and finish checkout with the airline or travel seller. These are live provider pages, not prices copied into TRAVESÍA.

Optional in-app flight offers use Amadeus when `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` are configured on the server. Credentials are never entered in the browser. Amadeus test-environment offers are not production inventory. Production ticket issuance needs the appropriate local/legal eligibility and an airline consolidator or issuer agreement; offer search by itself is not a booking.

## Indian trains: official and listed partner checkout
The travel page offers the official IRCTC e-ticket portal and ixigo's train search/booking site. IRCTC lists Le Travenues Technology (ixigo) as an IRCTC-listed B2C Principal Service Provider in the B2C Principal Service Provider section of its March 2026 authorised-provider list: https://contents.irctc.co.in/en/IRCTC%20Authorised%20Principal%20Service%20Providers.pdf. Users sign in and pay on the selected provider's site; TRAVESÍA does not collect IRCTC passwords, passenger identity data, or payment information. Train schedules and fare availability are provider controlled.

TRAVESÍA does not automate IRCTC login, scrape seat inventory, or make a ticket look confirmed. Direct in-app rail booking requires a formal IRCTC/PSP partnership and its applicable integration approval. The no-key alternative is the authorised provider hand-off.

## AI chat and visual storyboard
Set `LLM_API_KEY` and an HTTPS OpenAI-compatible `LLM_BASE_URL` on the server. `LLM_MODEL` must support chat; `clip-storyboard` additionally requires image/vision input support. No key belongs in the browser. The chat endpoint is usable without a key through local fallback responses. The visual storyboard requires sign-in, CSRF, explicit consent, FFmpeg/FFprobe and an MP4/MOV/WEBM/M4V file no larger than 25 MB and 3 minutes. Six sampled frames (no audio) are sent to the configured provider. Temporary input and frames are deleted when the request ends; provider retention terms still apply.

## Weather
Configure `CITYPULSEX_CONTACT_EMAIL` or a public `CITYPULSEX_CONTACT_URL` for MET Norway's identifying User-Agent. The provider can be unreachable in restricted environments. Open-Meteo's free API is non-commercial; production disables that fallback by default with `WEATHER_ALLOW_OPEN_METEO_FREE=0`. Use an appropriate licensed plan if commercial use is required.

## Satellite imagery
NASA GIBS is the no-key lower-detail global true-colour satellite layer, with date and attribution. MapTiler is optional higher-detail licensed imagery via `MAPTILER_API_KEY`. Road tiles are not satellite imagery; never relabel them.

## World atlas rendering
The current Explore experience uses a bundled illustrated world atlas with six clickable destination pins and a place-preview card inside the map. When Leaflet and map tiles are reachable, the online map can enhance the experience; the local atlas remains interactive without map credentials, GPU hardware or WebGL. Run `python scripts/verify_cinematic_refresh_browser.py` to validate the offline atlas, pin selection and responsive layout. The former orbital globe was intentionally removed from the landing page.

## Persistence / admin
Set `COOKIE_SECURE=1` behind HTTPS, `CITYPULSEX_DB` to persistent storage, and bootstrap `CITYPULSEX_ADMIN_EMAIL` / `CITYPULSEX_ADMIN_PASSWORD` using environment variables. The app reads `.env` automatically for local development; production secrets should be managed by the hosting provider. Flask signed-cookie sessions are not used, so `CITYPULSEX_SECRET_KEY` is not required. Shared-trip edit tokens are separate from read codes.

## Formal provider onboarding
For the exact IRCTC affiliate/associate route, document list, policy-listed fees, direct-PSP alternative and Amadeus production/ticket-issuance steps, see `docs/PROVIDER_ONBOARDING_PLAN.md`. The current application status is exposed by `/api/providers/status` under `provider_onboarding`. Provider approval is issued to the legal operator by the partner; it is not implied by an external booking link.
