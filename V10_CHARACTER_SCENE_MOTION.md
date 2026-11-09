# V10 — original-background animated character scenes

## Source images

The six friend images are copied from the user's uploaded images into `frontend/assets/character-scenes/`:

- `pikachu-scene.png`
- `bulbasaur-scene.png`
- `iron-man-scene.png`
- `spider-man-scene.png`
- `harry-potter-scene.png`
- `hermione-scene.png`

The original backgrounds are preserved. The Bulbasaur file retains the original white background while cropping away the search-result footer and camera overlay that were part of the screenshot chrome.

## Display and motion

- The picker and Split Expenses friend cards use matching square scene stages: 104×104 px desktop and 92×92 px compact/mobile.
- The complete source image is shown with `object-fit: contain`; it is not converted into a transparent silhouette or cropped to fill the square.
- A blurred, enlarged copy of the same image is used behind it to fill unused space and create a soft depth layer. The original image remains visible in front.
- The complete scene moves with a gentle camera drift/zoom. A separate ambient backdrop drift and a light sweep add motion. Each friend character has a different timing curve.
- Reduced-motion settings disable the effects.

## Important limitation

The supplied copyrighted characters have not been transformed into Studio Ghibli artwork. The attempted image restyle was rejected by the image-generation safety checks. V10 therefore preserves the uploaded images and applies CSS motion and colour treatment to the entire image scene. The six user images are not frame-by-frame animated or rigged. The seven original TRAVESÍA companions retain their existing GLB rigs.

## Verification

Run `python scripts/verify_v7_character_postcards.py` for the focused browser checks (postcard interactions, all 13 scene tiles, animation names, used-character state and mobile sizing).
