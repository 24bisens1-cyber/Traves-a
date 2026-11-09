/* Provider-aware map layers: road, public NASA GIBS imagery, optional licensed MapTiler. */
(function () {
  'use strict';
  const ROAD = {url:'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>', maxZoom:19};
  async function addMapLayers(map) {
    if (!window.L || !map) return null;
    const road=L.tileLayer(ROAD.url,{maxZoom:ROAD.maxZoom,attribution:ROAD.attribution});
    road.addTo(map);
    let cfg={layers:[]};
    try {
      const response=await fetch('/api/maps/config',{headers:{Accept:'application/json'}});
      if(response.ok) cfg=await response.json();
    } catch (_) { return {road,satellite:null,layers:{},config:cfg}; }
    const layers={};
    for(const item of (cfg.layers||[])) {
      if(!item || !item.id || !item.tile_url) continue;
      layers[item.id]=L.tileLayer(item.tile_url,{
        maxZoom:20, maxNativeZoom:Number(item.max_native_zoom||9),
        attribution:item.attribution||item.provider||'Satellite imagery',
        crossOrigin:true, updateWhenIdle:true, keepBuffer:2
      });
    }
    const nasa=layers.nasa_gibs||null;
    const premium=layers.maptiler||null;
    const baselayers={'Road map · OpenStreetMap':road};
    if(nasa) baselayers['NASA daily satellite · global low detail']=nasa;
    if(premium) baselayers['MapTiler satellite · higher detail']=premium;
    const selected=cfg.default_layer==='maptiler'&&premium?premium:(cfg.default_layer==='nasa_gibs'&&nasa?nasa:road);
    if(selected!==road){road.remove();selected.addTo(map);}
    L.control.layers(baselayers,null,{collapsed:true,position:'topright'}).addTo(map);
    return {road,satellite:selected===road?(nasa||premium):selected,nasa,premium,layers,config:cfg};
  }
  async function loadWeather(latitude,longitude,forecastDays=3) {
    const query=new URLSearchParams({latitude:String(latitude),longitude:String(longitude),forecast_days:String(forecastDays)});
    const response=await fetch('/api/travel/weather?'+query.toString(),{headers:{Accept:'application/json'}});
    const body=await response.json().catch(()=>({}));
    if(!response.ok) { const error=new Error(body.error||`Weather request failed (${response.status})`); error.payload=body; throw error; }
    return body;
  }
  window.CityPulseProviders={addMapLayers,loadWeather};
})();
