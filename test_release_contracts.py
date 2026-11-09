"""Dependency-light release checks for TRAVESÍA assets and safety contracts."""
from __future__ import annotations
import json, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'frontend'/'assets'/'companions3d'
EXPECTED_SLUGS={'bloop','sprout','mira','orbit','paws','pip','roo'}
EXPECTED_CLIPS={'Idle','Wave','Dance','AdventureHop','Walk','Turn','Point'}

def read_glb(path:Path):
    raw=path.read_bytes();assert len(raw)>=20
    magic,version,total=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and total==len(raw)
    json_len,json_type=struct.unpack_from('<II',raw,12);assert json_type==0x4E4F534A
    doc=json.loads(raw[20:20+json_len].decode('utf-8').rstrip('\x00 \t\r\n'))
    bin_header=20+json_len;bin_len,bin_type=struct.unpack_from('<II',raw,bin_header)
    assert bin_type==0x004E4942 and bin_header+8+bin_len==len(raw)
    binary=raw[bin_header+8:]
    assert doc.get('asset',{}).get('version')=='2.0'
    assert doc.get('skins') and len(doc['skins'][0].get('joints',[]))>=10
    names={a.get('name') for a in doc.get('animations',[])}
    assert EXPECTED_CLIPS.issubset(names),f'{path.name} clips missing: {EXPECTED_CLIPS-names}'
    assert any(n.get('skin')==0 for n in doc.get('nodes',[]))
    for accessor in doc.get('accessors',[]):
        view=doc['bufferViews'][accessor['bufferView']]
        assert view.get('buffer')==0 and view.get('byteOffset',0)+view['byteLength']<=len(binary)
        assert accessor['count']>0
    return doc,binary

def test_all_seven_companions_are_rigged_glbs_with_locomotion_and_greeting_clips():
    assert {x.stem for x in ASSETS.glob('*.glb')}==EXPECTED_SLUGS
    for slug in sorted(EXPECTED_SLUGS):
        doc,_=read_glb(ASSETS/f'{slug}.glb')
        assert len(doc['skins'][0]['joints'])>=10
        assert EXPECTED_CLIPS.issubset({a.get('name') for a in doc['animations']})
        assert all(a.get('channels') and a.get('samplers') for a in doc['animations'])

def test_provider_contracts_label_missing_credentials_and_no_civic_module():
    app=(ROOT/'app.py').read_text();front=(ROOT/'frontend/app.js').read_text()
    assert 'not_configured' in app and 'AMADEUS_CLIENT_ID' in app and 'AMADEUS_CLIENT_SECRET' in app
    assert 'MAPTILER_API_KEY' in app and 'satellite_enabled' in app and 'Open-Meteo' in app
    assert 'TRAVESÍA does not issue tickets or claim bookings are complete' in app
    assert 'civic_complaints' not in app and 'connected_live_civic_submission_apis' not in app
    assert 'Nagpur' not in front and 'Civic Pulse' not in front

def test_auth_and_shared_trip_contracts_are_present():
    source=(ROOT/'app.py').read_text();front=(ROOT/'frontend/app.js').read_text()
    assert 'check_password_hash' in source and 'generate_password_hash' in source
    assert 'httponly=True' in source and 'samesite="Lax"' in source
    assert 'X-CSRF-Token' in source and 'editor_token_hash' in source
    assert 'X-Shared-Trip-Editor' in source and 'hmac.compare_digest' in source
    assert 'shared-trip-editor-token' in front

def test_home_uses_editorial_destination_story_and_compact_svg_mascot():
    shell=(ROOT/'frontend/index.html').read_text();app=(ROOT/'frontend/app.js').read_text();viewer=(ROOT/'frontend/glb-viewer.js').read_text()
    assert 'hero-cinematic' in shell and 'sceneMainCard' in app
    assert 'id="citypulseGlobe"' not in shell and 'heroBuddy3D' not in shell
    assert 'globe.js' not in shell and 'cinematic.js' in shell
    assert 'CityPulseGLBViewer.mount' in (ROOT/'frontend/companion-3d.js').read_text()
    assert 'current=null' in viewer and "name==='Walk'" in viewer
    assert 'id="bloopMiniArt" class="bloop-mini-art"' in shell
    assert 'class="bloop-pupil"' in shell
    assert 'function wireBloopDock' in app and 'launcher.addEventListener("pointermove"' in app
    assert 'map-click-ripple' in (ROOT/'frontend/styles.css').read_text()

def test_game_and_video_storyboard_contracts():
    game=(ROOT/'frontend/world-game.js').read_text();app=(ROOT/'app.py').read_text();ui=(ROOT/'frontend/app.js').read_text()
    assert 'game-travel-portal' in game and 'game-floating-postcard' in game
    assert 'pointermove' in game and 'game-ripple' in game
    assert 'game-world-planet' not in game
    assert '/api/media/clip-storyboard' in app and 'ffprobe' in app and 'X-CSRF-Token' in app
    assert 'clipStoryboardForm' in ui and 'consent' in ui.lower()

def test_container_setup_has_persistent_database_secure_cookies_and_ffmpeg():
    blueprint=(ROOT/'render.yaml').read_text();docker=(ROOT/'Dockerfile').read_text();env=(ROOT/'.env.example').read_text()
    assert 'mountPath: /app/instance' in blueprint and 'CITYPULSEX_DB' in blueprint
    assert 'COOKIE_SECURE' in blueprint and 'healthCheckPath: /api/health' in blueprint
    assert 'apt-get install -y --no-install-recommends ffmpeg' in docker
    for name in ('AMADEUS_CLIENT_ID','AMADEUS_CLIENT_SECRET','MAPTILER_API_KEY','COOKIE_SECURE','LLM_API_KEY'):
        assert name in env

def test_bloop_is_a_small_persistent_octopus_with_blink_and_pointer_look():
    app=(ROOT/'frontend/app.js').read_text()
    shell=(ROOT/'frontend/index.html').read_text()
    css=(ROOT/'frontend/styles.css').read_text()
    assert 'bloop-launcher' in shell and 'bloopMiniArt' in shell
    assert 'bloop-pupil' in shell and 'moveEyes' in app
    assert 'launcher.addEventListener("pointermove"' in app
    assert 'is-blinking' in app and 'bloopBlink' in css
    assert '.bloop-dock{position:fixed' in css
    assert '.bloop-launcher{position:relative' in css and 'width:76px;height:76px' in css
    assert '.bloop-launcher{width:66px;height:66px}' in css

def test_world_explorer_uses_gpu_independent_atlas_and_browser_verification():
    feature=(ROOT/'frontend'/'feature-upgrades.js').read_text()
    css=(ROOT/'frontend'/'styles.css').read_text()
    verifier=(ROOT/'scripts'/'verify_cinematic_refresh_browser.py').read_text()
    alias=(ROOT/'scripts'/'verify_world_map_browser.py').read_text()
    assert 'offline-atlas-map' in feature and 'offline-map-marker' in feature
    assert 'assets/world-map.svg' in feature and '.offline-atlas-art' in css
    assert 'six postcards appear below map' in verifier and 'selected place card is inside the map' in verifier
    assert 'verify_cinematic_refresh_browser.py' in alias
    assert 'no longer requires a WebGL globe' in alias

def test_booking_handoffs_include_google_ixigo_and_official_irctc_without_secrets():
    ext=(ROOT/'frontend'/'extensions.js').read_text()
    docs=(ROOT/'docs'/'PROVIDER_SETUP.md').read_text()
    assert 'https://www.google.com/travel/flights?q=' in ext
    assert 'https://www.ixigo.com/flights' in ext and 'https://www.ixigo.com/trains' in ext
    assert 'https://www.irctc.co.in/eticket/' in ext
    assert 'cityPulseAuthCsrf' not in ext[ext.find('function currentExternalSearches'):ext.find('function experienceCardsHTML')]
    assert 'IRCTC-listed' in docs and 'No TRAVESÍA API key is required for these hand-offs' in docs


def test_backend_capabilities_expose_no_key_flight_and_authorised_train_handoffs():
    app=(ROOT/'app.py').read_text()
    assert '"ixigo_trains": "https://www.ixigo.com/trains"' in app
    assert '"ixigo_flights": "https://www.ixigo.com/flights"' in app
    assert 'IRCTC-listed B2C PSP' in app
    assert 'TRAVESÍA never collects provider passwords or payment details' in app


def test_provider_onboarding_status_and_documented_affiliate_route_are_exposed():
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    ui_source = (ROOT / "frontend" / "extensions.js").read_text(encoding="utf-8")
    plan = (ROOT / "docs" / "PROVIDER_ONBOARDING_PLAN.md").read_text(encoding="utf-8")
    assert '"provider_onboarding"' in app_source
    assert '"recommended_path": "affiliate_or_associate_of_an_existing_irctc_b2c_psp"' in app_source
    assert "Provider onboarding pack" in ui_source
    assert "affiliate/associate" in plan
    assert "Flight Create Orders" in plan and "consolidator" in plan
    assert "₹3 lakh" in plan and "₹10 lakh" in plan


def test_split_expenses_uses_seven_original_local_friend_characters():
    app=(ROOT/'frontend'/'app.js').read_text(encoding='utf-8')
    library=(ROOT/'frontend'/'friend-characters.js').read_text(encoding='utf-8')
    assets=ROOT/'frontend'/'assets'/'companions'
    expected=('bloop-mini.svg','sprout.webp','pip.webp','roo.webp','mira.webp','orbit.webp','paws.webp')
    assert 'function splitAvatarMarkup' in app and 'ensureUniqueFriendCharacters' in app
    for name in expected:
        path=assets/name
        assert path.is_file() and path.stat().st_size > 500, name
        assert name in library
    assert 'this.onerror=null;this.src=' in app
    assert 'character?.name' in app and 'travel character' in app and 'bloop-mini.svg' in app


def test_friend_character_picker_has_unique_pop_culture_characters_and_bundled_art():
    app=(ROOT/'frontend'/'app.js').read_text(encoding='utf-8')
    library=(ROOT/'frontend'/'friend-characters.js').read_text(encoding='utf-8')
    index=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')
    css=(ROOT/'frontend'/'styles.css').read_text(encoding='utf-8')
    for character in ('pikachu','bulbasaur','iron-man','spider-man','harry-potter','hermione'):
        asset=ROOT/'frontend'/'assets'/'character-scenes'/f'{character}-scene.png'
        assert asset.is_file() and asset.stat().st_size>1000,character
        from PIL import Image
        scene=Image.open(asset).convert('RGBA')
        assert scene.getchannel('A').getextrema() == (255,255), f'{character} should preserve its opaque source scene'
        assert f'id: "{character}"' in library
    assert 'friend-characters.js?v=10' in index
    assert 'object-fit: contain !important' in css and '--character-scene-image' in css and 'cpFullSceneCamera' in css
    assert 'function openFriendCharacterPicker' in app and 'function ensureUniqueFriendCharacters' in app
    assert 'available(people, selected, person)' in library and 'assign(people, selected, person, characterId)' in library
    assert 'In use by ${escapeHtml(assigned)}' in app and 'characters:state.splitCharacters||{}' in app
    assert 'twelve friends' in (ROOT/'frontend'/'tests'/'friend-characters.test.cjs').read_text(encoding='utf-8').lower()
    assert 'friendWizardGlow' in css and 'friendLeafSway' in css and 'friendWebSwing' in css


def test_secondary_pages_have_own_scene_sequences_without_changing_discover_or_explore():
    app=(ROOT/'frontend'/'app.js').read_text(encoding='utf-8')
    extensions=(ROOT/'frontend'/'extensions.js').read_text(encoding='utf-8')
    scenes=('planner','mobility','citytwin','companion','squad','saved','split','pulse','experiences','account')
    for view in scenes:
        assert f'{view}:{{eyebrow:' in app
    assert 'window.cityPulsePageSceneMarkup?.(state.view)' in extensions
    assert 'render(homeHTML(),wireHome,false)' in extensions
    assert 'render(exploreHTML(),wireExplore,false)' in extensions
    assert 'Next scene' in app and 'cpPageSceneNext' in app


def test_shared_trip_payload_preserves_unique_friend_character_assignments():
    server=(ROOT/'app.py').read_text(encoding='utf-8')
    front=(ROOT/'frontend'/'app.js').read_text(encoding='utf-8')
    assert 'characters_raw = payload.get("characters", {})' in server
    assert 'character_owners' in server and 'Each friend must have a different character' in server
    assert 'characters:state.splitCharacters||{}' in front
    assert 'state.splitCharacters=shared.characters' in front


def test_local_env_configuration_is_loaded_without_extra_runtime_dependency():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    loader=(ROOT/'services'/'env_config.py').read_text(encoding='utf-8')
    run=(ROOT/'run_windows.bat').read_text(encoding='utf-8')
    assert 'load_env_file(ROOT / ".env")' in app
    assert 'os.environ.setdefault(key, value)' in loader
    assert 'copy ".env.example" ".env"' in run.lower()


def test_full_verification_cannot_silently_skip_flask_http_auth_tests():
    api=(ROOT/'tests'/'test_travesia_api.py').read_text(encoding='utf-8')
    verify=(ROOT/'verify_windows.bat').read_text(encoding='utf-8')
    workflow=(ROOT/'.github'/'workflows'/'tests.yml').read_text(encoding='utf-8')
    assert 'RuntimeError(' in api and 'importorskip' not in api
    assert 'CITYPULSEX_REQUIRE_FLASK_TESTS=1' in verify
    assert 'CITYPULSEX_REQUIRE_FLASK_TESTS: "1"' in workflow


def test_all_referenced_cinematic_and_friend_scripts_are_served_by_flask():
    app_source=(ROOT/'app.py').read_text(encoding='utf-8')
    html=(ROOT/'frontend'/'index.html').read_text(encoding='utf-8')
    for asset in ('friend-characters.js','cinematic.js','cinematic.css'):
        assert asset in html
        assert f'@app.get("/{asset}")' in app_source


def test_home_float_postcards_change_the_main_destination_scene():
    app_source=(ROOT/'frontend'/'app.js').read_text(encoding='utf-8')
    assert 'data-postcard-dest="Kyoto, Japan"' in app_source
    assert 'data-postcard-dest="Antarctica"' in app_source
    assert "$$('[data-postcard-dest]')" in app_source
    assert 'image.src=scene.image' in app_source
    assert 'window.heroSceneManualUntil' in app_source


def test_hero_floating_postcards_are_clickable_and_replace_the_centre_scene():
    app=(ROOT/'frontend'/'app.js').read_text(encoding='utf-8')
    css=(ROOT/'frontend'/'styles.css').read_text(encoding='utf-8')
    assert 'data-postcard-dest="Kyoto, Japan"' in app
    assert 'data-postcard-dest="Antarctica"' in app
    assert 'event.target.closest("[data-postcard-dest]")' in app
    assert 'chooseHeroDestination(postcard.dataset.postcardDest)' in app and 'const chooseHeroDestination=destination=>setHeroScene(destination,{manual:true})' in app
    assert 'sceneMainImage' in app and 'sceneDestinationName' in app
    assert 'pointer-events: auto !important' in css
