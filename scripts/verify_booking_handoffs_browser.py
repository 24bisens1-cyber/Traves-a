#!/usr/bin/env python3
"""Browser checks for route-aware flight and authorised rail booking hand-offs.

Requires Playwright + Chromium. This tests the real Stays & Experiences UI without
requiring external travel APIs or provider credentials.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is required: pip install -r requirements-dev.txt", file=sys.stderr)
        return 2

    root=Path(__file__).resolve().parents[1]
    ext=(root/"frontend"/"extensions.js").read_text(encoding="utf-8")
    html='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{font:14px Arial;margin:24px;background:#f5f2e9}.panel{padding:18px;background:white;border-radius:14px;margin-bottom:14px}.experience-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.experience-card{padding:14px;border:1px solid #ddd;border-radius:12px}.experience-card-actions{display:flex;gap:10px;flex-wrap:wrap}.field{display:grid;gap:4px;margin:6px 0}.experience-fields{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.primary-btn,.secondary-btn{padding:10px;border-radius:8px}</style></head><body>
    <div id="crumb"></div><div id="page"></div><div id="toast"></div>
    <script>
      var state={origin:'Nagpur, India',destination:'Goa, India',tripStart:'2026-11-14',tripEnd:'2026-11-20',budget:20000,days:5,view:'experiences'};
      function title(kicker,heading,description){return `<header><small>${kicker}</small><h1>${heading}</h1><p>${description}</p></header>`}
      function toast(message){document.querySelector('#toast').textContent=message}
      window.plannerHTML=()=>'';window.wirePlanner=()=>{};window.cityTwinHTML=()=>'';window.wireCityTwin=()=>{};
    </script>
    <script>__EXTENSIONS__</script></body></html>'''.replace("__EXTENSIONS__",ext)
    results=[];errors=[]
    with sync_playwright() as p:
        launch={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage"]}
        if Path("/usr/bin/chromium").exists(): launch["executable_path"]="/usr/bin/chromium"
        browser=p.chromium.launch(**launch)
        page=browser.new_page(viewport={"width":1440,"height":1000})
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.set_content(html,wait_until="domcontentloaded")
        page.evaluate("window.setView('experiences')")
        page.wait_for_selector("#experienceResults .experience-card")
        def check(name,ok,**details): results.append({"name":name,"pass":bool(ok),**details})
        cards=page.locator("#experienceResults .experience-card")
        check("travel cards render in the app",cards.count()>=9,count=cards.count())
        flight=cards.filter(has=page.get_by_role("heading",name="Compare & book flights"))
        train=cards.filter(has=page.get_by_role("heading",name="Compare & book trains"))
        check("flight card includes a route-aware live search",flight.count()==1 and "google.com/travel/flights?q=" in (flight.locator("a").first.get_attribute("href") or ""))
        flight_href=flight.locator("a").first.get_attribute("href") or ""
        check("flight search contains the selected route and dates",all(s in flight_href for s in ["Nagpur","Goa","2026-11-14","2026-11-20"]),url=flight_href)
        check("flight card offers ixigo as a second live search",flight.locator("a").nth(1).get_attribute("href")=="https://www.ixigo.com/flights")
        check("train card links directly to official IRCTC",train.count()==1 and train.locator("a").first.get_attribute("href")=="https://www.irctc.co.in/eticket/")
        check("train card provides IRCTC-listed ixigo as an alternative",train.count()==1 and train.locator("a").nth(1).get_attribute("href")=="https://www.ixigo.com/trains")
        external=page.locator("#experienceResults a[target='_blank']")
        check("external booking hand-offs use safe new-tab attributes",external.count()>=12 and all("noopener" in (external.nth(i).get_attribute("rel") or "") for i in range(external.count())))
        page.locator("#experienceOrigin").fill("Mumbai, India");page.locator("#experienceDestination").fill("Pune, India")
        page.locator("#experienceStart").fill("2026-12-01");page.locator("#experienceEnd").fill("2026-12-03")
        page.locator("#refreshExperiences").click()
        updated=page.locator("#experienceResults .experience-card").filter(has=page.get_by_role("heading",name="Compare & book flights")).locator("a").first.get_attribute("href") or ""
        check("changing route and date rebuilds live search URLs",all(s in updated for s in ["Mumbai","Pune","2026-12-01","2026-12-03"]),url=updated)
        # Simulate an unavailable optional Amadeus feed; UI must keep the user moving to
        # live third-party results, never fabricate sample fares.
        page.evaluate('''() => { window.fetch=async (u)=>{
          if(String(u).includes('/api/auth/me')) return new Response(JSON.stringify({csrf_token:''}),{status:200,headers:{'Content-Type':'application/json'}});
          return new Response(JSON.stringify({error:'Amadeus credentials are not configured. Use live provider searches.',alternatives:[
            {provider:'Google Flights',url:'https://www.google.com/travel/flights?q='+encodeURIComponent('Flights from NAG to GOI on 2026-11-14')},
            {provider:'KAYAK',url:'https://www.kayak.co.in/flights'}]}),{status:503,headers:{'Content-Type':'application/json'}});
        }; }''')
        page.locator("#liveFlightOrigin").fill("NAG");page.locator("#liveFlightDestination").fill("GOI")
        page.locator("#liveFlightSearch").click()
        page.wait_for_selector("#liveFlightResults a")
        fallback=page.locator("#liveFlightResults a")
        check("no-key live flight search offers external results instead of fake fares",fallback.count()>=3 and "No sample offers" in page.locator("#liveFlightResults").inner_text(),count=fallback.count())
        check("no-key fallback exposes Google Flights and ixigo",any("Google Flights" in (fallback.nth(i).inner_text()) for i in range(fallback.count())) and any("ixigo Flights" in fallback.nth(i).inner_text() for i in range(fallback.count())))
        browser.close()
    payload={"passed":sum(bool(x["pass"]) for x in results),"total":len(results),"checks":results,"browser_errors":errors}
    print(json.dumps(payload,indent=2))
    return 0 if payload["passed"]==payload["total"] and not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
