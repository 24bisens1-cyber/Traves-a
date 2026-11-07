# Research and roadmap

## Product thesis

TRAVESÍA combines playful spatial exploration with transparent trip decisions. Its differentiator hypothesis is a living character/world interface tied to source-labelled travel data—not the unsubstantiated claim that maps, itinerary planning or AI assistants are unique in the market.

## Current direction
- Full-body 3D assistant with explicit greeting/locomotion clips and a static homepage default.
- Interactive global atlas with map click effects, Portal Run and companion unlocks.
- Source/timestamp/status-labelled weather and provider-backed flight searches; external hand-offs when credentials are missing.
- Inspectable budget heuristics and Trip Pulseboard snapshots.
- Optional visual travel-video storyboard using six sampled frames, with consent and no audio processing.

## Next validation
1. Usability test whether a first-time user discovers map destinations, chat, and Portal Run without instruction.
2. Validate model animation quality on multiple real browsers/devices and improve foot/tentacle contact using reviewed animation clips.
3. Enable provider integrations only with the account owner's authorised credentials and verify freshness, licensing and provider error behaviour.
4. Run complete auth/API tests, cross-user collaboration and persistent-disk tests in a connected CI/hosted environment.
5. Validate the storyboard with a vision-capable endpoint, confirm frame timestamps/quality and provider data policy; do not claim rendered-video editing until implemented.
