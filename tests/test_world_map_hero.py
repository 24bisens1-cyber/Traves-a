from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_world_map_asset_exists_and_is_not_empty():
    text=(ROOT/'frontend/assets/world-map.svg').read_text(encoding='utf-8')
    assert 'Illustrated world map' in text and 'width="1440" height="760"' in text
    assert 'fill="url(#land)"' in text and 'stroke-dasharray="6 8"' in text

def test_home_has_cinematic_postcards_and_global_destinations():
    app=(ROOT/'frontend/app.js').read_text(encoding='utf-8');index=(ROOT/'frontend/index.html').read_text(encoding='utf-8')
    for place in ('Rome, Italy','Goa, India','Kyoto, Japan','Sydney, Australia','Antarctica','Bali, Indonesia'):
        assert place in app or place in index
    assert 'hero-cinematic' in app and 'sceneMainCard' in app and 'data-scene-dest' in app
    assert 'id="citypulseGlobe"' not in app and 'heroBuddy3D' not in index
    globe=(ROOT/'frontend/globe.js').read_text(encoding='utf-8')
    assert 'cityPulseOpenDestination' in globe and 'Bali, Indonesia' in globe and 'place.name,b' in globe
    assert 'Nagpur' not in app+index and 'Civic Pulse' not in app+index


def test_bloop_is_a_compact_bottom_right_travel_companion():
    index=(ROOT/'frontend/index.html').read_text(encoding='utf-8')
    app=(ROOT/'frontend/app.js').read_text(encoding='utf-8')
    css=(ROOT/'frontend/styles.css').read_text(encoding='utf-8')
    assert 'id="bloopDock"' in index and 'id="bloopLauncher"' in index
    assert 'bloopMiniArt' in index and 'bloop-pupil' in index
    assert 'function wireBloopDock' in app and 'moveEyes' in app
    assert '.bloop-dock{position:fixed' in css
    assert 'width:76px;height:76px' in css and 'width:66px;height:66px' in css


def test_cinematic_destination_scene_reacts_to_pointer():
    app=(ROOT/'frontend/app.js').read_text(encoding='utf-8');css=(ROOT/'frontend/styles.css').read_text(encoding='utf-8')
    assert 'pointermove' in app and '--scene-tilt-x' in app and '--scene-tilt-y' in app
    assert 'map-click-ripple' in css and 'heroMapStage' in app


def test_explore_keeps_selected_destination_in_map_and_offline_atlas_is_interactive():
    source=(ROOT/'frontend/feature-upgrades.js').read_text(encoding='utf-8')
    assert 'offline-atlas-map' in source and 'offline-map-marker' in source
    assert 'renderDestinationDetails(place' in source and 'data-offline-dest' in source
    assert 'destinationDetails' in source and 'atlas-destination-card' in source

def test_deployment_has_persistent_database_secure_cookie_and_health_check():
    blueprint=(ROOT/'render.yaml').read_text(encoding='utf-8');docker=(ROOT/'Dockerfile').read_text(encoding='utf-8')
    assert 'name: travesia' in blueprint and 'mountPath: /app/instance' in blueprint
    assert 'CITYPULSEX_DB' in blueprint and 'COOKIE_SECURE' in blueprint and 'healthCheckPath: /api/health' in blueprint
    assert 'gunicorn --bind 0.0.0.0:${PORT:-5000}' in docker

def test_release_is_travesia_only_and_no_water_application():
    app=(ROOT/'app.py').read_text(encoding='utf-8');docker=(ROOT/'Dockerfile').read_text(encoding='utf-8');workflow=(ROOT/'.github/workflows/tests.yml').read_text(encoding='utf-8')
    assert 'WATER_DIR' not in app and '"/water/"' not in app and 'WATER_DIR' not in docker
    assert 'water service' not in workflow.lower()
