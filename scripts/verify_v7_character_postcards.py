#!/usr/bin/env python3
"""Focused Chromium check for V9 dynamic postcard alternates and themed animated character tiles."""
from __future__ import annotations
import base64, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
FRONT=ROOT/'frontend'
errors=[]; results=[]
def check(name,ok,details=None):
    results.append((name,bool(ok),details))
def uri(path):
    mime={'.svg':'image/svg+xml','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg'}.get(path.suffix,'application/octet-stream')
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
asset_paths={
 'goa.webp':'destinations/goa.webp','kyoto.webp':'destinations/kyoto.webp','antarctica.webp':'destinations/antarctica.webp',
 'rome.webp':'destinations/rome.webp','sydney.webp':'destinations/sydney.webp','india-inspiration.webp':'destinations/india-inspiration.webp',
 'bloop-mini.svg':'companions/bloop-mini.svg','bloop.svg':'companions/bloop.svg',
 'sprout.webp':'companions/sprout.webp','pip.webp':'companions/pip.webp','roo.webp':'companions/roo.webp',
 'mira.webp':'companions/mira.webp','orbit.webp':'companions/orbit.webp','paws.webp':'companions/paws.webp',
 'world-map.svg':'world-map.svg','travesia-globe-mark.webp':'brand/travesia-globe-mark.webp',
 'pikachu-scene.png':'character-scenes/pikachu-scene.png','bulbasaur-scene.png':'character-scenes/bulbasaur-scene.png',
 'iron-man-scene.png':'character-scenes/iron-man-scene.png','spider-man-scene.png':'character-scenes/spider-man-scene.png',
 'harry-potter-scene.png':'character-scenes/harry-potter-scene.png','hermione-scene.png':'character-scenes/hermione-scene.png'
}
assets={name:uri(FRONT/'assets'/rel) for name,rel in asset_paths.items()}
html=(FRONT/'index.html').read_text(encoding='utf-8')
body=re.search(r'<body>(.*)</body>',html,re.S).group(1)
body=re.sub(r'<script[^>]+src="[^"]+"[^>]*>\s*</script>','',body)
body=re.sub(r'<link[^>]+>','',body)
css='\n'.join((FRONT/x).read_text(encoding='utf-8') for x in ['styles.css','pulseboard.css','cinematic.css'])
for name,data in assets.items():
    for rel in ['destinations','companions','character-avatars','character-scenes','brand']:
        body=body.replace(f'src="assets/{rel}/{name}"',f'src="{data}"')
        body=body.replace(f'assets/{rel}/{name}',data)
        css=css.replace(f'url("assets/{rel}/{name}")',f'url("{data}")').replace(f"url('assets/{rel}/{name}')",f"url('{data}')")
script_names=['providers.js','glb-viewer.js','companion-3d.js','expense-ledger.js','friend-characters.js','world-game.js','app.js','extensions.js','pulseboard.js','feature-upgrades.js','cinematic.js']
scripts=[]
for name in script_names:
    source=(FRONT/name).read_text(encoding='utf-8')
    for asset,data in assets.items():
        for rel in ['destinations','companions','character-avatars','character-scenes','brand']:
            source=source.replace(f'"assets/{rel}/{asset}"',f'"{data}"').replace(f"'assets/{rel}/{asset}'",f"'{data}'")
    source=source.replace('"assets/world-map.svg"','"'+assets['world-map.svg']+'"').replace("'assets/world-map.svg'","'"+assets['world-map.svg']+"'")
    scripts.append(source)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--enable-webgl','--ignore-gpu-blocklist'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+css+'</style></head><body>'+body+'</body></html>',wait_until='domcontentloaded')
    for source in scripts: page.add_script_tag(content=source)
    page.wait_for_selector('#sceneMainCard',timeout=12000)
    page.wait_for_timeout(400)
    page.screenshot(path='/mnt/data/TRAVESÍA_V10_Home_Goa.png',full_page=False)
    initial=page.locator('#sceneMainImage').get_attribute('src')
    page.locator('[data-postcard-dest="Antarctica"]').click(force=True,timeout=4000)
    page.wait_for_function("(initial)=>document.querySelector('#sceneDestinationName')?.textContent==='Antarctica' && document.querySelector('#sceneMainImage')?.src!==initial",arg=initial,timeout=4000)
    ice=page.locator('#sceneMainImage').evaluate('(e)=>({alt:e.alt,complete:e.complete,w:e.naturalWidth,h:e.naturalHeight})')
    check('Antarctica floating postcard replaces the large middle scene',page.locator('#sceneDestinationName').inner_text()=='Antarctica' and 'Antarctic' in ice['alt'] and ice['complete'] and ice['w']>200,ice)
    current_alternatives=page.locator('[data-postcard-dest]').evaluate_all('(items)=>items.map(e=>e.dataset.postcardDest)')
    check('Antarctica selected: Goa and Kyoto appear as the two floating return/alternate cards',current_alternatives==['Goa, India','Kyoto, Japan'],current_alternatives)
    check('Antarctica bottom selector follows the postcard selection',page.locator('[data-scene-dest="Antarctica"]').get_attribute('aria-pressed')=='true' and page.locator('[data-scene-dest="Goa, India"]').get_attribute('aria-pressed')=='false')
    page.wait_for_timeout(800)
    page.screenshot(path='/mnt/data/TRAVESÍA_V10_Antarctica_Selected.png',full_page=False)
    mid=page.locator('#sceneMainImage').get_attribute('src')
    page.locator('[data-postcard-dest="Goa, India"]').click(force=True,timeout=4000)
    page.wait_for_function("(initial)=>document.querySelector('#sceneDestinationName')?.textContent==='Goa, India' && document.querySelector('#sceneMainImage')?.src!==initial",arg=mid,timeout=4000)
    goa=page.locator('#sceneMainImage').evaluate('(e)=>({alt:e.alt,complete:e.complete,w:e.naturalWidth,h:e.naturalHeight})')
    check('Goa floating return postcard restores Goa to the central scene',page.locator('#sceneDestinationName').inner_text()=='Goa, India' and 'Goa' in goa['alt'] and goa['complete'] and goa['w']>200,goa)
    current_alternatives=page.locator('[data-postcard-dest]').evaluate_all('(items)=>items.map(e=>e.dataset.postcardDest)')
    check('Goa selected: Kyoto and Antarctica return to the floating cards',current_alternatives==['Kyoto, Japan','Antarctica'],current_alternatives)
    mid=page.locator('#sceneMainImage').get_attribute('src')
    page.locator('[data-postcard-dest="Kyoto, Japan"]').click(force=True,timeout=4000)
    page.wait_for_function("(initial)=>document.querySelector('#sceneDestinationName')?.textContent==='Kyoto, Japan' && document.querySelector('#sceneMainImage')?.src!==initial",arg=mid,timeout=4000)
    kyoto=page.locator('#sceneMainImage').evaluate('(e)=>({alt:e.alt,complete:e.complete,w:e.naturalWidth,h:e.naturalHeight})')
    check('Kyoto floating postcard replaces the large middle scene',page.locator('#sceneDestinationName').inner_text()=='Kyoto, Japan' and 'Kyoto' in kyoto['alt'] and kyoto['complete'] and kyoto['w']>200,kyoto)
    current_alternatives=page.locator('[data-postcard-dest]').evaluate_all('(items)=>items.map(e=>e.dataset.postcardDest)')
    check('Kyoto selected: Goa returns as a floating one-click return card',current_alternatives==['Goa, India','Antarctica'],current_alternatives)
    check('Kyoto bottom selector follows the postcard selection',page.locator('[data-scene-dest="Kyoto, Japan"]').get_attribute('aria-pressed')=='true' and page.locator('[data-scene-dest="Goa, India"]').get_attribute('aria-pressed')=='false')
    page.wait_for_timeout(800)
    page.screenshot(path='/mnt/data/TRAVESÍA_V10_Kyoto_Selected.png',full_page=False)
    page.locator('[data-view="split"]').first.click();page.wait_for_selector('.split-person',timeout=6000)
    page.wait_for_function("Array.from(document.querySelectorAll('.split-person .split-avatar img')).length===4 && Array.from(document.querySelectorAll('.split-person .split-avatar img')).every(i=>i.complete&&i.naturalWidth>0)",timeout=6000)
    avatars=page.locator('.split-person .split-avatar').evaluate_all('(items)=>items.map(e=>{const r=e.getBoundingClientRect(),i=e.querySelector("img"),s=getComputedStyle(i);return {alt:i.alt,width:i.naturalWidth,height:i.naturalHeight,fit:s.objectFit,radius:s.borderRadius,scenePng:i.getAttribute("src").startsWith("data:image/png"),boxWidth:r.width,boxHeight:r.height,animation:s.animationName,boxRadius:getComputedStyle(e).borderRadius}})')
    check('default friends use full original-background scenes inside identical square stages',len(avatars)==4 and all(x['fit']=='contain' and x['scenePng'] and x['radius']=='13px' and x['width']>80 and x['height']>80 and abs(x['boxWidth']-x['boxHeight'])<0.5 and x['animation']!='none' for x in avatars),avatars)
    page.locator('.split-panel').scroll_into_view_if_needed()
    page.wait_for_function("document.querySelectorAll('.split-person.is-in-view').length===4 && document.querySelector('.split-panel')?.classList.contains('is-in-view')",timeout=5000)
    page.wait_for_function("Array.from(document.querySelectorAll('.split-person')).every(e=>Number(getComputedStyle(e).opacity)>.98)",timeout=3000)
    page.screenshot(path='/mnt/data/TRAVESÍA_V10_Split_Expenses_Preview.png',full_page=False)
    page.locator('.choose-friend-character').first.click();page.wait_for_selector('#friendCharacterBackdrop:not([hidden])')
    page.evaluate('window.scrollTo(0,0)')
    art=page.locator('.friend-character-choice-art').evaluate_all('(items)=>items.map(e=>{const r=e.getBoundingClientRect(),i=e.querySelector("img"),s=getComputedStyle(i);return {alt:i.alt,fit:s.objectFit,radius:s.borderRadius,complete:i.complete,w:i.naturalWidth,h:i.naturalHeight,boxWidth:r.width,boxHeight:r.height,animation:s.animationName,id:e.dataset.characterId}})')
    check('all picker characters use identical square stages and original-background animated scenes',len(art)==13 and all(x['fit']=='contain' and x['radius']=='13px' and x['complete'] and x['w']>80 and x['h']>80 and abs(x['boxWidth']-x['boxHeight'])<0.5 and x['animation']!='none' for x in art),art)
    tile_backgrounds=page.locator('.friend-character-choice-art').evaluate_all('(items)=>items.map(e=>({id:e.dataset.characterId,bg:getComputedStyle(e).backgroundImage,glow:getComputedStyle(e,"::before").backgroundImage,glowAnimation:getComputedStyle(e,"::before").animationName,sparkle:getComputedStyle(e,"::after").animationName}))')
    check('all 13 characters have an animated scene backdrop and light-sweep layer',len(tile_backgrounds)==13 and all(x['glow']!='none' and x['glowAnimation']=='cpFullSceneBackdrop' and x['sparkle']=='cpFullSceneLightSweep' for x in tile_backgrounds),tile_backgrounds)
    check('all 13 characters use 13 distinct idle animation rhythms',len(set(x['animation'] for x in art))==13,[x['animation'] for x in art])
    locked=page.locator('.friend-character-choice:disabled').evaluate_all('(items)=>items.map(e=>({opacity:getComputedStyle(e).opacity,filter:getComputedStyle(e).filter,disabled:e.disabled}))')
    check('used characters stay full-colour while their buttons remain locked',len(locked)>=3 and all(x['opacity']=='1' and x['filter']=='none' and x['disabled'] for x in locked),locked)
    page.screenshot(path='/mnt/data/TRAVESÍA_V10_Character_Picker_Preview.png',full_page=True)
    check('no uncaught browser errors',not errors,errors)
    page.locator('#cancelFriendCharacterPicker').click(force=True)
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(180)
    page.locator('.split-panel').scroll_into_view_if_needed()
    mobile=page.locator('.split-person .split-avatar.has-character').evaluate_all('(items)=>items.map(e=>{const r=e.getBoundingClientRect();return {w:r.width,h:r.height}})')
    check('compact/mobile friend tiles use the same responsive square stage',len(mobile)==4 and all(abs(x['w']-92)<0.5 and abs(x['h']-92)<0.5 for x in mobile),mobile)
    page.screenshot(path='/mnt/data/TRAVESÍA_V10_Square_Character_Mobile.png',full_page=True)
    browser.close()
for name,ok,details in results:
    print(('PASS' if ok else 'FAIL'),name,details if details is not None else '')
print(f'RESULT: {sum(1 for _,ok,_ in results if ok)}/{len(results)} passed')
if errors or not all(ok for _,ok,_ in results): raise SystemExit(1)
