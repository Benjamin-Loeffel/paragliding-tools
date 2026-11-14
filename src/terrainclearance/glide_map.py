"""2D-Gleitkarte (OpenLayers, wie Flightbook): Spur nach Vario eingefärbt, Gleitstrecken mit Gleitzahl.

Eigenständige HTML-Datei: OpenLayers 9.2.4 vom CDN (dieselbe Bibliothek und Version wie die
Flightbook-App), Kartengrund umschaltbar (OpenStreetMap, swisstopo Landeskarte, swisstopo Luftbild).
Die Vario-Farbrampe ist die von Flightbook (blau sinken, grün um null, rot steigen, ±5 m/s), damit
die Ansicht als Prototyp für ein Gleitzahl-Labor in Flightbook direkt vergleichbar ist.
"""

from __future__ import annotations

import json
from html import escape

import numpy as np

from .glide import glide_segments

_FLIGHT_COLORS = ["#e41a1c", "#377eb8", "#ff7f00", "#984ea3", "#a65628", "#f781bf", "#17becf", "#4daf4a"]


def _vario(alt: np.ndarray, t_s: np.ndarray, half: int = 3) -> np.ndarray:
    """Vario aus der Höhe, gleitender Mittelwert über ±half Fixe (wie Flightbook)."""
    t = np.asarray(t_s, float)
    z = np.asarray(alt, float)
    v = np.zeros_like(z)
    dt = np.diff(t)
    ok = dt > 0
    raw = np.zeros(z.size - 1)
    raw[ok] = np.diff(z)[ok] / dt[ok]
    raw = np.r_[raw, raw[-1:]] if raw.size else np.zeros_like(z)
    k = np.ones(2 * half + 1) / (2 * half + 1)
    v = np.convolve(np.pad(raw, (half, half), mode="edge"), k, mode="valid")
    return v


def flight_payload(f: dict, times: list, nr: int, min_s: float) -> dict:
    """Daten eines Flugs für die Karte (Listen, auf 5 Nachkommastellen gerundet)."""
    gz = glide_segments(f["e"], f["n"], f["alt"], f["t_s"], f["valid"], min_s=min_s)
    vario = _vario(f["alt"], f["t_s"])
    segs = [dict(i0=s.i0, i1=s.i1, gzg=round(s.glide_ground, 2), gzl=round(s.glide_air, 2),
                 dur=round(s.duration_s), len=round(s.length_m), loss=round(s.loss_m),
                 sink=round(s.sink_mps, 2), gs=round(s.gs_kmh, 1), air=round(s.airspeed_kmh, 1),
                 kurs=round(s.bearing_deg), von=f"{times[s.i0]:%H:%M:%S}", bis=f"{times[s.i1]:%H:%M:%S}")
            for s in gz.segments]
    st = gz.straight or {}
    return dict(
        nr=nr, name=f.get("name", f"Flug {nr}"), color=_FLIGHT_COLORS[(nr - 1) % len(_FLIGHT_COLORS)],
        start=f"{times[0]:%H:%M}", ende=f"{times[-1]:%H:%M}", datum=f"{times[0]:%d.%m.%Y}",
        lon=np.round(np.asarray(f["lon"], float), 6).tolist(), lat=np.round(np.asarray(f["lat"], float), 6).tolist(),
        alt=np.round(np.asarray(f["alt"], float)).astype(int).tolist(),
        vario=np.round(vario, 2).tolist(), time=[f"{t:%H:%M:%S}" for t in times],
        segs=segs,
        summary=dict(gzg=round(st.get("glide_ground", float("nan")), 1) if st else None,
                     gzl=round(st.get("glide_air", float("nan")), 1) if st else None,
                     track=round(gz.glide_track, 1) if np.isfinite(gz.glide_track) else None,
                     sink=round(st.get("sink_mps", float("nan")), 2) if st else None,
                     air=round(st.get("airspeed_kmh", float("nan"))) if st else None,
                     wind=round(gz.wind_kmh) if np.isfinite(gz.wind_kmh) else None,
                     windfrom=round(gz.wind_from_deg) if np.isfinite(gz.wind_from_deg) else None),
    )


def build_glide_map_html(flights: list[dict], title: str) -> str:
    data = json.dumps(flights, separators=(",", ":"))
    return _TEMPLATE.replace("__TITLE__", escape(title)).replace("__DATA__", data)


_TEMPLATE = r"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@9.2.4/ol.css">
<script src="https://cdn.jsdelivr.net/npm/ol@9.2.4/dist/ol.js"></script>
<style>
:root{--bg:#f4f6f8;--panel:#ffffff;--ink:#10293c;--muted:#5d6f7d;--line:#d7dee4;--accent:#1f6fa8}
@media (prefers-color-scheme:dark){:root{--bg:#0f161c;--panel:#17212a;--ink:#e6edf3;--muted:#9aabb8;--line:#2a3946;--accent:#6cb4e6}}
html,body{height:100%;margin:0}
body{font-family:"Segoe UI",system-ui,sans-serif;font-size:14px;color:var(--ink);background:var(--bg);display:grid;grid-template-columns:minmax(260px,330px) 1fr;grid-template-rows:100%}
@media (max-width:760px){body{grid-template-columns:1fr;grid-template-rows:auto 70vh;height:auto}}
aside{overflow:auto;padding:14px 16px;border-right:1px solid var(--line);background:var(--panel);display:grid;gap:14px;align-content:start}
h1{font-size:18px;margin:0;line-height:1.2}
.sub{color:var(--muted);font-size:13px;margin-top:2px}
.grp{display:grid;gap:6px}
.grp > b{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.seg{display:flex;flex-wrap:wrap;gap:4px}
.seg button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:6px;padding:4px 9px;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--ink);color:var(--panel);border-color:var(--ink)}
.flight{display:grid;grid-template-columns:auto 1fr;gap:2px 8px;align-items:start;padding:8px;border:1px solid var(--line);border-radius:8px;cursor:pointer}
.flight input{margin:3px 0 0;accent-color:var(--accent)}
.flight .h{font-weight:600;display:flex;align-items:center;gap:6px}
.flight .chip{width:12px;height:12px;border-radius:3px;display:inline-block}
.flight .s{grid-column:2;color:var(--muted);font-size:12.5px;font-variant-numeric:tabular-nums;line-height:1.45}
.flight .s b{color:var(--ink)}
.legend{display:grid;gap:4px;font-size:12px;color:var(--muted)}
.ramp{height:10px;border-radius:3px}
.ticks{display:flex;justify-content:space-between;font-variant-numeric:tabular-nums}
#map{position:relative;min-height:300px}
.popup{position:absolute;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;line-height:1.45;box-shadow:0 4px 14px rgba(0,0,0,.18);transform:translate(-50%,calc(-100% - 12px));white-space:nowrap;pointer-events:none;font-variant-numeric:tabular-nums}
.popup b{font-size:15px}
.note{font-size:12px;color:var(--muted);line-height:1.4}
</style></head>
<body>
<aside>
  <div><h1>__TITLE__</h1><div class="sub" id="sub"></div></div>
  <div class="grp"><b>Karte</b><div class="seg" id="base">
    <button data-k="osm" aria-pressed="true">OpenStreetMap</button><button data-k="topo">OpenTopoMap</button><button data-k="lk">Landeskarte</button><button data-k="img">Luftbild</button></div></div>
  <div class="grp"><b>Spur einfärben</b><div class="seg" id="mode">
    <button data-k="vario" aria-pressed="true">Steigen/Sinken</button><button data-k="flight">Je Flug</button></div></div>
  <div class="grp"><b>Gleitzahl zeigen</b><div class="seg" id="gzmode">
    <button data-k="g" aria-pressed="true">Über Grund</button><button data-k="l">In der Luft</button><button data-k="off">Aus</button></div></div>
  <div class="grp"><b>Flüge</b><div id="flights" class="grp"></div></div>
  <div class="legend"><span>Steigen/Sinken (m/s), Farben wie Flightbook</span><div class="ramp" id="vramp"></div><div class="ticks"><span>−5</span><span>0</span><span>+5</span></div>
    <span style="margin-top:6px">Gleitzahl der geraden Strecken (≥ 20 s)</span><div class="ramp" id="gramp"></div><div class="ticks"><span>4</span><span>7</span><span>10</span></div></div>
  <p class="note">Gerade Strecke = mindestens 20 s ohne Kurve. Gleitzahl über Grund = Weg / Höhenverlust; in der Luft mit dem Wind, der aus den Kreisen geschätzt ist. Steigen oder Sinken der Luft steckt in jeder Zahl drin. Klick auf eine Strecke zeigt Details.</p>
</aside>
<div id="map"></div>
<script>
const FLIGHTS = __DATA__;
const VSTOPS=[[-5,[21,82,184]],[-3,[43,143,214]],[-1.5,[63,201,201]],[-.4,[90,200,120]],[.4,[162,205,70]],[1.5,[242,196,61]],[3,[240,138,44]],[5,[214,59,42]]];
const VIRIDIS=[[0,[68,1,84]],[.25,[59,82,139]],[.5,[33,145,140]],[.75,[94,201,98]],[1,[253,231,37]]];
function ramp(stops,x){x=Math.min(stops[stops.length-1][0],Math.max(stops[0][0],x));for(let i=0;i<stops.length-1;i++){const[a,ca]=stops[i],[b,cb]=stops[i+1];if(x>=a&&x<=b){const t=b>a?(x-a)/(b-a):0;return `rgb(${ca.map((c,k)=>Math.round(c+(cb[k]-c)*t)).join(",")})`}}return `rgb(${stops[0][1].join(",")})`}
const vcol=v=>ramp(VSTOPS,Number.isFinite(v)?v:0);
const gcol=g=>ramp(VIRIDIS,(g-4)/6);
document.getElementById("vramp").style.background=`linear-gradient(90deg,${VSTOPS.map(([a])=>vcol(a)+" "+((a+5)*10).toFixed(0)+"%").join(",")})`;
document.getElementById("gramp").style.background=`linear-gradient(90deg,${[4,5.5,7,8.5,10].map(g=>gcol(g)).join(",")})`;
document.getElementById("sub").textContent=FLIGHTS.length?`${FLIGHTS[0].datum} · ${FLIGHTS.length} Flug${FLIGHTS.length>1?"e":""}`:"";

const {Map,View,Feature,Overlay}=ol;const {LineString,Point}=ol.geom;const {fromLonLat}=ol.proj;
const S=ol.style;
const XYZ=(url,att)=>new ol.layer.Tile({source:new ol.source.XYZ({url,attributions:att,crossOrigin:"anonymous",maxZoom:19}),visible:false});
// OpenStreetMap über den Server der deutschen OSM-Community: tile.openstreetmap.org verlangt einen Referer,
// den eine lokal geöffnete Datei nicht sendet. OpenTopoMap = OSM-Daten mit Höhenlinien und Schummerung.
const bases={osm:new ol.layer.Tile({source:new ol.source.XYZ({url:"https://tile.openstreetmap.de/{z}/{x}/{y}.png",attributions:"© OpenStreetMap contributors",crossOrigin:"anonymous",maxZoom:19})}),
  topo:XYZ("https://{a-c}.tile.opentopomap.org/{z}/{x}/{y}.png","© OpenStreetMap contributors, SRTM · Kartendarstellung © OpenTopoMap (CC-BY-SA)"),
  lk:XYZ("https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg","© swisstopo"),
  img:XYZ("https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage/default/current/3857/{z}/{x}/{y}.jpeg","© swisstopo")};
const trackSrc=new ol.source.Vector(),glideSrc=new ol.source.Vector(),labelSrc=new ol.source.Vector(),endSrc=new ol.source.Vector();
const casing=new S.Style({stroke:new S.Stroke({color:"rgba(16,41,60,.38)",width:7})});
const trackLayer=new ol.layer.Vector({source:trackSrc,style:f=>[casing,new S.Style({stroke:new S.Stroke({color:f.get("c"),width:4})})]});
const glideLayer=new ol.layer.Vector({source:glideSrc,style:f=>[new S.Style({stroke:new S.Stroke({color:"rgba(0,0,0,.55)",width:11})}),new S.Style({stroke:new S.Stroke({color:f.get("c"),width:7})})]});
const labelLayer=new ol.layer.Vector({source:labelSrc,declutter:true,style:f=>new S.Style({text:new S.Text({text:f.get("t"),font:"600 13px Segoe UI,system-ui,sans-serif",fill:new S.Fill({color:"#10293c"}),backgroundFill:new S.Fill({color:"rgba(255,255,255,.92)"}),backgroundStroke:new S.Stroke({color:f.get("c"),width:2}),padding:[2,5,1,5],offsetY:-16})})});
const endLayer=new ol.layer.Vector({source:endSrc,style:f=>new S.Style({image:new S.Circle({radius:6,fill:new S.Fill({color:f.get("c")}),stroke:new S.Stroke({color:"#fff",width:2})})})});
const map=new Map({target:"map",layers:[bases.osm,bases.topo,bases.lk,bases.img,trackLayer,glideLayer,endLayer,labelLayer],view:new View({center:fromLonLat([7.6,46.6]),zoom:13})});

const state={base:"osm",mode:"vario",gz:"g",on:new Set(FLIGHTS.map(f=>f.nr))};
function draw(){
  trackSrc.clear();glideSrc.clear();labelSrc.clear();endSrc.clear();
  const ext=ol.extent.createEmpty();
  FLIGHTS.forEach(f=>{
    if(!state.on.has(f.nr))return;
    const pts=f.lon.map((x,i)=>fromLonLat([x,f.lat[i]]));
    ol.extent.extend(ext,new LineString(pts).getExtent());
    if(state.mode==="flight"){trackSrc.addFeature(new Feature({geometry:new LineString(pts),c:f.color}))}
    else{ // Läufe gleicher Farbstufe (24 Stufen wie Flightbook)
      const step=v=>Math.min(23,Math.max(0,Math.floor((Math.min(5,Math.max(-5,v))+5)/10*24)));
      let i0=0,s0=step(f.vario[0]);
      for(let i=1;i<=pts.length;i++){const s=i<pts.length?step(f.vario[i]):-1;if(s!==s0){trackSrc.addFeature(new Feature({geometry:new LineString(pts.slice(i0,i+1<=pts.length?i+1:i)),c:vcol(-5+(s0+.5)*10/24)}));i0=i;s0=s}}
    }
    endSrc.addFeature(new Feature({geometry:new Point(pts[0]),c:"#22a95c"}));
    endSrc.addFeature(new Feature({geometry:new Point(pts[pts.length-1]),c:"#e0483a"}));
    if(state.gz==="off")return;
    const multi=FLIGHTS.filter(x=>state.on.has(x.nr)).length>1;
    f.segs.forEach(s=>{
      const g=state.gz==="g"?s.gzg:s.gzl;
      const line=new LineString(pts.slice(s.i0,s.i1+1));
      glideSrc.addFeature(new Feature({geometry:line,c:gcol(g),seg:s,flight:f}));
      const mid=pts[Math.floor((s.i0+s.i1)/2)];
      labelSrc.addFeature(new Feature({geometry:new Point(mid),t:(multi?f.nr+": ":"")+"GZ "+g.toFixed(1),c:gcol(g)}));
    });
  });
  if(!ol.extent.isEmpty(ext))draw.ext=ext;
  if(draw.ext&&!draw.fitted){map.getView().fit(draw.ext,{padding:[40,40,40,40],maxZoom:16});draw.fitted=true}
}
// Kartenausschnitt nachführen, solange die Seite noch ihr Layout findet (erste 2 s)
const t0=Date.now();new ResizeObserver(()=>{map.updateSize();if(Date.now()-t0<2000&&draw.ext)map.getView().fit(draw.ext,{padding:[40,40,40,40],maxZoom:16})}).observe(document.getElementById("map"));
function seg(id,key,cb){document.querySelectorAll(`#${id} button`).forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll(`#${id} button`).forEach(x=>x.setAttribute("aria-pressed",String(x===b)));state[key]=b.dataset.k;cb();}))}
seg("base","base",()=>Object.entries(bases).forEach(([k,l])=>l.setVisible(k===state.base)));
// Kartengrund über die Adresse vorwählen: …_gleitkarte.html#topo, #lk, #img
{const h=location.hash.slice(1);const b=document.querySelector(`#base button[data-k="${h}"]`);if(b)b.click();}
seg("mode","mode",draw);seg("gzmode","gz",draw);
const fl=document.getElementById("flights");
FLIGHTS.forEach(f=>{
  const s=f.summary||{};const lab=document.createElement("label");lab.className="flight";
  const cb=document.createElement("input");cb.type="checkbox";cb.checked=true;cb.addEventListener("change",()=>{cb.checked?state.on.add(f.nr):state.on.delete(f.nr);draw()});
  const h=document.createElement("span");h.className="h";const chip=document.createElement("span");chip.className="chip";chip.style.background=f.color;h.append(chip,document.createTextNode(`Flug ${f.nr} · ${f.start}–${f.ende}`));
  const d=document.createElement("span");d.className="s";
  const fmt=(x,n=1)=>x==null||!isFinite(x)?"–":Number(x).toFixed(n);
  d.innerHTML=`Geradeaus <b>${fmt(s.gzg)}</b> über Grund · <b>${fmt(s.gzl)}</b> in der Luft<br>Ganzer Flugweg ${fmt(s.track)} · Sinken ${fmt(s.sink,2)} m/s<br>Fahrt ${fmt(s.air,0)} km/h · Wind ${fmt(s.wind,0)} km/h aus ${fmt(s.windfrom,0)}°`;
  lab.append(cb,h,document.createElement("span"),d);fl.append(lab);
});
// Popup für Gleitstrecken
const pop=document.createElement("div");pop.className="popup";pop.hidden=true;
const ov=new Overlay({element:pop,stopEvent:false});map.addOverlay(ov);
map.on("click",e=>{
  const f=map.forEachFeatureAtPixel(e.pixel,x=>x.get("seg")?x:null,{layerFilter:l=>l===glideLayer,hitTolerance:6});
  if(!f){pop.hidden=true;return}
  const s=f.get("seg"),fl=f.get("flight");
  pop.innerHTML=`Flug ${fl.nr} · ${s.von}–${s.bis} · ${s.dur} s<br><b>GZ ${s.gzg.toFixed(1)}</b> über Grund · ${s.gzl.toFixed(1)} in der Luft<br>${s.len} m · Δh ${s.loss} m · Sinken ${s.sink.toFixed(2)} m/s<br>GS ${s.gs.toFixed(0)} km/h · Fahrt ${s.air.toFixed(0)} km/h · Kurs ${s.kurs}°`;
  pop.hidden=false;ov.setPosition(e.coordinate);
});
map.on("pointermove",e=>{const hit=map.hasFeatureAtPixel(e.pixel,{layerFilter:l=>l===glideLayer,hitTolerance:6});map.getTargetElement().style.cursor=hit?"pointer":""});
draw();
</script>
</body></html>
"""
