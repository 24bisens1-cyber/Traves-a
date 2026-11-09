# Friend characters and secondary-page motion

## Friend character picker

Split Expenses supports up to 12 people and ships with 13 distinct character choices:

- Seven original TRAVESÍA characters: City explorer, Sprout, Pip, Roo, Mira, Orbit and Paws.
- Six extra portraits cropped from images supplied by the project owner: Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter and Hermione.

Every friend receives a different default character. The **Choose character** control opens a picker; characters used by another friend in the same trip are disabled and identify the friend using them. Selection is saved with the local ledger, follows a friend when their name changes, is released when they leave the crew, and is included in shared-trip sync. The shared-trip API validates both the character allowlist and uniqueness before storing the crew state.

The portraits have gentle idle motion. Pikachu has a little hop, Bulbasaur sways, Iron Man has a hover/glow, Spider-Man swings, Harry Potter has a soft glow and Hermione has a light book-like sway. Hovering a friend card gives a brief reaction. `prefers-reduced-motion` disables these animations.

User-uploaded friend photos continue to work. The original images in the reference screenshots were supplied by the project owner and have been cropped for the avatars; public redistribution should use only artwork for which the project owner has the necessary rights or permissions.

## Secondary-page scene ribbons

The following pages have their own local-image scene header:

- Trip Studio
- Mobility
- World Scene Lab
- Companion Studio
- Squad Plans
- Saved Worlds
- Split Expenses
- Trip Pulseboard
- Stays & Experiences
- Account & access

Each header has page-specific copy and photography, a scene selector, a Next scene action, a small automatic scene change, pointer-responsive perspective and a page-relevant action. Reduced-motion preferences are respected. The selected place can be handed to Explore where appropriate.

**Discover and Explore are intentionally excluded.** Their page composition and layout are not wrapped in the new secondary-page scene component. The Explore visual layout is unchanged; its existing online image enrichment now handles concurrent/offline lookup failures without producing an unhandled browser promise rejection.

## Verification

- `node --test frontend/tests/*.test.cjs` covers 15 tests, including uniqueness for 12 friends, duplicate repair, locked selections and assignment rules.
- `scripts/verify_cinematic_refresh_browser.py` verifies the picker, 12 loaded portraits, unique assignments, all ten secondary-page scenes, scene switching, mobile layout and absence of injected banners on Discover/Explore.
- Shared-trip API tests verify that character assignments survive create/read and that duplicate character assignments are rejected. Those Flask HTTP tests require Flask/Werkzeug to be installed before they can execute.


## V6 fix — 7 November 2026

- Flask now explicitly serves `friend-characters.js`, `cinematic.js` and `cinematic.css`, which were previously linked by the HTML but not routed by the Flask app.
- Default crew order is Pikachu, Bulbasaur, Iron Man, Spider-Man, Harry Potter, Hermione, then Bloop, Sprout, Pip, Roo, Mira, Orbit and Paws. The legacy generic `traveller` id is migrated to a distinct default and is no longer a character option.
- The Kyoto and Antarctica floating postcards now update the central Discover hero image and its destination copy when activated.
