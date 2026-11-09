# TRAVESÍA visual and travel interaction upgrades

These upgrades keep the existing TRAVESÍA brand, warm editorial palette, layout and navigation rather than replacing the approved design.

## Destination discovery

- The home page has six local illustrated fallback images for featured destinations. The cards label them as illustrative covers.
- The world explorer opens a detail panel when a featured marker/list item is selected.
- Clicking an arbitrary point on the map attempts an OpenStreetMap Nominatim reverse lookup, then searches Wikipedia/Wikimedia for a matching image/article.
- Where image metadata is available, the preview displays the article source, image-file source, creator and licence. If remote sources are unavailable, it keeps the illustrated fallback and says so.
- Online lookups are initiated by user interaction; map tiles and remote place images require internet access. The map defaults to OpenStreetMap road tiles. A dated NASA GIBS global MODIS satellite layer is available without a key, and a MapTiler higher-detail layer is available when the licensed provider key is configured; see `docs/PROVIDER_SETUP.md`.

## Companion 3D models and friend profiles

- Seven original GLB models are bundled locally: Bloop, Sprout, Pip, Roo, Mira, Orbit and Paws. Each has a skinned mesh, 12-joint rig and seven clips (`Idle`, `Wave`, `Dance`, `AdventureHop`, `Walk`, `Turn`, `Point`).
- `frontend/glb-viewer.js` is a self-contained CPU skeletal renderer for the bundled GLB skin/joint/animation data; it requires neither a WebGL context nor third-party renderer CDN scripts. Chromium playback tests cover all seven models and verify changing frames for Wave, Dance, AdventureHop, Walk, Turn and Point. A portrait fallback is retained if an asset cannot load. Hardware-specific visual/performance review remains recommended.
- Companion replies use local travel guidance by default; an optional server-side reply service can be configured. Browser speech depends on device support.
- Split Expenses supports up to twelve unique, editable participants. Each can use an illustrated portrait or upload a personal photo. Photos are resized before storage in local browser storage on that device.
- Renaming a friend keeps their avatar and updates their existing ledger references.

## Train/flight selection

- Flight cards link to Google Flights for current price and option comparisons. Booking proceeds through the airline/travel-partner provider the user chooses.
- Train tickets link directly to the official IRCTC ticketing portal. A secondary link opens a route-and-date schedule/fare search.
- The Flight or Train comparison widget lets the user enter the provider's displayed fare and journey duration. It compares those entered values without inventing a live fare.
- Changing the route/date rebuilds the provider links and clears the old manual comparison values so fares from a previous route are not reused accidentally.
- TRAVESÍA does not collect IRCTC/airline passwords, reserve a seat, or perform a transaction.

## Technical additions

- `frontend/feature-upgrades.js` contains the discovery and interaction enhancements.
- The unified Flask app serves `/feature-upgrades.js` and `/assets/...` in addition to the existing frontend routes.
- New image files live in `frontend/assets/companions/` and `frontend/assets/destinations/`.


## PulseMatch (October 2026)
- Added `POST /api/trip/fit` for an explainable group destination shortlist.
- Score dimensions and weights are visible in the response: budget fit 55%, vibe fit 30%, trip-duration fit 15%.
- Input validation covers group size, duration, budget and supported vibe choices.
- Candidate daily-cost bands are explicitly illustrative planning assumptions; they are not sourced live prices, a guarantee of affordability, or model predictions.
- The Squad Plans UI displays each candidate's score breakdown, reasons and caveats, and can send the selected destination to Trip Studio.
- API tests cover response shape, sorting, group-budget arithmetic and invalid inputs.
