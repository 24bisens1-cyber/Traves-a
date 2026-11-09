/* TRAVESÍA extensions: travel hand-offs, world scenarios and account access. */
(function () {
  const basePlannerHTML = window.plannerHTML;
  const baseWirePlanner = window.wirePlanner;
  const baseCityTwinHTML = window.cityTwinHTML;
  const baseWireCityTwin = window.wireCityTwin;
  const local = { scenarioRuns: [] };
  state.origin = state.origin || "New Delhi, India";
  if (!state.scenarioRuns) state.scenarioRuns = [];

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", {maximumFractionDigits: 2});
  const dateText = (s) => { try { return s ? new Date(s).toLocaleString() : "Date not recorded"; } catch { return "Date not recorded"; } };
  async function api(url, options={}) {
    const method=String(options.method||'GET').toUpperCase();
    const headers=new Headers(options.headers||{});
    if (!['GET','HEAD','OPTIONS'].includes(method) && !window.cityPulseAuthCsrf) {
      try { const sessionResponse=await fetch('/api/auth/me',{credentials:'same-origin',headers:{Accept:'application/json'}}); const session=await sessionResponse.json(); window.cityPulseAuthCsrf=session.csrf_token||''; } catch (_) {}
    }
    if (!['GET','HEAD','OPTIONS'].includes(method) && window.cityPulseAuthCsrf && !headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token',window.cityPulseAuthCsrf);
    const response = await fetch(url, {...options, method, headers, credentials:'same-origin'});
    let payload = {};
    try { payload = await response.json(); } catch { payload = {}; }
    if (!response.ok) { const error=new Error(payload.error || `Request failed (${response.status})`); error.payload=payload; error.status=response.status; throw error; }
    return payload;
  }
  function currentExternalSearches(origin, destination, start, end) {
    const from = (origin || "New Delhi, India").trim();
    const to = (destination || state.destination || "Goa, India").trim();
    const datePhrase = start ? ` on ${start}` : "";
    const routeText = `${from} to ${to}`;
    const mapsSearch = (q, place=to) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${q} in ${place}`)}`;
    const search = (q) => `https://www.google.com/search?q=${encodeURIComponent(q)}`;
    const hotel = new URLSearchParams({ss: to, group_adults: "1", no_rooms: "1", group_children: "0"});
    if (start) hotel.set("checkin", start);
    if (end) hotel.set("checkout", end);
    const flightQuery = `Flights from ${from} to ${to}${start ? ` on ${start}` : ""}${end ? ` returning ${end}` : ""}`;
    const railQuery = `trains from ${from} to ${to}${datePhrase} fares schedule availability`;
    return [
      {icon:"✈️", title:"Compare & book flights", tag:"FLIGHT FARES", desc:"Open Google Flights with this route and date, or enter the same details on ixigo. Compare current airline and seller prices, then complete passenger details and payment with the seller.", url:`https://www.google.com/travel/flights?q=${encodeURIComponent(flightQuery)}`, secondaryUrl:"https://www.ixigo.com/flights", secondaryLabel:"Compare on ixigo Flights"},
      {icon:"🚆", title:"Compare & book trains", tag:"AUTHORISED RAIL", desc:"Check current trains, fares and seats with IRCTC or an IRCTC-listed booking partner. Sign in and pay on the provider site.", url:"https://www.irctc.co.in/eticket/", secondaryUrl:"https://www.ixigo.com/trains", secondaryLabel:"Search on IRCTC-authorised ixigo"},
      {icon:"🧭", title:"Train timings & route info", tag:"TRAIN INFO", desc:"Look up route schedules and running information before you choose a train.", url:search(railQuery), secondaryUrl:"https://www.google.com/search?q="+encodeURIComponent(`Where is my train ${routeText}`), secondaryLabel:"Check train running info"},
      {icon:"🚌", title:"Intercity buses", tag:"BUS", desc:"Compare operators and check boarding/drop-off points.", url:search(`bus tickets ${routeText}${datePhrase}`)},
      {icon:"🏡", title:"Stays & hotels", tag:"STAY", desc:"Open a lodging search. Availability and terms are provider-controlled.", url:`https://www.booking.com/searchresults.html?${hotel.toString()}`},
      {icon:"🚇", title:"Local transport", tag:"LOCAL", desc:"Open route planning for transit, driving, walking or cycling.", url:`https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(from)}&destination=${encodeURIComponent(to)}&travelmode=transit`},
      {icon:"🎮", title:"Gaming & cyber cafés", tag:"GAMING", desc:"Find gaming cafés, esports venues and cyber cafés near the destination.", url:mapsSearch("gaming cafe OR cyber cafe")},
      {icon:"🍜", title:"Food & cafés", tag:"FOOD", desc:"Explore restaurants, street food and cafés around your stay.", url:mapsSearch("restaurants cafes local food")},
      {icon:"🎟️", title:"Events & activities", tag:"DO", desc:"Look for museums, activities, attractions and dated events.", url:search(`things to do events attractions in ${to}${start ? ` around ${start}` : ""}`)},
      {icon:"🌳", title:"Parks & nature", tag:"OUTDOORS", desc:"Discover parks, walks, outdoor spaces and nature experiences.", url:mapsSearch("parks nature walks")},
    ];
  }
  function experienceCardsHTML() {
    const origin = document.querySelector("#experienceOrigin")?.value || state.origin;
    const destination = document.querySelector("#experienceDestination")?.value || state.destination;
    const start = document.querySelector("#experienceStart")?.value || state.tripStart || "";
    const end = document.querySelector("#experienceEnd")?.value || state.tripEnd || "";
    return currentExternalSearches(origin, destination, start, end).map(item => `
      <article class="experience-card"><div class="experience-card-top"><span class="experience-icon">${item.icon}</span><span class="experience-tag">${item.tag}</span></div>
      <h3>${item.title}</h3><p>${item.desc}</p><div class="experience-card-actions"><a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer">${item.tag==="AUTHORISED RAIL"?"Open official IRCTC ↗":item.tag==="FLIGHT FARES"?"Compare live flight results ↗":item.tag==="TRAIN INFO"?"Search train information ↗":"Open search ↗"}</a>${item.secondaryUrl?`<a class="subtle-external-link" href="${esc(item.secondaryUrl)}" target="_blank" rel="noopener noreferrer">${esc(item.secondaryLabel||"Open another provider")} ↗</a>`:""}</div></article>`).join("");
  }
  function experiencesHTML() {
    return `${title("TRAVEL, STAYS & REAL-WORLD FINDS", "Everything for the adventure.", "Compare where to stay, how to get there, and what to do. Each link is a search hand-off, not a live price or confirmed booking.")}
      <section class="panel experience-search-panel"><div class="experience-fields">
        <div class="field"><label>Starting city</label><input id="experienceOrigin" value="${esc(state.origin || "New Delhi, India")}" autocomplete="off"></div>
        <div class="field"><label>Destination / area</label><input id="experienceDestination" value="${esc(state.destination || "Goa, India")}" autocomplete="off"></div>
        <div class="field"><label>Check-in / departure date (optional)</label><input id="experienceStart" type="date" value="${esc(state.tripStart || "")}"></div>
        <div class="field"><label>Check-out / return date (optional)</label><input id="experienceEnd" type="date" value="${esc(state.tripEnd || "")}"></div>
      </div><div class="experience-actions"><button class="primary-btn" id="refreshExperiences">Build my searches ↗</button><button class="secondary-btn" id="useTripDetails">Use Trip Studio details</button></div>
      <p class="experience-disclaimer">Before paying, confirm the provider's final total, cancellation terms, age restrictions, accessibility, opening hours and service availability. These searches do not make reservations.</p></section>
      <section class="panel" style="margin-top:16px"><div class="panel-heading-row"><div><div class="eyebrow">PROVIDER-BACKED INVENTORY</div><h3>Search live flight offers</h3><p>Uses the configured Amadeus offer feed when available. Without a server key, open live Google Flights or ixigo results below instead. Airport codes are IATA codes, not city names.</p></div><span class="status-chip">PROVIDER DATA</span></div><div class="experience-fields"><div class="field"><label for="liveFlightOrigin">From (IATA)</label><input id="liveFlightOrigin" value="DEL" maxlength="3" pattern="[A-Za-z]{3}" autocomplete="off"></div><div class="field"><label for="liveFlightDestination">To (IATA)</label><input id="liveFlightDestination" value="GOI" maxlength="3" pattern="[A-Za-z]{3}" autocomplete="off"></div><div class="field"><label for="liveFlightDeparture">Departure date</label><input id="liveFlightDeparture" type="date" required></div><div class="field"><label for="liveFlightReturn">Return date (optional)</label><input id="liveFlightReturn" type="date"></div><div class="field"><label for="liveFlightAdults">Adults</label><input id="liveFlightAdults" type="number" value="1" min="1" max="9"></div></div><button class="primary-btn" id="liveFlightSearch">Fetch flight offers ↗</button><div class="scenario-result" id="liveFlightResults" role="status" aria-live="polite">No live request has been made. Provider credentials are configured by the server administrator, never entered here.</div><p class="experience-disclaimer">Offers can change before booking. This endpoint searches, it does not reserve or purchase tickets. Test-environment results are labelled as test data.</p></section>
      <div class="section-head"><div><div class="eyebrow">THE BIG DECISION</div><h2>Flight or train?</h2></div></div>
      <section class="panel fare-compare-panel"><h3>Compare the fares you find</h3><p>Open the flight comparison and railway provider pages below. Enter the displayed totals from Google Flights, ixigo or IRCTC to compare them without relying on made-up prices.</p><div class="fare-compare-grid"><label>Flight total (₹)<input id="compareFlightFare" type="number" min="0" step="0.01" placeholder="Enter fare from flight results"></label><label>Train total (₹)<input id="compareTrainFare" type="number" min="0" step="0.01" placeholder="Enter fare from IRCTC or ixigo"></label><label>Flight journey time (hours, optional)<input id="compareFlightHours" type="number" min="0" step="0.25" placeholder="e.g. 2.5"></label><label>Train journey time (hours, optional)<input id="compareTrainHours" type="number" min="0" step="0.25" placeholder="e.g. 14"></label></div><button class="primary-btn" id="runFareCompare">Compare my options ↗</button><div class="scenario-result" id="fareCompareResult" role="status" aria-live="polite">Add the totals from current provider results to see the cheaper option and time trade-off.</div><p class="experience-disclaimer">Include baggage, convenience fees, transfers, station/airport distance and cancellation terms before deciding. Actual fares and seats change; TRAVESÍA does not invent live results.</p><div class="booking-flow-note"><b>How checkout works</b><span>Compare current results → choose an airline, IRCTC or an IRCTC-listed partner → sign in with that provider → enter passenger details and pay there → return with the provider's confirmation / PNR. TRAVESÍA never asks for your IRCTC or airline password.</span></div></section>
      <div class="section-head"><div><div class="eyebrow">YOUR NEXT STEPS, CONNECTED</div><h2>Go from idea to options.</h2></div></div><section class="experience-grid" id="experienceResults">${experienceCardsHTML()}</section>
      <section class="panel experience-footnote"><h3>What is and isn't live?</h3><p>Search pages come from external providers. TRAVESÍA does not yet have its own live airline, rail, bus, hotel, event or places inventory; it never reports that a booking was made unless an authorized booking integration confirms it.</p></section>`;
  }
  function wireExperiences() {
    const dep=document.querySelector('#liveFlightDeparture'), ret=document.querySelector('#liveFlightReturn');
    const today=new Date(); const localISO=new Date(today.getTime()-today.getTimezoneOffset()*60000).toISOString().slice(0,10);
    if(dep){dep.min=localISO;if(!dep.value)dep.value=state.tripStart&&state.tripStart>=localISO?state.tripStart:localISO;}
    if(ret){ret.min=dep?.value||localISO;if(state.tripEnd&&state.tripEnd>=ret.min)ret.value=state.tripEnd;}
    dep?.addEventListener('change',()=>{if(ret){ret.min=dep.value;if(ret.value&&ret.value<dep.value)ret.value='';}});
    const flightButton=document.querySelector('#liveFlightSearch');
    if(flightButton)flightButton.onclick=async()=>{
      const result=document.querySelector('#liveFlightResults'); const origin=document.querySelector('#liveFlightOrigin').value.trim().toUpperCase(); const destination=document.querySelector('#liveFlightDestination').value.trim().toUpperCase();
      const departure_date=dep?.value||'', return_date=ret?.value||'', adults=Number(document.querySelector('#liveFlightAdults').value||1);
      if(!/^[A-Z]{3}$/.test(origin)||!/^[A-Z]{3}$/.test(destination)||origin===destination){result.textContent='Enter two different 3-letter airport codes, such as DEL and GOI.';return;}
      if(!departure_date||departure_date<localISO||(return_date&&return_date<departure_date)){result.textContent='Choose a departure date today or later and a return date on or after departure.';return;}
      if(!Number.isInteger(adults)||adults<1||adults>9){result.textContent='Choose between 1 and 9 adults.';return;}
      flightButton.disabled=true;flightButton.textContent='Contacting flight provider…';result.textContent='Fetching current provider offers…';
      try{
        const payload=await api('/api/travel/flights/offers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({origin,destination,departure_date,return_date,adults,currency:'INR',limit:10})});
        const offers=payload.offers||[];
        result.innerHTML=`<b>${offers.length} provider offer(s)</b> · ${esc(payload.data_mode||'provider response')} · Retrieved ${esc(payload.retrieved_at||'time unavailable')}<div class="scenario-history">${offers.map(o=>`<div class="scenario-history-row"><b>${esc(o.currency||'INR')} ${esc(o.price_total??'—')}</b><span>${esc([...new Set((o.itineraries||[]).flatMap(it=>(it.segments||[]).map(seg=>seg.carrier||seg.flight_number).filter(Boolean)))].join(', ')||'Airline not identified')}</span><span>${(o.itineraries||[]).map(it=>`${esc(it.duration||'duration n/a')} · ${Number(it.segments?.length||0)} segment(s)`).join(' / ')}</span></div>`).join('')||'<p>No matching offers were returned for this route and date.</p>'}</div><small>${esc(payload.notice||'Provider availability may change before booking.')}</small>`;
      }catch(error){
        const alternatives=Array.isArray(error.payload?.alternatives)?error.payload.alternatives:[];
        const quickLinks=[...alternatives,{provider:'ixigo Flights',url:'https://www.ixigo.com/flights'}].filter((a,i,all)=>a.url&&all.findIndex(x=>x.url===a.url)===i);
        result.innerHTML=`<b>${esc(error.message)}</b><p>No sample offers are substituted for a failed live request.</p><div class="experience-card-actions">${quickLinks.map(a=>`<a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">Open ${esc(a.provider)} live search ↗</a>`).join('')}</div><small>These links open live provider searches. Confirm price, baggage and availability on the seller site before paying.</small>`;
      }
      finally{flightButton.disabled=false;flightButton.textContent='Fetch flight offers ↗';}
    };
    const rebuild = () => {
      state.origin = document.querySelector("#experienceOrigin").value.trim() || "New Delhi, India";
      state.destination = document.querySelector("#experienceDestination").value.trim() || "Choose destination";
      state.tripStart = document.querySelector("#experienceStart").value;
      state.tripEnd = document.querySelector("#experienceEnd").value;
      if (state.tripStart && state.tripEnd && state.tripEnd < state.tripStart) {
        document.querySelector("#experienceEnd").setCustomValidity("Return/check-out date must be on or after the start date.");
        document.querySelector("#experienceEnd").reportValidity();
        document.querySelector("#experienceEnd").setCustomValidity("");
        return;
      }
      document.querySelector("#experienceResults").innerHTML = experienceCardsHTML();
      ["#compareFlightFare", "#compareTrainFare", "#compareFlightHours", "#compareTrainHours"].forEach(selector => { const field=document.querySelector(selector); if(field) field.value=""; });
      const comparison=document.querySelector("#fareCompareResult"); if(comparison) comparison.textContent="Route updated. Open the new provider searches and enter the current fares to compare this trip.";
      toast("Search links updated. Prices and inventory are shown by the providers.");
    };
    document.querySelector("#refreshExperiences").onclick = rebuild;
    document.querySelector("#useTripDetails").onclick = () => {
      const dest = document.querySelector("#experienceDestination");
      const origin = document.querySelector("#experienceOrigin");
      if (dest) dest.value = state.destination || "Goa, India";
      if (origin) origin.value = state.origin || "New Delhi, India";
      const start = document.querySelector("#experienceStart");
      const end = document.querySelector("#experienceEnd");
      if (start) start.value = state.tripStart || "";
      if (end) end.value = state.tripEnd || "";
      rebuild();
    };
    const compareButton=document.querySelector("#runFareCompare");
    if(compareButton) compareButton.onclick=()=>{
      const flight=document.querySelector("#compareFlightFare").value;
      const train=document.querySelector("#compareTrainFare").value;
      const fh=document.querySelector("#compareFlightHours").value;
      const th=document.querySelector("#compareTrainHours").value;
      const result=document.querySelector("#fareCompareResult");
      if(flight===""||train===""||!Number.isFinite(Number(flight))||!Number.isFinite(Number(train))||Number(flight)<0||Number(train)<0){result.textContent="Enter both non-negative totals from the provider websites first.";return;}
      const f=Number(flight),t=Number(train),delta=Math.abs(f-t);
      let message=f===t?"Both options currently show the same entered fare.":`${f<t?"Flight":"Train"} is cheaper by ₹${delta.toLocaleString("en-IN",{maximumFractionDigits:2})} based on the prices you entered.`;
      if(fh!==""&&th!==""&&Number.isFinite(Number(fh))&&Number.isFinite(Number(th))&&Number(fh)>=0&&Number(th)>=0){const timeDelta=Math.abs(Number(fh)-Number(th));message+=` ${Number(fh)<Number(th)?"Flight":"Train"} is faster by ${timeDelta.toLocaleString("en-IN",{maximumFractionDigits:2})} hour(s) based on the journey times you entered.`;}
      result.textContent=message+" Recheck live prices, baggage, transfers, station/airport access and cancellation conditions before booking.";
      toast("Fare comparison calculated from your entries.");
    };
  }

  function cityTwinHTML() { return typeof baseCityTwinHTML === "function" ? baseCityTwinHTML() : "<section class=panel><h2>World Scene Lab</h2><p>Reload the app to restore the travel scenario tools.</p></section>"; }
  function wireCityTwin() { if (typeof baseWireCityTwin === "function") baseWireCityTwin(); }

  function accountHTML(){return `${title("ACCOUNT · IDENTITY & ACCESS","One account, clear permissions.","Sign in for protected review/export tools. New registrations are members; an administrator account is created only from server environment variables.")}<section class="panel"><div id="accountStatus" class="scenario-result" role="status" aria-live="polite">Checking current session…</div><div class="two-col"><form id="accountLoginForm" class="panel" style="box-shadow:none"><h3>Sign in</h3><div class="field"><label for="accountLoginEmail">Email</label><input id="accountLoginEmail" type="email" required maxlength="120" autocomplete="username"></div><div class="field"><label for="accountLoginPassword">Password</label><input id="accountLoginPassword" type="password" required maxlength="256" autocomplete="current-password"></div><button class="primary-btn" type="submit">Sign in securely ↗</button></form><form id="accountRegisterForm" class="panel" style="box-shadow:none"><h3>Create member account</h3><div class="field"><label for="accountName">Display name</label><input id="accountName" required minlength="2" maxlength="80" autocomplete="name"></div><div class="field"><label for="accountRegisterEmail">Email</label><input id="accountRegisterEmail" type="email" required maxlength="120" autocomplete="email"></div><div class="field"><label for="accountRegisterPassword">Password (12+ characters)</label><input id="accountRegisterPassword" type="password" required minlength="12" maxlength="256" autocomplete="new-password"></div><button class="primary-btn" type="submit">Create account ↗</button><p class="field-hint">Public registration cannot create an administrator account.</p></form></div><button class="secondary-btn" id="accountLogout" hidden>Sign out</button></section><section class="panel" style="margin-top:16px"><h3>Provider and safety status</h3><div id="accountProviderStatus" class="scenario-result">Loading configured provider readiness…</div><p class="field-hint">Do not paste provider secrets into this page. Configure them on the server. Protected account operations require a valid session and CSRF token. Provider secrets are configured on the server only.</p></section>`}
  function wireAccount(){
    const status=document.querySelector('#accountStatus'), providerStatus=document.querySelector('#accountProviderStatus'), logout=document.querySelector('#accountLogout');
    async function refresh(){try{const me=await api('/api/auth/me');window.cityPulseAuthCsrf=me.csrf_token||'';if(me.authenticated){status.innerHTML=`Signed in as <b>${esc(me.user.display_name)}</b> (${esc(me.user.email)}) · Role: <b>${esc(me.user.role)}</b>. Session expires after 14 days of issuance; sign out to revoke it.`;logout.hidden=false;}else{window.cityPulseAuthCsrf='';status.textContent='Not signed in. You can register a member account or sign in. Protected administrator actions remain unavailable.';logout.hidden=true;}}catch(e){status.textContent=e.message;}}
    const getForm=async(formId,bodyBuilder)=>{const form=document.querySelector(formId);form.onsubmit=async ev=>{ev.preventDefault();const button=form.querySelector('button[type="submit"]');button.disabled=true;try{const result=await api(formId==='#accountLoginForm'?'/api/auth/login':'/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(bodyBuilder())});window.cityPulseAuthCsrf=result.csrf_token||'';status.textContent=`Signed in as ${result.user.display_name} (${result.user.role}).`;form.reset();await refresh();toast('Account session established.');}catch(e){status.textContent=e.message;}finally{button.disabled=false;}}};
    getForm('#accountLoginForm',()=>({email:document.querySelector('#accountLoginEmail').value.trim(),password:document.querySelector('#accountLoginPassword').value}));
    getForm('#accountRegisterForm',()=>({display_name:document.querySelector('#accountName').value.trim(),email:document.querySelector('#accountRegisterEmail').value.trim(),password:document.querySelector('#accountRegisterPassword').value}));
    logout.onclick=async()=>{try{await api('/api/auth/logout',{method:'POST',headers:{'X-CSRF-Token':window.cityPulseAuthCsrf||''}});window.cityPulseAuthCsrf='';await refresh();toast('Signed out.');}catch(e){status.textContent=e.message;}};
    api('/api/providers/status').then(async d=>{const rows=d.providers||[];const amadeus=rows.find(x=>x.type==='flight_offer_api');const weather=rows.find(x=>x.type==='current_weather_api');const metno=rows.find(x=>x.type==='global_weather_api');const sat=rows.find(x=>x.type==='satellite_tiles');providerStatus.innerHTML=`<div class="scenario-history-row"><b>In-app flight offers (Amadeus)</b><span>${amadeus?.status==='configured'?'Configured':'Credential required; Google Flights, KAYAK and ixigo hand-offs available'}</span></div><div class="scenario-history-row"><b>Weather forecast (MET Norway)</b><span>${metno?.status==='configured'?'Ready when provider reachable':'Needs a real contact email or public HTTPS URL'}</span></div><div class="scenario-history-row"><b>Open-Meteo fallback</b><span>${weather?.status==='public_api_configured_noncommercial_fallback'?'Non-commercial use only':'Disabled by deployment policy'}</span></div><div class="scenario-history-row"><b>NASA GIBS satellite layer</b><span>Public no-key global imagery available at lower detail</span></div><div class="scenario-history-row"><b>MapTiler satellite</b><span>${d.providers?.find(x=>x.type==='satellite_tiles_premium')?.status==='configured'?'Configured':'Optional licensed higher-detail layer'}</span></div><div class="scenario-history-row"><b>Rail services</b><span>Official IRCTC and IRCTC-listed ixigo hand-offs are ready now. For in-app checkout, pursue an affiliate/associate agreement with an existing B2C PSP and IRCTC registration; direct PSP registration is a separate, higher-cost route.</span></div><div class="scenario-history-row"><b>Flight ticket issuance</b><span>Search can use Amadeus when configured or no-key external search now. In-app ticket issuance requires a signed airline consolidator/issuer agreement and production approval.</span></div><div class="scenario-history-row"><b>Provider onboarding pack</b><span>See docs/PROVIDER_ONBOARDING_PLAN.md for the exact IRCTC affiliate route, fee/eligibility checklist and Amadeus production requirements.</span></div>`;}).catch(e=>providerStatus.textContent=e.message);refresh();
  }

  // Extend the original Trip Studio instead of discarding its editable itinerary.
  window.plannerHTML = function() {
    let html=basePlannerHTML();
    const dates='<div class="field"><label>Starting city</label><input id="tripOrigin" value="'+esc(state.origin || "New Delhi, India")+'"></div><div class="field"><label>Departure date (optional)</label><input id="tripStart" type="date" value="'+esc(state.tripStart || "")+'"></div><div class="field"><label>Return date (optional)</label><input id="tripEnd" type="date" value="'+esc(state.tripEnd || "")+'"></div>';
    html=html.replace(/<div class="field"><label>Trip length \(days\)<\/label><input id="tripDays" type="number" min="1" max="30" value="[^"]*"><\/div>/, match=>match+dates);
    html=html.replace('<button class="chip-btn" id="openRoutes">↗ Compare local transport</button>', '<button class="chip-btn" id="openRoutes">↗ Compare local transport</button><button class="chip-btn" id="openExperiences">🏡 Find stays & experiences</button>');
    return html;
  };
  window.wirePlanner = function() {
    baseWirePlanner();
    const from=document.querySelector("#tripOrigin");if(from)from.addEventListener("change",()=>{state.origin=from.value.trim()||"New Delhi, India";});
    const start=document.querySelector("#tripStart"),end=document.querySelector("#tripEnd");
    if(start)start.addEventListener("change",()=>{state.tripStart=start.value;});
    if(end)end.addEventListener("change",()=>{state.tripEnd=end.value;});
    const routeBtn=document.querySelector("#openRoutes"); if(routeBtn){routeBtn.onclick=()=>{if(from)state.origin=from.value.trim()||state.origin;setView("mobility");};}
    const xp=document.querySelector("#openExperiences");if(xp)xp.onclick=()=>{if(from)state.origin=from.value.trim()||state.origin;state.destination=document.querySelector("#tripDest").value.trim()||state.destination;state.budget=Math.max(0,Number(document.querySelector("#tripBudget").value)||state.budget);state.days=Math.max(1,Number(document.querySelector("#tripDays").value)||state.days);if(start)state.tripStart=start.value;if(end)state.tripEnd=end.value;setView("experiences");};
  };
  window.setView = function(view) {
    state.view=view;
    const names={home:"Discover",explore:"Explore the world",planner:"Trip studio",pulse:"Trip Pulseboard",mobility:"Get me there",experiences:"Stays & experiences",citytwin:"World Scene Lab",squad:"Squad plans",companion:"Companion studio",saved:"Saved worlds",split:"Split expenses",account:"Account & access"};
    const crumb=document.querySelector("#crumb");if(crumb)crumb.textContent=names[view]||"Discover";
    document.querySelectorAll(".nav-item[data-view]").forEach(b=>b.classList.toggle("active",b.dataset.view===view));
    document.querySelector("#sidebar")?.classList.remove("open");
    window.renderView();
  };
  window.renderView = function() {
    const page=document.querySelector("#page");if(!page)return;
    page.classList.remove("cinematic-page-enter");
    void page.offsetWidth;
    page.classList.add("cinematic-page-enter");
    window.setTimeout(()=>page.classList.remove("cinematic-page-enter"),720);
    window.clearInterval(window.cityPulsePageSceneTimer);
    const render=(html,wire,withScene=true)=>{page.innerHTML=(withScene?(window.cityPulsePageSceneMarkup?.(state.view)||""):"")+html;if(withScene)window.cityPulseWirePageScene?.(state.view);wire();};
    if(state.view==="pulse"&&window.CityPulsePulseBoard){render(window.CityPulsePulseBoard.markup(),window.CityPulsePulseBoard.wire);return;}
    if(state.view==="experiences"){render(experiencesHTML(),wireExperiences);return;}
    if(state.view==="citytwin"){render(cityTwinHTML(),wireCityTwin);return;}
    if(state.view==="planner"){render(window.plannerHTML(),window.wirePlanner);return;}
    if(state.view==="home"){render(homeHTML(),wireHome,false);return;}
    if(state.view==="explore"){render(exploreHTML(),wireExplore,false);return;}
    if(state.view==="mobility"){render(mobilityHTML(),wireMobility);return;}
    if(state.view==="companion"){render(companionHTML(),wireCompanion);return;}
    if(state.view==="squad"){render(squadHTML(),wireSquad);return;}
    if(state.view==="saved"){render(savedHTML(),wireSaved);return;}
    if(state.view==="split"){render(splitHTML(),wireSplit);return;}
    if(state.view==="account"){render(accountHTML(),wireAccount);return;}
    render(homeHTML(),wireHome,false);
  };
})();
