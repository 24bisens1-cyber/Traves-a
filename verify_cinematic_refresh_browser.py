#!/usr/bin/env python3
"""Offline-capable browser checks for the TRAVESÍA visual refresh."""
from __future__ import annotations
import base64, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; FRONT=ROOT/'frontend'
checks=[]; errors=[]
def check(name,ok,details=None):
    checks.append({'name':name,'pass':bool(ok),'details':details})
def uri(path):
    mime={'.svg':'image/svg+xml','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg'}.get(path.suffix,'application/octet-stream')
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
assets={name:uri(FRONT/'assets'/rel) for name,rel in {
 'goa.webp':'destinations/goa.webp','kyoto.webp':'destinations/kyoto.webp','antarctica.webp':'destinations/antarctica.webp',
 'rome.webp':'destinations/rome.webp','sydney.webp':'destinations/sydney.webp','india-inspiration.webp':'destinations/india-inspiration.webp',
 'bloop-mini.svg':'companions/bloop-mini.svg','bloop.svg':'companions/bloop.svg',
 'sprout.webp':'companions/sprout.webp','pip.webp':'companions/pip.webp','roo.webp':'companions/roo.webp',
 'mira.webp':'companions/mira.webp','orbit.webp':'companions/orbit.webp','paws.webp':'companions/paws.webp','world-map.svg':'world-map.svg',
 'travesia-globe-mark.webp':'brand/travesia-globe-mark.webp','pikachu-scene.png':'character-scenes/pikachu-scene.png','bulbasaur-scene.png':'character-scenes/bulbasaur-scene.png',
 'iron-man-scene.png':'character-scenes/iron-man-scene.png','spider-man-scene.png':'character-scenes/spider-man-scene.png','harry-potter-scene.png':'character-scenes/harry-potter-scene.png','hermione-scene.png':'character-scenes/hermione-scene.png'
}.items()}
html=(FRONT/'index.html').read_text(encoding='utf-8')
body=re.search(r'<body>(.*)</body>',html,re.S).group(1)
body=re.sub(r'<script[^>]+src="[^"]+"[^>]*>\s*</script>','',body)
body=re.sub(r'<link[^>]+>','',body)
for name,data in assets.items(): body=body.replace(f'src="assets/destinations/{name}"',f'src="{data}"').replace(f'src="assets/companions/{name}"',f'src="{data}"')
css=(FRONT/'styles.css').read_text(encoding='utf-8')+'\n'+(FRONT/'pulseboard.css').read_text(encoding='utf-8')+'\n'+(FRONT/'cinematic.css').read_text(encoding='utf-8')
for name,data in assets.items(): css=css.replace(f'url("assets/destinations/{name}")',f'url("{data}")').replace(f"url('assets/destinations/{name}')",f"url('{data}')")
script_names=['providers.js','glb-viewer.js','companion-3d.js','expense-ledger.js','friend-characters.js','world-game.js','app.js','extensions.js','pulseboard.js','feature-upgrades.js','cinematic.js']
scripts=[]
for name in script_names:
    source=(FRONT/name).read_text(encoding='utf-8')
    for asset,data in assets.items():
        source=source.replace(f'"assets/destinations/{asset}"',f'"{data}"').replace(f"'assets/destinations/{asset}'",f"'{data}'")
        source=source.replace(f'"assets/companions/{asset}"',f'"{data}"').replace(f"'assets/companions/{asset}'",f"'{data}'")
        source=source.replace(f'"/assets/companions/{asset}"',f'"{data}"').replace(f"'/assets/companions/{asset}'",f"'{data}'")
    source=source.replace('\"assets/world-map.svg\"', '\"'+assets['world-map.svg']+'\"').replace("'assets/world-map.svg'", "'"+assets['world-map.svg']+"'")
    for asset_name, data_uri in assets.items():
        source=source.replace(f'"assets/character-avatars/{asset_name}"', f'"{data_uri}"').replace(f"'assets/character-avatars/{asset_name}'", f"'{data_uri}'")
        source=source.replace(f'"assets/character-scenes/{asset_name}"', f'"{data_uri}"').replace(f"'assets/character-scenes/{asset_name}'", f"'{data_uri}'")
        source=source.replace(f'"assets/brand/{asset_name}"', f'"{data_uri}"').replace(f"'assets/brand/{asset_name}'", f"'{data_uri}'")
    scripts.append(source)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--enable-webgl','--ignore-gpu-blocklist'])
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    # Keep external place enrichment deterministic and offline in this browser suite.
    page.route(re.compile(r'^https://en\.wikipedia\.org/'),lambda route:route.fulfill(status=200,content_type='application/json',body='{"query":{"pages":{}}}'))
    page.route(re.compile(r'^https://nominatim\.openstreetmap\.org/'),lambda route:route.fulfill(status=200,content_type='application/json',body='{}'))
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+css+'</style></head><body>'+body+'</body></html>',wait_until='domcontentloaded')
    for source in scripts: page.add_script_tag(content=source)
    page.wait_for_selector('#sceneMainCard',timeout=10000)
    page.wait_for_timeout(250)
    check('new home postcard hero rendered',page.locator('#sceneMainCard').count()==1)
    check('obsolete black globe is absent',page.locator('#citypulseGlobe').count()==0 and page.locator('#heroBuddy3D').count()==0)
    check('compact Bloop dock is mounted once',page.locator('#bloopLauncher').count()==1 and page.locator('#heroGuideChat').count()==1)
    b=page.locator('#bloopLauncher').evaluate('(e)=>({w:e.offsetWidth,h:e.offsetHeight,r:innerWidth-e.getBoundingClientRect().right,b:innerHeight-e.getBoundingClientRect().bottom})')
    check('Bloop is small and bottom-right',44<=b['w']<=55 and 44<=b['h']<=55 and b['r']<30 and b['b']<30,b)
    page.locator('#bloopLauncher').click(); check('Bloop opens its chat',page.locator('#heroGuideChat').evaluate('(e)=>!e.hidden'))
    no_halo=page.locator('.bloop-launcher-halo').evaluate('(e)=>getComputedStyle(e).display==="none"')
    no_badge=page.locator('.bloop-online-dot').evaluate('(e)=>getComputedStyle(e).display==="none"')
    check('Bloop is a clean character with no oversized badge or halo',no_halo and no_badge)
    page.locator('#bloopLauncher').evaluate('(e)=>e.classList.add("is-blinking")')
    blink_name=page.locator('#bloopMiniArt .bloop-eyes').evaluate('(e)=>getComputedStyle(e).animationName')
    art_name=page.locator('#bloopMiniArt').evaluate('(e)=>getComputedStyle(e).animationName')
    check('Bloop blinks its eyes rather than shrinking its whole body','bloopEyeBlink' in blink_name and 'bloopBlink' not in art_name,{'eyes':blink_name,'body':art_name})
    page.locator('#bloopLauncher').evaluate('(e)=>e.classList.remove("is-blinking")')
    pupil_before=page.locator('#bloopMiniArt .bloop-pupil').first.get_attribute('transform')
    page.locator('#bloopLauncher').dispatch_event('pointermove',{'clientX':40,'clientY':30,'pointerType':'mouse'})
    pupil_after=page.locator('#bloopMiniArt .bloop-pupil').first.get_attribute('transform')
    check('Bloop eyes respond to pointer movement',pupil_before!=pupil_after,{'before':pupil_before,'after':pupil_after})
    page.locator('#heroGuideClose').click()
    page.locator('[data-scene-dest="Kyoto, Japan"]').click(); page.wait_for_timeout(220)
    check('hero destination selector works',page.locator('#sceneDestinationName').inner_text()=='Kyoto, Japan')
    hero_before=page.locator('#sceneMainImage').get_attribute('src')
    page.locator('#sceneFloatIce').click(); page.wait_for_function("(previous) => document.querySelector('#sceneDestinationName')?.textContent==='Antarctica' && document.querySelector('#sceneMainImage')?.src!==previous",arg=hero_before,timeout=3000)
    check('clicking the Antarctica floating postcard replaces the large centre scene',page.locator('#sceneDestinationName').inner_text()=='Antarctica' and 'Antarctica' in page.locator('#sceneMainImage').get_attribute('alt') and page.locator('#sceneFloatIce').get_attribute('aria-pressed')=='true')
    hero_before=page.locator('#sceneMainImage').get_attribute('src')
    page.locator('#sceneFloatKyoto').click(); page.wait_for_function("(previous) => document.querySelector('#sceneDestinationName')?.textContent==='Kyoto, Japan' && document.querySelector('#sceneMainImage')?.src!==previous",arg=hero_before,timeout=3000)
    check('clicking the Kyoto floating postcard replaces the large centre scene',page.locator('#sceneDestinationName').inner_text()=='Kyoto, Japan' and 'Kyoto' in page.locator('#sceneMainImage').get_attribute('alt') and page.locator('#sceneFloatKyoto').get_attribute('aria-pressed')=='true')
    check('Portal Run is a travel scene, not a planet demo',page.locator('.game-travel-portal').count()==1 and page.locator('.game-world-planet').count()==0)
    page.locator('#gameStart').click(); page.locator('#gameTarget').evaluate('(e)=>{for(let i=0;i<7;i++)e.click()}')
    check('Portal Run still plays and unlocks',page.locator('#gameScore').inner_text().strip()=='07' and page.locator('#gameWinOverlay').is_visible())
    page.locator('[data-view="explore"]').first.click(); page.wait_for_selector('.atlas-map-wrap')
    check('Explore uses the new full-width map composition',page.locator('.atlas-map-wrap').count()==1 and page.locator('.atlas-place-grid').count()==1)
    check('offline map fallback displays illustrated atlas',page.locator('#map .offline-atlas-map').count()==1)
    map_pixels=page.locator('.offline-atlas-art').evaluate('(e)=>({width:e.naturalWidth,height:e.naturalHeight,complete:e.complete})')
    check('bundled world map artwork loads offline',map_pixels['complete'] and map_pixels['width']>=1000,map_pixels)
    check('offline map includes six working destination pins',page.locator('#map .offline-map-marker').count()==6)
    page.locator('#map [data-offline-dest="1"]').click()
    check('offline map pin opens its destination preview',page.locator('#destinationDetails h3').inner_text()=='Kyoto, Japan')
    check('selected place card is inside the map',page.locator('.atlas-map-wrap #destinationDetails').count()==1)
    count=page.locator('.atlas-destination-card').count(); check('six postcards appear below map',count==6,{'count':count})
    page.locator('.atlas-destination-card').filter(has_text='Goa').click()
    check('opening a destination fills the in-map preview',page.locator('#destinationDetails .map-preview-card').count()==1)
    place_title=page.locator('#destinationDetails h3').inner_text() if page.locator('#destinationDetails h3').count() else ''
    check('map preview shows selected destination', 'Goa' in place_title,{'title':place_title})
    page.locator('[data-filter="culture"]').click(); visible=page.locator('.atlas-destination-card:visible').count()
    check('destination filters respond',visible>0 and visible<6,{'visible':visible})
    page.locator('[data-filter="all"]').click()
    # Friend 1 must use a real, distinctive local traveller portrait, not a broken
    # bloop.webp path or the browser's alt-text placeholder.
    page.locator('[data-view="split"]').first.click(); page.wait_for_selector('.split-person')
    friend_cards=page.locator('.split-person')
    friend_images=page.locator('.split-person .split-avatar img')
    page.wait_for_function("Array.from(document.querySelectorAll('.split-person .split-avatar img')).length===4 && Array.from(document.querySelectorAll('.split-person .split-avatar img')).every(img=>img.complete && img.naturalWidth>0)", timeout=5000)
    check('split ledger shows four editable crew profiles',friend_cards.count()==4 and friend_images.count()==4,{'cards':friend_cards.count(),'images':friend_images.count()})
    first_avatar=friend_images.first.evaluate('(e)=>({src:e.getAttribute("src"),alt:e.alt,width:e.naturalWidth,height:e.naturalHeight,complete:e.complete})')
    check('Friend 1 starts with the supplied Pikachu artwork', 'Pikachu' in first_avatar['alt'] and first_avatar['width']>=100 and first_avatar['height']>=100 and first_avatar['complete'],first_avatar)
    all_avatar_states=friend_images.evaluate_all('(items)=>items.map(e=>({alt:e.alt,width:e.naturalWidth,height:e.naturalHeight,complete:e.complete,character:e.closest(".split-avatar").dataset.characterId}))')
    check('all four default friend portraits load and use different characters',all(x['complete'] and x['width']>=100 and x['height']>=100 for x in all_avatar_states) and len({x['character'] for x in all_avatar_states})==4,all_avatar_states)
    check('first four friends receive different supplied character art', [x['character'] for x in all_avatar_states] == ['pikachu','bulbasaur','iron-man','spider-man'], all_avatar_states)
    page.locator('.choose-friend-character').first.click();page.wait_for_selector('#friendCharacterBackdrop:not([hidden])')
    check('friend character picker opens with all supplied character options',page.locator('.friend-character-choice').count()==13)
    picker_art=page.locator('.friend-character-choice-art img').evaluate_all('(items)=>items.slice(0,6).map(e=>({src:e.getAttribute("src"),fit:getComputedStyle(e).objectFit,radius:getComputedStyle(e).borderRadius,w:e.naturalWidth,h:e.naturalHeight}))')
    check('uploaded characters retain original backgrounds in square animated-scene frames',len(picker_art)==6 and all(x['src'].startswith('data:image/png') and x['fit']=='contain' and x['radius']=='13px' and x['w']>50 and x['h']>70 for x in picker_art),picker_art)
    page.screenshot(path='/mnt/data/TRAVESÍA_Friend_Character_Picker.png',full_page=False)
    page.locator('[data-character-choice="pikachu"]').click();page.wait_for_timeout(100)
    check('selecting Pikachu assigns it to Friend 1 and closes the picker',page.locator('.split-person').first.locator('.split-avatar').get_attribute('data-character-id')=='pikachu' and page.locator('#friendCharacterBackdrop').is_hidden())
    for _ in range(8): page.locator('#addSplitPerson').click()
    page.wait_for_timeout(120)
    crew_characters=page.locator('.split-person .split-avatar').evaluate_all('(items)=>items.map(e=>e.dataset.characterId)')
    check('twelve friends never receive a repeated character',len(crew_characters)==12 and len(set(crew_characters))==12,crew_characters)
    page.locator('.choose-friend-character').nth(1).click();page.wait_for_selector('#friendCharacterBackdrop:not([hidden])')
    check('a character already assigned to Friend 1 is locked for Friend 2',page.locator('[data-character-choice="pikachu"]').is_disabled())
    page.locator('#cancelFriendCharacterPicker').click()
    friend_cards.last.scroll_into_view_if_needed();page.wait_for_function("Array.from(document.querySelectorAll('.split-person .split-avatar img')).length===12 && Array.from(document.querySelectorAll('.split-person .split-avatar img')).every(img=>img.complete && img.naturalWidth>0)",timeout=8000)
    loaded_crew=page.locator('.split-person .split-avatar img').evaluate_all('(items)=>items.map(e=>({alt:e.alt,width:e.naturalWidth,src:e.getAttribute("src")}))')
    check('all twelve friend character portraits are real loaded images',len(loaded_crew)==12 and all(x['width']>=100 for x in loaded_crew),loaded_crew)
    friend_cards.first.scroll_into_view_if_needed(); page.wait_for_timeout(100)
    page.screenshot(path='/mnt/data/TRAVESÍA_Split_Expenses_Preview.png',full_page=False)
    # Secondary pages gain their own cinematic scene; the two discovery pages remain unchanged.
    for view in ['planner','mobility','citytwin','companion','squad','saved','split','pulse','experiences','account']:
        page.evaluate('(v)=>window.cityPulseSetView(v)',view);page.wait_for_timeout(120)
        has_scene=page.locator('#cpPageScene').count()==1
        check(f'{view} page has its own animated travel scene',has_scene,{'errors':errors,'page_text':page.locator('#page').inner_text()[:400]})
        if view=='planner':
            page.evaluate('window.scrollTo(0,0)')
            page.wait_for_timeout(900)
            page.screenshot(path='/mnt/data/TRAVESÍA_Trip_Studio_Motion_Preview.png',full_page=False)
        if has_scene:
            scene_image=page.locator('#cpPageSceneImage').evaluate('(e)=>({complete:e.complete,width:e.naturalWidth})')
            check(f'{view} scene artwork loads',scene_image['complete'] and scene_image['width']>0,scene_image)
            if view=='companion':
                check('Companion scene action is labelled for choosing a buddy',page.locator('#cpPageSceneUse').inner_text().startswith('Choose this buddy'))
            before=page.locator('#cpPageSceneName').inner_text();page.evaluate("document.querySelector('#cpPageSceneNext').click()");page.wait_for_timeout(250)
            after=page.locator('#cpPageSceneName').inner_text()
            check(f'{view} scene selector changes the visual chapter',after!=before,{'before':before,'after':after})
        else: break
    page.evaluate("window.cityPulseSetView('home')")
    check('Discover remains unchanged and has no secondary scene injection',page.locator('#cpPageScene').count()==0)
    page.evaluate("window.cityPulseSetView('explore')")
    check('Explore remains unchanged and has no secondary scene injection',page.locator('#cpPageScene').count()==0)
    page.locator('[data-view="home"]').first.click(); page.wait_for_selector('.story-chapter-art')
    story_art=page.locator('.story-chapter-art').first
    page.evaluate('document.documentElement.style.scrollBehavior="auto";document.body.style.scrollBehavior="auto"')
    story_card=page.locator('.story-chapter').first
    story_card.scroll_into_view_if_needed(); page.evaluate('window.dispatchEvent(new Event("scroll"))'); page.wait_for_timeout(180)
    check('travel story cards reveal when scrolled into view',story_card.evaluate('(e)=>e.classList.contains("is-in-view") && getComputedStyle(e).opacity==="1"'))
    story_lift_before=story_art.evaluate('(e)=>getComputedStyle(e).getPropertyValue("--cp-scroll-lift").trim()')
    page.evaluate('window.scrollBy({top:140,behavior:"instant"});window.dispatchEvent(new Event("scroll"))'); page.wait_for_timeout(180)
    story_lift_after=story_art.evaluate('(e)=>getComputedStyle(e).getPropertyValue("--cp-scroll-lift").trim()')
    check('travel story artwork receives scroll-linked camera motion',story_lift_before.endswith('px') and story_lift_after.endswith('px') and story_lift_before!=story_lift_after,{'before':story_lift_before,'after':story_lift_after})
    page.evaluate('window.scrollTo(0,0)'); page.wait_for_timeout(80)
    page.locator('[data-view="explore"]').first.click(); page.wait_for_selector('.atlas-map-wrap')
    page.screenshot(path='/mnt/data/TRAVESÍA_Explore_Atlas_Preview.png',full_page=False)
    page.set_viewport_size({'width':390,'height':844}); page.wait_for_timeout(100)
    metrics=page.evaluate('()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
    check('mobile Explore has no horizontal overflow',metrics['scroll']<=metrics['client']+2,metrics)
    bm=page.locator('#bloopLauncher').evaluate('(e)=>({w:e.offsetWidth,h:e.offsetHeight,r:innerWidth-e.getBoundingClientRect().right,b:innerHeight-e.getBoundingClientRect().bottom})')
    check('mobile Bloop remains compact and pinned',36<=bm['w']<=46 and bm['r']<20 and bm['b']<20,bm)
    page.evaluate("window.cityPulseSetView('home')"); page.set_viewport_size({'width':1440,'height':1000}); page.wait_for_timeout(160)
    # Walk the page once so intersection-triggered story/feature reveals are in
    # their finished state in the exported full-page preview (not blank frames).
    page.evaluate('document.documentElement.style.scrollBehavior="auto";document.body.style.scrollBehavior="auto"')
    max_scroll=page.evaluate('Math.max(0,document.documentElement.scrollHeight-window.innerHeight)')
    for scroll_y in range(0,int(max_scroll)+1,520):
        page.evaluate('(y)=>{window.scrollTo({top:y,behavior:"instant"});window.dispatchEvent(new Event("scroll"))}',scroll_y); page.wait_for_timeout(75)
    page.evaluate('window.scrollTo(0,0)'); page.wait_for_timeout(500)
    page.screenshot(path='/mnt/data/TRAVESÍA_Cinematic_Desktop_Preview.png',full_page=False)
    page.set_viewport_size({'width':390,'height':844}); page.wait_for_timeout(100)
    page.screenshot(path='/mnt/data/TRAVESÍA_Cinematic_Mobile_Preview.png',full_page=False)
    check('no uncaught browser JavaScript errors',len(errors)==0,errors)
    browser.close()
print(json.dumps({'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks,'browser_errors':errors},indent=2))
if sum(c['pass'] for c in checks)!=len(checks) or errors: raise SystemExit(1)
