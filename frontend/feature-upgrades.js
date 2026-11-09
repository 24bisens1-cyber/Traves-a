/* TRAVESÍA discovery and booking hand-off upgrades.
   Keeps the existing approved visual style. External prices/photos require internet;
   no booking is completed inside TRAVESÍA. */
(function () {
  "use strict";
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const photoCache = new Map();
  let lastReverseLookupAt = 0;
  const localFallback = (place) => {
    const s = `${place?.name || place?.displayName || ""}`.toLowerCase();
    if (/goa|beach|konkan/.test(s)) return "assets/destinations/goa.webp";
    if (/kyoto|japan|temple/.test(s)) return "assets/destinations/kyoto.webp";
    if (/antarctica|polar|penguin|glacier/.test(s)) return "assets/destinations/antarctica.webp";
    if (/sydney|australia/.test(s)) return "assets/destinations/sydney.webp";
    if (/rome|italy|colosseum/.test(s)) return "assets/destinations/rome.webp";
    if (/india/.test(s)) return "assets/destinations/india-inspiration.webp";
    return "assets/destinations/india-inspiration.webp";
  };
  const wikiSearch = async (placeName) => {
    const cacheKey = String(placeName || "").toLowerCase().trim();
    if (!cacheKey) return null;
    if (photoCache.has(cacheKey)) {
      // Several map markers can request the same place while Explore is mounting.
      // Await cached work inside the same rejection boundary so an offline lookup
      // never becomes an unhandled page-level promise rejection.
      try { return await photoCache.get(cacheKey); }
      catch (_) { photoCache.delete(cacheKey); return null; }
    }
    const task = (async () => {
      const url = "https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrnamespace=0&gsrlimit=6&prop=pageimages%7Cextracts%7Cinfo&inprop=url&piprop=thumbnail%7Cname&pithumbsize=1100&exintro=1&explaintext=1&format=json&origin=*" + "&gsrsearch=" + encodeURIComponent(placeName);
      const resp = await fetch(url, { headers: { "Accept": "application/json" } });
      if (!resp.ok) throw new Error("Place image search was unavailable.");
      const body = await resp.json();
      const pages = Object.values(body?.query?.pages || {}).sort((a,b)=>(a.index ?? 999)-(b.index ?? 999));
      const page = pages.find(p => p.thumbnail?.source && p.extract) || pages.find(p => p.thumbnail?.source) || pages[0];
      if (!page) return null;
      let imageUrl = page.thumbnail?.source || "";
      let credit = "Image/article source: Wikipedia";
      // Resolve the image-file metadata when possible so creator and licence can be credited.
      if (page.pageimage) {
        try {
          const fileUrl = "https://en.wikipedia.org/w/api.php?action=query&titles=" + encodeURIComponent("File:" + page.pageimage) + "&prop=imageinfo&iiprop=url%7Cextmetadata&iiurlwidth=1100&format=json&origin=*";
          const fileResp = await fetch(fileUrl, { headers: { "Accept": "application/json" } });
          if (fileResp.ok) {
            const fileBody = await fileResp.json();
            const filePage = Object.values(fileBody?.query?.pages || {})[0];
            const info = filePage?.imageinfo?.[0];
            const meta = info?.extmetadata || {};
            if (info?.thumburl || info?.url) imageUrl = info.thumburl || info.url;
            const artist = String(meta.Artist?.value || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
            const license = String(meta.LicenseShortName?.value || "").replace(/<[^>]*>/g, " ").trim();
            const filePageUrl = info?.descriptionurl || "https://commons.wikimedia.org/";
            const parts = [];
            if (artist) parts.push("Creator: " + artist.slice(0, 160));
            if (license) parts.push("Licence: " + license.slice(0, 80));
            if (parts.length) credit = parts.join(" · ");
            return { name: page.title || placeName, imageUrl, extract: page.extract || "", pageUrl: page.fullurl || "https://en.wikipedia.org/wiki/" + encodeURIComponent(page.title || placeName).replace(/%20/g,"_"), imagePageUrl: filePageUrl, credit };
          }
        } catch (_) { /* Use article thumbnail and source link if metadata lookup fails. */ }
      }
      return { name: page.title || placeName, imageUrl, extract: page.extract || "", pageUrl: page.fullurl || "https://en.wikipedia.org/wiki/" + encodeURIComponent(page.title || placeName).replace(/%20/g,"_"), imagePageUrl: page.fullurl || "https://en.wikipedia.org/", credit };
    })();
    photoCache.set(cacheKey, task);
    try { return await task; } catch (_) { photoCache.delete(cacheKey); return null; }
  };

  function renderDestinationDetails(place, options = {}) {
    const panel = document.querySelector("#destinationDetails");
    if (!panel || !place) return;
    state.selectedPlace = place;
    const name = place.displayName || place.name || "Selected place";
    state.destination = name;
    const fallback = place.photo || localFallback(place);
    const source = place.pageUrl ? `<a href="${esc(place.pageUrl)}" target="_blank" rel="noopener noreferrer">Article ↗</a>${place.imagePageUrl ? ` · <a href="${esc(place.imagePageUrl)}" target="_blank" rel="noopener noreferrer">Photo / licence ↗</a>` : ""}` : `<span>Illustrative cover art</span>`;
    panel.innerHTML = `<div class="map-preview-card"><img class="destination-hero-img" src="${esc(place.imageUrl || fallback)}" alt="${esc(name)} travel preview" loading="lazy"><div class="map-preview-copy"><div class="eyebrow">YOUR PLACE PREVIEW <span class="pill">${place.lat != null && place.lon != null ? "MAP SELECTED" : "PLACE DISCOVERY"}</span></div><h3>${esc(name)}</h3><p>${esc(place.extract || place.desc || "Explore local highlights, culture, food and experiences. Select a place to load available image and article information.")}</p><div class="destination-highlights">${(place.highlights || ["Local highlights","Food & cafés","Things to do"]).slice(0,3).map(t=>`<span>${esc(t)}</span>`).join("")}</div><div class="destination-attribution">${source}${place.credit ? ` · ${esc(place.credit)}` : ""}</div><div class="destination-actions"><button class="primary-btn" id="planSelectedPlace">Plan here ↗</button><button class="secondary-btn" id="searchSelectedPlace">Stays & tickets</button></div><p class="field-hint">Photos and place descriptions are sourced from Wikipedia/Wikimedia when available; fallback artwork is illustrative.</p></div></div>`;
    const tripButton = document.querySelector("#planSelectedPlace");
    if (tripButton) tripButton.onclick = () => { state.destination = name; setView("planner"); };
    const searchButton = document.querySelector("#searchSelectedPlace");
    if (searchButton) searchButton.onclick = () => { state.destination = name; setView("experiences"); };
    if (options.loading) panel.insertAdjacentHTML("beforeend", '<div class="destination-searching" id="destinationSearching">Finding a photo and a little local context…</div>');
  }

  async function enrichPlace(place) {
    const key = place?.name || place?.displayName;
    if (!key) return;
    const detail = await wikiSearch(key);
    if (!detail) return;
    // Only update the current panel if this is still the selected result.
    if (!state.selectedPlace || (state.selectedPlace.name || state.selectedPlace.displayName) !== key) return;
    const merged = { ...state.selectedPlace, ...detail, displayName: state.selectedPlace.displayName || undefined,
      name: state.selectedPlace.name || detail.name, lat: state.selectedPlace.lat, lon: state.selectedPlace.lon,
      desc: state.selectedPlace.desc || detail.extract, highlights: state.selectedPlace.highlights || ["Places to explore","Food & cafés","Local experiences"] };
    state.selectedPlace = merged;
    renderDestinationDetails(merged);
  }

  async function reverseMapClick(lat, lon) {
    const fallbackPlace = { name: `Place near ${lat.toFixed(3)}, ${lon.toFixed(3)}`, lat, lon, desc: "Finding the nearest named place…", photo: localFallback({name:"India"}), highlights:["Map selection","Explore nearby"] };
    renderDestinationDetails(fallbackPlace, { loading: true });
    try {
      const elapsed = Date.now() - lastReverseLookupAt;
      if (elapsed < 1100) await new Promise(resolve => setTimeout(resolve, 1100 - elapsed));
      lastReverseLookupAt = Date.now();
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}&zoom=10&addressdetails=1&accept-language=en`;
      const resp = await fetch(url, { headers: { "Accept": "application/json" } });
      if (!resp.ok) throw new Error("Place lookup is temporarily unavailable.");
      const data = await resp.json();
      const a = data.address || {};
      const locality = a.city || a.town || a.village || a.municipality || a.county || a.state_district || a.state || a.country || data.name || "Selected map area";
      const country = a.country && !String(locality).toLowerCase().includes(String(a.country).toLowerCase()) ? `, ${a.country}` : "";
      const place = { name: `${locality}${country}`, displayName: `${locality}${country}`, lat, lon, desc: data.name || data.display_name || "Explore this area on the map", photo: localFallback({name: `${locality} ${country}`}), highlights:[a.country || "Selected region", a.state || "Explore nearby", "Place discovery"] };
      if (!state.selectedPlace || Math.abs((state.selectedPlace.lat || 0) - lat) < 0.00001) renderDestinationDetails(place, { loading: true });
      await enrichPlace(place);
      const loading = document.querySelector("#destinationSearching"); if (loading) loading.remove();
    } catch (error) {
      const loading = document.querySelector("#destinationSearching"); if (loading) loading.remove();
      const p = document.querySelector("#destinationDetails");
      if (p) p.insertAdjacentHTML("beforeend", `<p class="field-hint">${esc(error.message || "Online place lookup failed.")} The map still works; try opening a marked destination or check your internet connection.</p>`);
    }
  }

  // The selected-place preview lives inside the map. The destination collection is a separate rail below it.
  window.exploreHTML = function () {
    return `${title("THE WORLD IS YOUR POSTCARD", "Find a place that feels like you.", "Move around the map, tap a marker or choose any point on Earth. Your selected place preview stays inside the map while the destination postcards wait below.")}
      <section class="atlas-map-panel panel"><div class="map-wrap atlas-map-wrap"><div id="map"></div><div class="map-hint">✦ Tap a pin or anywhere on the map to open its postcard</div><div id="destinationDetails" class="destination-discovery map-preview-dock" aria-live="polite"></div></div><div class="atlas-filter-bar"><span class="atlas-filter-label">Browse by feeling</span><button class="chip-btn active" data-filter="all">✦ All discoveries</button><button class="chip-btn" data-filter="nature">🌿 Nature</button><button class="chip-btn" data-filter="culture">🏛 Culture</button><button class="chip-btn" data-filter="food">🍜 Food & cafés</button></div><p class="atlas-explore-note">Map tiles by OpenStreetMap. Place photos and descriptions are loaded from Wikipedia/Wikimedia when available; fallback artwork is illustrative. Local listings and opening hours depend on live provider coverage.</p></section>
      <section class="atlas-destination-rail"><div class="atlas-rail-head"><div><div class="eyebrow">A FEW PLACES TO START WITH</div><h2>Pick your next postcard.</h2></div><p>Six little doors into very different worlds.</p></div><div id="destinationList" class="atlas-place-grid">${destinations.map((d,i)=>`<button type="button" class="atlas-destination-card" data-go="${i}"><img src="${esc(d.photo || localFallback(d))}" alt="${esc(d.name)} travel scene" loading="lazy"><div class="atlas-destination-card-copy"><small>${esc((d.highlights||[]).slice(0,2).join(" · ").toUpperCase())}</small><b>${esc(d.name)}</b><span>${esc(d.desc)}</span></div><span class="atlas-card-arrow">↗</span></button>`).join("")}</div></section>`;
  };

  window.wireExplore = function () {
    initMap();
    $$('[data-go]').forEach(button => button.onclick = () => {
      const d = destinations[Number(button.dataset.go)];
      if (d) { flyDestination(d); }
    });
    $$('[data-filter]').forEach(button => button.onclick = () => {
      $$('[data-filter]').forEach(item => item.classList.toggle('active', item === button));
      const type = button.dataset.filter;
      const keywords = { nature:/nature|wild|park|antarctica|coast|glacier|island/i, culture:/culture|temple|history|heritage|rome|kyoto/i, food:/food|cafe|restaurant|goa|rome|bali/i };
      const cards = $$('[data-go]');
      cards.forEach((card,i) => { const d=destinations[i]; card.hidden = type !== 'all' && !keywords[type]?.test(`${d.name} ${d.desc} ${(d.highlights||[]).join(' ')}`); });
      toast(type === 'all' ? 'Showing all six destination postcards.' : `Showing ${type} destinations.`);
    });
    const initial = state.selectedPlace || destinations[0];
    renderDestinationDetails(initial, { loading: true });
    enrichPlace(initial);
  };

  window.initMap = function (center) {
    const mapEl = document.querySelector("#map");
    if (!mapEl) return;
    if (!window.L) {
      // Offline atlas: the map remains visual and interactive even when Leaflet/tiles cannot load.
      const clampPct = value => Math.max(5, Math.min(95, value));
      const markers = destinations.map((place, index) => {
        const left = clampPct(((Number(place.lon) + 180) / 360) * 100);
        const top = clampPct(((90 - Number(place.lat)) / 180) * 100);
        return `<button type="button" class="offline-map-marker ${index === 0 ? "is-selected" : ""}" data-offline-dest="${index}" style="left:${left.toFixed(2)}%;top:${top.toFixed(2)}%" aria-label="Explore ${esc(place.name)}"><span class="offline-map-marker-pulse"></span><span class="offline-map-marker-core">${esc(place.emoji)}</span><span class="offline-map-marker-label">${esc(place.name.split(",")[0])}</span></button>`;
      }).join("");
      mapEl.innerHTML = `<div class="offline-atlas-map" role="group" aria-label="Illustrated interactive world map"><img class="offline-atlas-art" src="assets/world-map.svg" alt="Illustrated world map with continent shapes and suggested travel routes"><div class="offline-atlas-vignette" aria-hidden="true"></div><div class="offline-atlas-topline"><span><i></i> THE LIVING ATLAS</span><b>06 DESTINATION PORTALS</b></div><svg class="offline-atlas-route" viewBox="0 0 1000 540" preserveAspectRatio="none" aria-hidden="true"><path d="M710 224 Q610 72 535 160 T382 155 M710 224 Q800 130 880 180 T922 375 M710 224 Q770 290 900 470"/><path class="route-glint" d="M710 224 Q610 72 535 160 T382 155 M710 224 Q800 130 880 180 T922 375 M710 224 Q770 290 900 470"/></svg><div class="offline-atlas-stars" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>${markers}<div class="offline-atlas-compass" aria-hidden="true">N<span>✦</span></div><div class="offline-atlas-footnote"><span class="offline-atlas-live-dot"></span> DRAG AROUND · PICK A PIN · OPEN A POSTCARD</div></div>`;
      const offlineMap = mapEl.querySelector(".offline-atlas-map");
      // Subtle cursor-led map camera; pin clicks and keyboard interactions remain unchanged.
      const atlasArt = offlineMap.querySelector(".offline-atlas-art");
      offlineMap.addEventListener("pointermove", event => {
        if (event.pointerType === "touch" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        const rect = offlineMap.getBoundingClientRect();
        const x = (event.clientX - rect.left) / Math.max(1, rect.width);
        const y = (event.clientY - rect.top) / Math.max(1, rect.height);
        offlineMap.style.setProperty("--atlas-x", `${(x - .5) * -9}px`);
        offlineMap.style.setProperty("--atlas-y", `${(y - .5) * -7}px`);
        offlineMap.style.setProperty("--atlas-pointer-x", `${x * 100}%`);
        offlineMap.style.setProperty("--atlas-pointer-y", `${y * 100}%`);
        if (atlasArt) atlasArt.style.transform = `translate3d(${(x - .5) * -9}px, ${(y - .5) * -7}px, 0) scale(1.055)`;
      });
      offlineMap.addEventListener("pointerleave", () => {
        offlineMap.style.setProperty("--atlas-pointer-x", "50%");
        offlineMap.style.setProperty("--atlas-pointer-y", "50%");
        if (atlasArt) atlasArt.style.transform = "translate3d(0,0,0) scale(1.015)";
      });
      offlineMap.querySelectorAll("[data-offline-dest]").forEach(button => {
        button.addEventListener("click", event => {
          event.stopPropagation();
          const place = destinations[Number(button.dataset.offlineDest)];
          offlineMap.querySelectorAll(".offline-map-marker").forEach(pin => pin.classList.toggle("is-selected", pin === button));
          if (place) { renderDestinationDetails(place, { loading: true }); enrichPlace(place); }
        });
      });
      offlineMap.addEventListener("click", event => {
        if (event.target.closest("button")) return;
        const rect = offlineMap.getBoundingClientRect();
        const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
        const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));
        reverseMapClick(90 - y * 180, x * 360 - 180);
      });
      return;
    }
    if (state.map) { try { state.map.remove(); } catch (_) {} state.map = null; }
    state.map = L.map("map").setView(center || [20,0],1.25);
    if(window.CityPulseProviders)window.CityPulseProviders.addMapLayers(state.map);else L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(state.map);
    state.markers = [];
    destinations.forEach((d, i) => {
      const marker = L.marker([d.lat,d.lon]).addTo(state.map).bindPopup(`<b>${esc(d.emoji)} ${esc(d.name)}</b><br>${esc(d.desc)}<br><span class="field-hint">Click the map or open the preview panel for photos and details.</span>`);
      marker.on("click", () => { renderDestinationDetails(d, { loading:true }); enrichPlace(d); });
      state.markers.push(marker);
    });
    state.map.on("click", event => reverseMapClick(event.latlng.lat, event.latlng.lng));
    if (center) state.map.setView(center, 6);
    window.setTimeout(() => state.map?.invalidateSize(), 120);
  };

  window.chooseDest = function (index) {
    const place = destinations[Number(index)];
    if (!place) return;
    state.selectedPlace = place; state.destination = place.name;
    renderDestinationDetails(place, { loading:true }); enrichPlace(place);
  };
  window.flyDestination = function (place) {
    if (state.map && place?.lat != null && place?.lon != null) state.map.flyTo([place.lat,place.lon],6,{duration:1.15});
    state.selectedPlace = place; state.destination = place.name;
    renderDestinationDetails(place, { loading:true }); enrichPlace(place);
    toast("Place preview opened. Photos and descriptions are being checked.");
  };

  // Keep the home cards but hydrate them with destination imagery when the source is reachable.
  const baseWireHome = window.wireHome;
  window.wireHome = function () {
    baseWireHome();
    document.querySelectorAll(".destination-card[data-dest]").forEach(card => {
      card.onclick = () => {
        const place = destinations.find(d => d.name.toLowerCase() === card.dataset.dest.toLowerCase()) || { name:card.dataset.dest, photo:localFallback({name:card.dataset.dest}), desc:"Explore destination highlights" };
        state.selectedPlace = place; state.destination = place.name; setView("explore");
      };
    });
    // Keep the bundled illustrated covers on the landing page; source-backed place photos
    // load in the selected-place panel, where their article, image source and licence are shown.
  };
  async function hydrateHomePhotos() {
    const imgs = [...document.querySelectorAll("img[data-dest-photo]")];
    await Promise.all(imgs.map(async img => {
      const place = img.dataset.destPhoto;
      const result = await wikiSearch(place);
      if (result?.imageUrl && img.isConnected) {
        img.src = result.imageUrl; img.alt = `${place} · destination photo sourced from Wikipedia`; img.title = `${place}. ${result.credit || "Image source: Wikipedia"}`;
        const host = img.parentElement;
        let credit = host?.querySelector(".photo-credit");
        if (!credit && host) { credit=document.createElement("span"); credit.className="photo-credit"; credit.textContent="PHOTO PREVIEW · WIKIPEDIA"; host.appendChild(credit); }
      }
    }));
  }

  // Enrich chatbot output with the selected original character portrait.
  window.sendChat = function () {
    const input = document.querySelector("#chatInput"), text = input?.value.trim();
    if (!text) return;
    const box = document.querySelector("#chatBox");
    box.insertAdjacentHTML("beforeend", `<div class="bubble user">${esc(text)}</div>`);
    input.value = "";
    const response = companionResponse(text);
    const buddyMap = {Sprout:"sprout",Pip:"pip",Roo:"roo",Mira:"mira",Orbit:"orbit",Paws:"paws"};
    const slug = buddyMap[state.companion] || "sprout";
    window.setTimeout(() => {
      box.insertAdjacentHTML("beforeend", `<div class="bubble"><img class="chat-avatar" src="assets/companions/${slug}.webp" alt="${esc(state.companion)}">${esc(response)}</div>`);
      box.scrollTop = box.scrollHeight;
      if (window.speakReplies && "speechSynthesis" in window) { window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance(response)); }
    }, 350);
    box.scrollTop = box.scrollHeight;
  };
  // Re-render once after all feature overrides load so the first home-screen clicks use the updated behavior.
  if (state.view === "home" && typeof window.renderView === "function") window.renderView();
})();
