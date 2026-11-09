# TRAVESÍA visual refresh — 7 November 2026

This refresh responds to the user's screenshots, compact-octopus reference and supplied video-reference handoff while retaining the TRAVESÍA identity and existing travel features. The handoff describes Delulu Café; its transferable principles (controlled cinematic reveals, foreground/background depth, deliberate camera movement, layered timing, scroll storytelling and consistent scene continuity) are adapted to travel scenes. Café-specific coffee pouring and menu-book interactions are not imported into TRAVESÍA.

## Landing experience
- The oversized black orbital globe was removed; the opening experience is now an editorial destination-postcard composition.
- Goa is the initial featured story; Kyoto and Antarctica appear as layered floating cards.
- Destination selector buttons switch the main postcard; the story scene adds pointer-responsive lighting/parallax and a moving route line.
- The hero, floating cards and story artwork use purposeful scroll-linked movement, controlled entry reveals and a consistent travel palette.
- Three story chapters connect discovery, group planning and itinerary building.

## Bloop travel buddy
- Bloop is a small inline-SVG aqua octopus anchored at the bottom-right of the viewport.
- Measured size in Chromium: 48 × 48 px desktop, 42 × 42 px mobile and 38 × 38 px on very narrow phones. The launcher is transparent with no badge or halo.
- Pupils follow pointer movement; tapping the buddy triggers a click-look/blink response. Only the eyes blink; the character body does not shrink. A compact chat popover opens separately.
- The buddy remains separate from the hero content and does not cover the map or main navigation at tested viewports.

## Explore atlas
- The selected-place card is overlaid inside the map panel.
- Six destination postcards (Goa, Kyoto, Antarctica, Sydney, Rome and Bali) appear in a rail beneath the map.
- Category filters remain interactive.
- When Leaflet or online tiles are unavailable, the bundled `frontend/assets/world-map.svg` provides the illustrated atlas with six clickable pins, an animated route and a local preview.
- The no-GPU atlas is intentional; the black orbital globe and its WebGL dependency were removed from the landing and Explore experience.

## Split Expenses friend portraits
- The supplied Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione artwork is bundled locally and shown first in the picker.
- All seven original TRAVESÍA companions remain available after those six supplied choices.
- Twelve friends receive twelve different defaults; a character already assigned to another friend is locked. Retired generic `traveller` values migrate to valid unique choices.
- Profile images use verified local asset paths and an image-error fallback. Custom friend photo uploads remain supported.

## Portal Run
- The orbital/science-class presentation was replaced with a floating-island travel scene, a destination-image portal, floating postcards and travel collectibles.
- Layered island, cloud, postcard and portal movement uses controlled pointer/scroll cues, not random transformations. Reduced-motion preferences stop decorative movement.
- The collectible mechanic and saved best score are preserved.

## Browser verification
Run from the project root:

```bash
python scripts/verify_cinematic_refresh_browser.py
python scripts/verify_glb_animation_browser.py
python scripts/verify_booking_handoffs_browser.py
python scripts/verify_portal_run_browser.py
python scripts/verify_trip_pulseboard_browser.py
```

Executed results: cinematic refresh 29/29, companions 14/14, booking hand-offs 10/10, Portal Run 7/7 and Trip Pulseboard 9/9 (69/69 total). The checks confirm eye movement, all four default profile portraits, scroll-linked story motion, all six offline map pins, selected-place details inside the map, responsive mascot sizing and no mobile horizontal overflow.

The browser suite uses an in-memory offline fixture to make the UI deterministic. It does not claim that external photo, weather, tile or booking providers are always reachable.
