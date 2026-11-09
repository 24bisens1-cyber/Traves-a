#!/usr/bin/env python3
"""Offline Chromium contract smoke-test for Trip Pulseboard, using explicitly mocked provider responses."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", help="Optional output path for a desktop Trip Pulseboard screenshot")
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed; install it with python -m pip install playwright", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    js = (root / "frontend" / "pulseboard.js").read_text(encoding="utf-8")
    css = (root / "frontend" / "pulseboard.css").read_text(encoding="utf-8")
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:14px Arial;margin:0;padding:18px;background:#f6f4ec}.primary-btn,.secondary-btn{padding:10px 14px;border:0;border-radius:9px;margin:3px;cursor:pointer}.primary-btn{background:#1f6953;color:white}.secondary-btn{background:white;color:#234}</style><style>''' + css + '''</style></head><body><main id="page"></main>
<script>
const state={view:'pulse',destination:'Goa, India',budget:10000,days:4,priority:'balanced'};
window.__store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>window.__store[k]??null,setItem:(k,v)=>window.__store[k]=String(v),removeItem:k=>delete window.__store[k]}});
window.fetch=async (url,options={})=>{const u=String(url);let data={};
 if(u.includes('/api/travel/weather')) data={source:'MET Norway Locationforecast/2.0',data_mode:'live_provider_response',retrieved_at:'2026-10-25T00:00:00Z',timezone:'UTC',current:{time:'2026-10-25T00:00:00Z',temperature_2m:29,apparent_temperature:null,wind_speed_10m:2.4,weather_description:'partly cloudy'},units:{temperature_2m:'°C',apparent_temperature:'°C',wind_speed_10m:'m/s'},daily:{time:['2026-10-25','2026-10-26','2026-10-27'],temperature_2m_max:[31,30,28],temperature_2m_min:[22,21,20],precipitation_probability_max:[null,null,null],weather_code:[null,null,null],weather_description:['partly cloudy','clearsky day','rain']},daily_units:{temperature_2m_max:'°C',temperature_2m_min:'°C'},stale:false};
 else if(u.includes('/api/trip/fit')) data={all_destinations:[{name:'Goa, India',score:82,score_breakdown:{budget_fit:86,vibe_fit:100,duration_fit:80},reasons:['budget fit is strong','matches the selected travel vibe','duration suits this destination'],budget_note:'Illustrative planning band; not a live quote.'}],recommendations:[],method:{data_mode:'illustrative_heuristic_not_live_prices_or_personalised_AI'}};

 else data={};
 return {ok:true,status:200,json:async()=>data};};
</script><script>''' + js + '''</script><script>document.getElementById('page').innerHTML=CityPulsePulseBoard.markup();CityPulsePulseBoard.wire();</script></body></html>'''
    checks = []
    errors = []
    with sync_playwright() as p:
        opts = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if Path('/usr/bin/chromium').exists(): opts['executable_path'] = '/usr/bin/chromium'
        browser = p.chromium.launch(**opts)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html, wait_until='load')
        def check(name, passed, **details): checks.append({"name": name, "pass": bool(passed), **details})
        page.wait_for_function("document.querySelector('#pulseWeatherValue')?.textContent.includes('29') && document.querySelector('#pulseFitValue')?.textContent.includes('86')")
        check('Trip Pulseboard mounts with source-labelled signals', page.locator('.pulseboard').count()==1 and page.locator('.pulse-source').count()>=3)
        check('Budget fit remains labelled as an estimate', 'ESTIMATED' in page.locator('.pulse-grid').inner_text() and '86 / 100' in page.locator('#pulseFitValue').inner_text())
        check('First forecast time-slot displays its temperature and source', '29' in page.locator('#pulseWeatherValue').inner_text() and 'MET NORWAY' in page.locator('#pulseWeatherSource').inner_text())
        check('Forecast displays provider description strings', 'partly cloudy' in page.locator('#pulseForecast').inner_text())
        check('Missing precipitation probability is not fabricated', 'Precipitation probability not provided' in page.locator('#pulseForecast').inner_text())
        check('No blended safety score is rendered', page.get_by_text('not an overall safety score', exact=False).count()==0 and 'not a market price or overall safety score' in page.locator('#pulseStatus').inner_text())
        page.locator('#pulseSave').click()
        check('Snapshots persist locally and identify destination', 'citypulsex.trip-pulse.snapshots.v1' in page.evaluate('Object.keys(window.__store).join()') and 'Goa, India' in page.locator('#pulseSaved').inner_text())
        check('Flight hand-off remains a search link, not a fabricated fare', page.locator('#pulseFlights').get_attribute('href').startswith('https://www.google.com/travel/flights?q='))
        if args.screenshot:
            # Capture a useful scored example after the main signal checks.
            page.locator('#pulseDestination').select_option('Goa, India')
            page.locator('#pulseRefresh').click()
            page.wait_for_function("document.querySelector('#pulseFitValue')?.textContent.includes('86')")
            output = Path(args.screenshot).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            page.set_viewport_size({"width":1440,"height":1000})
            page.screenshot(path=str(output), full_page=True)
            print(f"Screenshot: {output}")
        page.set_viewport_size({"width":390,"height":844})
        metrics=page.evaluate('()=>({width:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth})')
        check('Mobile view has no horizontal overflow', metrics['width']<=metrics['viewport']+2, metrics=metrics)
        browser.close()
    print(json.dumps({"passed":sum(c['pass'] for c in checks),"total":len(checks),"checks":checks,"browser_errors":errors},indent=2))
    return 0 if all(c['pass'] for c in checks) and not errors else 1

if __name__=='__main__': raise SystemExit(main())
