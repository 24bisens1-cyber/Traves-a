# 3D companion implementation

Bloop is an original teal octopus-inspired plush travel guide at `frontend/assets/companions3d/bloop.glb`. It is a full-body skinned GLB with a 12-joint skeleton and seven authored procedural clips: Idle, Wave, Dance, AdventureHop, Walk, Turn and Point. Six other original companions are bundled. The local canvas renderer skins mesh data and animation channels without a third-party CDN dependency.

## Interaction contract

- Home: Bloop's body and position remain still by default. Subtle procedural breathing/blinking and clamped head-look add life without making the character wander around the page.
- Greeting: clicking the character/greeting control opens the assistant chat dock and triggers Wave.
- Destination: selecting a map pin triggers Walk → Turn → Wave, then opens the selected destination's planning view.
- Chat: the guide is presented beside a proper chat panel, not inside a square avatar frame. Without LLM credentials it gives a clearly local fallback; generative answers require user-supplied server-side configuration.
- Reduced motion: UI transitions/effects should be limited according to the user's reduced-motion preference.

## Verification

`scripts/verify_glb_animation_browser.py` tests all seven bundled models and visible frame changes for Wave, Dance, AdventureHop, Walk, Turn and Point in Chromium. This release recorded 14/14 checks passing. The homepage/map smoke suite separately verifies Bloop rendering, head tracking, chat dock, greeting and destination interaction.

## Honest limitations

The models are procedurally generated stylized low-poly art, not photoreal models or motion-capture-quality performances. The current renderer is a self-contained canvas CPU-skinning renderer, not a CDN-dependent Three.js/WebGL renderer. Continue improving the walk cycle's weight transfer, foot contact, anticipation, eye target and animation blending if a more lifelike result is needed. Original franchise-inspired silhouettes may be used as broad creative direction only; use copyrighted character assets only when licensed/authorized.
