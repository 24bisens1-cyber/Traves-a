# TRAVESÍA release scope

## Product
TRAVESÍA is a global playful travel-planning product. It is not a municipal incident reporting or civic digital-twin application in this release.

## Core modules
- Editorial destination-postcard discovery and a clickable six-destination illustrated world atlas, with an in-map selected-place preview, animated route details and responsive pointer interactions.
- Trip Studio with editable itinerary drafts and transparent illustrative budget allocations.
- Trip Pulseboard showing separate weather source/freshness, estimated budget fit and flight hand-off signals.
- Mobility comparisons (explicitly illustrative until live local routing/fare providers are integrated).
- Stays and experiences through external searches; no claimed booking without provider confirmation.
- Squad destination fit and shared trip/expense collaboration.
- Portal Run game with seven collectible sparks, timer, score, best score, replay and unlock screen.
- Original rigged 3D companions in Companion Studio. Bloop is a small bottom-right SVG travel buddy on the main application shell, with eye tracking, blinking and chat.
- Companion chat with local fallback and an optional server-side reply service. Optional consent-gated video storyboard samples six frames; no audio analysis or rendered video is claimed.
- Account authentication, CSRF-protected changes, editor-token collaboration, persistent production database setup.

## Evidence and restrictions
- Real-world provider values require successful authorised integrations and show source/time/status; otherwise values are marked unavailable or hand-off.
- Budget/scenario outputs are heuristics/demos, not live prices, official forecasts or safety scores.
- All models/media must be original or licensed. Uploaded reference videos are private design references and are not bundled as public assets.
- No Civic Pulse/Nagpur civic reports, complaint routes, civic data templates or official civic provider claims remain in the app.

## Release quality gates
- Unit/API/auth tests run in a connected environment.
- Browser tests verify map, game, chat states and actual changed pixels for animation playback.
- Cross-user read/write permission and stale-write tests pass.
- Hosted persistence/HTTPS are checked after a real deployment.
- Provider connectivity is tested only after credentials and usage permissions are configured.
