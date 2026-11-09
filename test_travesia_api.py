"""Flask API smoke tests; run in CI after installing requirements-dev.txt."""
from __future__ import annotations
import io
from datetime import datetime, timezone
import pytest

# Flask HTTP/auth coverage is mandatory for the full release suite. If the app
# dependencies are missing, collection fails with an actionable message; it is
# never reported as a passing run with this module silently skipped.
try:
    import flask  # noqa: F401
    import werkzeug  # noqa: F401
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "TRAVESÍA HTTP/auth tests require Flask and Werkzeug. "
        "Run verify_windows.bat or install requirements-dev.txt before pytest."
    ) from exc
import app as citypulsex

@pytest.fixture()
def client(tmp_path, monkeypatch):
    previous=citypulsex.app.config.get('DATABASE')
    citypulsex.app.config['DATABASE']=str(tmp_path/'citypulsex-test.sqlite3')
    monkeypatch.setenv('CITYPULSEX_ADMIN_EMAIL','admin-test@example.com')
    monkeypatch.setenv('CITYPULSEX_ADMIN_PASSWORD','unique-test-password-at-least-20')
    monkeypatch.delenv('AMADEUS_CLIENT_ID',raising=False);monkeypatch.delenv('AMADEUS_CLIENT_SECRET',raising=False)
    monkeypatch.delenv('MAPTILER_API_KEY',raising=False);monkeypatch.delenv('LLM_API_KEY',raising=False)
    citypulsex.init_database()
    with citypulsex.app.test_client() as c:
        assert c.get('/api/health').json['status']=='ok'
        login=c.post('/api/auth/login',json={'email':'admin-test@example.com','password':'unique-test-password-at-least-20'})
        assert login.status_code==200
        yield c
    citypulsex.app.config['DATABASE']=previous

def csrf_headers(client):
    session=client.get('/api/auth/me');assert session.status_code==200 and session.json.get('authenticated')
    return {'X-CSRF-Token':session.json['csrf_token']}

def test_shell_assets_and_travesia_only_capabilities(client):
    assert client.get('/').status_code==200
    for path in ('/extensions.js','/pulseboard.js','/pulseboard.css','/expense-ledger.js','/providers.js','/glb-viewer.js','/companion-3d.js','/world-game.js','/globe.js'):
        assert client.get(path).status_code==200,path
    assert client.get('/assets/companions3d/bloop.glb').status_code==200
    caps=client.get('/api/capabilities').json
    assert 'world_explorer' in caps['modules'] and 'civic_complaints' not in caps['modules']
    assert client.get('/api/complaints').status_code==404
    assert client.get('/api/civic/overview').status_code==404
    assert caps['official_links']['ixigo_flights']=='https://www.ixigo.com/flights'
    assert caps['official_links']['ixigo_trains']=='https://www.ixigo.com/trains'

def test_health_security_headers_and_account_sessions(client):
    response=client.get('/api/health');assert response.status_code==200
    with citypulsex.connect_db() as conn:
        tables={row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'users','auth_sessions','shared_trips','rate_limit_buckets'} <= tables
    assert response.headers.get('X-Content-Type-Options')=='nosniff'
    assert response.headers.get('Referrer-Policy')=='strict-origin-when-cross-origin'
    anon=citypulsex.app.test_client()
    registered=anon.post('/api/auth/register',json={'display_name':'Normal Member','email':'member@example.com','password':'member-password-at-least-12'})
    assert registered.status_code==200 and registered.json['user']['role']=='member'
    cookies=registered.headers.getlist('Set-Cookie');session=next(x for x in cookies if x.startswith('citypulsex_session='))
    assert 'HttpOnly' in session and 'SameSite=Lax' in session
    assert anon.get('/api/auth/me').json['authenticated'] is True

def test_trip_fit_explains_heuristic_and_rejects_invalid_inputs(client):
    result=client.post('/api/trip/fit',json={'people':4,'budget_per_person':3000,'days':4,'vibe':'low-cost'})
    assert result.status_code==200
    body=result.json;assert len(body['recommendations'])==5
    assert body['recommendations'][0]['score']>=body['recommendations'][-1]['score']
    assert body['method']['data_mode']=='illustrative_heuristic_not_live_prices_or_personalised_AI'
    invalid=client.post('/api/trip/fit',json={'people':0,'budget_per_person':-10,'days':100,'vibe':'unicorn'})
    assert invalid.status_code==400

def test_scenarios_are_illustrative_and_validated(client):
    response=client.post('/api/scenarios/run',json={'scenario_type':'route','intensity':4,'budget':50000,'days':4})
    assert response.status_code==200
    assert response.json['data_mode']=='illustrative_rule_based_travel_scenario'
    assert response.json['official_assessment'] is False
    assert response.json['official_risk_assessment'] is False
    bad=client.post('/api/scenarios/run',json={'scenario_type':'unknown','intensity':99,'budget':-2,'days':0})
    assert bad.status_code==400

def test_chat_local_fallback_and_input_validation(client,monkeypatch):
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    assert client.post('/api/companion/chat',json={'message':'  '}).status_code==400
    result=client.post('/api/companion/chat',json={'message':'Plan a trip','companion':'Bloop','history':[{'role':'user','content':'Hello'}]})
    assert result.status_code==200 and result.json['configured'] is False and result.json['mode']=='local_fallback'

def test_clip_storyboard_requires_auth_csrf_consent_and_provider(client,monkeypatch):
    anon=citypulsex.app.test_client()
    denied=anon.post('/api/media/clip-storyboard')
    assert denied.status_code==401
    bad_csrf=client.post('/api/media/clip-storyboard',data={'consent':'on','video':(io.BytesIO(b'fake'),'clip.mp4')},content_type='multipart/form-data')
    assert bad_csrf.status_code==403
    no_consent=client.post('/api/media/clip-storyboard',data={'video':(io.BytesIO(b'fake'),'clip.mp4')},content_type='multipart/form-data',headers=csrf_headers(client))
    assert no_consent.status_code==400
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    not_configured=client.post('/api/media/clip-storyboard',data={'consent':'on','video':(io.BytesIO(b'fake'),'clip.mp4')},content_type='multipart/form-data',headers=csrf_headers(client))
    assert not_configured.status_code==503 and 'LLM_API_KEY' in not_configured.json['error']

def test_provider_handoffs_and_config_are_truthfully_labelled(client):
    flight=client.post('/api/travel/flights/offers',json={'origin':'DEL','destination':'GOI','departure_date':datetime.now(timezone.utc).date().isoformat(),'adults':1})
    assert flight.status_code==503 and flight.json['data_mode']=='not_configured'
    assert {a['provider'] for a in flight.json['alternatives']}=={'Google Flights','KAYAK','ixigo Flights'}
    assert all(a['mode']=='external_live_search' for a in flight.json['alternatives'])
    status=client.get('/api/providers/status').json
    assert any(x['type']=='flight_search_handoff' and x['name']=='ixigo Flights' for x in status['providers'])
    assert any(x['type']=='train_booking_handoff' and x['name'].startswith('ixigo Trains') for x in status['providers'])
    assert status['provider_onboarding']['rail']['recommended_path']=='affiliate_or_associate_of_an_existing_irctc_b2c_psp'
    assert status['provider_onboarding']['flights']['ticket_issuance_status']=='consolidator_agreement_required'
    assert client.get('/api/travel/weather?latitude=120&longitude=79').status_code==400
    maps=client.get('/api/maps/config').json
    assert maps['satellite_enabled'] is True and maps['nasa_fallback_available'] is True
    assert any(x['id']=='nasa_gibs' for x in maps['layers']) and maps['maptiler_enabled'] is False

def test_shared_trip_read_edit_token_conflict_and_validation(client):
    state={'people':['Asha','Riya'],'expenses':[],'avatars':{},'characters':{'Asha':'pikachu','Riya':'iron-man'}}
    created=client.post('/api/shared-trips',json={'name':'Trip','state':state});assert created.status_code==201
    code,token=created.json['share_code'],created.json['editor_token']
    loaded=client.get(f'/api/shared-trips/{code}');assert loaded.status_code==200
    assert loaded.json['state']['characters']==state['characters']
    other=citypulsex.app.test_client()
    denied=other.put(f'/api/shared-trips/{code}',json={'state':state,'expected_updated_at':loaded.json['updated_at']},headers={'X-Shared-Trip-Editor':'bad-token'})
    assert denied.status_code==403
    missing_version=other.put(f'/api/shared-trips/{code}',json={'state':state},headers={'X-Shared-Trip-Editor':token})
    assert missing_version.status_code==428
    headers={'X-Shared-Trip-Editor':token}
    changed={**state,'expenses':[{'id':'e1','description':'Train','amount':500,'paidBy':'Asha','splitWith':['Asha','Riya']}]}
    ok=other.put(f'/api/shared-trips/{code}',json={'state':changed,'expected_updated_at':loaded.json['updated_at']},headers=headers)
    assert ok.status_code==200
    conflict=other.put(f'/api/shared-trips/{code}',json={'state':state,'expected_updated_at':loaded.json['updated_at']},headers=headers)
    assert conflict.status_code==409 and conflict.json['conflict'] is True
    invalid=client.post('/api/shared-trips',json={'name':'Bad','state':{'people':['A','B'],'expenses':[{'description':'oops','amount':400,'paidBy':'A','splitWith':['No one']}],'avatars':{}}})
    assert invalid.status_code==400
    duplicate_characters=client.post('/api/shared-trips',json={'name':'Duplicate crew','state':{'people':['A','B'],'expenses':[],'avatars':{},'characters':{'A':'pikachu','B':'pikachu'}}})
    assert duplicate_characters.status_code==400 and 'characters' in duplicate_characters.json['fields']

def test_csrf_required_for_state_mutations(client):
    no_csrf=client.post('/api/auth/logout')
    assert no_csrf.status_code==403
    with_csrf=client.post('/api/auth/logout',headers=csrf_headers(client))
    assert with_csrf.status_code==200



def test_auth_logout_rejects_cross_origin_and_csrf_is_mandatory(client):
    csrf = csrf_headers(client)['X-CSRF-Token']
    cross_origin = client.post('/api/auth/logout', headers={
        'Origin': 'https://attacker.example', 'X-CSRF-Token': csrf,
    })
    assert cross_origin.status_code == 403
    missing_csrf = client.post('/api/auth/logout')
    assert missing_csrf.status_code == 403
    valid = client.post('/api/auth/logout', headers={'X-CSRF-Token': csrf})
    assert valid.status_code == 200
    assert client.get('/api/auth/me').json['authenticated'] is False


def test_rate_limiter_uses_hashed_persistent_buckets(client):
    with citypulsex.app.test_request_context('/', environ_base={'REMOTE_ADDR': '192.0.2.44'}):
        assert citypulsex.rate_limit_response('unit-test', 1, 60, 'member@example.com') is None
        blocked = citypulsex.rate_limit_response('unit-test', 1, 60, 'member@example.com')
        assert blocked.status_code == 429
        assert int(blocked.headers['Retry-After']) >= 1
    with citypulsex.connect_db() as conn:
        rows = conn.execute("SELECT bucket_key FROM rate_limit_buckets").fetchall()
    assert rows and all('member@example.com' not in row['bucket_key'] for row in rows)


def test_login_endpoint_applies_persistent_rate_limit(client, monkeypatch):
    monkeypatch.setattr(citypulsex, 'rate_limit_response', lambda *args, **kwargs: (citypulsex.jsonify({'error':'limited'}), 429))
    response = client.post('/api/auth/login', json={'email':'member@example.com','password':'wrong-password'})
    assert response.status_code == 429


def test_registration_cannot_self_assign_admin_and_login_rotates_server_session(client):
    member = citypulsex.app.test_client()
    registered = member.post('/api/auth/register', json={
        'display_name': 'Regular Member',
        'email': 'role-test@example.com',
        'password': 'member-password-at-least-12',
        'role': 'admin',
    })
    assert registered.status_code == 200
    assert registered.json['user']['role'] == 'member'
    cookie = member.get_cookie('citypulsex_session')
    assert cookie and cookie.value
    old_hash = citypulsex._sha256_secret(cookie.value)
    with citypulsex.connect_db() as conn:
        assert conn.execute('SELECT 1 FROM auth_sessions WHERE token_hash=?', (old_hash,)).fetchone()

    logged_in = member.post('/api/auth/login', json={
        'email': 'role-test@example.com',
        'password': 'member-password-at-least-12',
    })
    assert logged_in.status_code == 200
    with citypulsex.connect_db() as conn:
        assert conn.execute('SELECT 1 FROM auth_sessions WHERE token_hash=?', (old_hash,)).fetchone() is None
    assert member.get('/api/auth/me').json['authenticated'] is True


def test_cross_site_fetch_metadata_rejects_api_mutations(client):
    response = client.post('/api/trip/fit', json={
        'people': 2, 'budget_per_person': 5000, 'days': 3, 'vibe': 'relaxed',
    }, headers={'Sec-Fetch-Site': 'cross-site'})
    assert response.status_code == 403
    assert 'Cross-origin' in response.json['error']


def test_health_reports_incomplete_schema_instead_of_false_ready(client, tmp_path):
    previous = citypulsex.app.config['DATABASE']
    citypulsex.app.config['DATABASE'] = str(tmp_path / 'empty.sqlite3')
    try:
        response = client.get('/api/health')
        assert response.status_code == 503
        assert response.json['status'] == 'degraded'
        assert response.json['database'] == 'schema_incomplete'
    finally:
        citypulsex.app.config['DATABASE'] = previous
