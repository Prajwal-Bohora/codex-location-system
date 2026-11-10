(() => {
  const pageState = window.MIDWEST || {routes:[], selectedRoute:null};
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
  const headers = {'Content-Type':'application/json','X-CSRFToken':csrf};
  const mapWith = (id, zoom=12) => {
    const el=document.getElementById(id); if(!el || !window.L) return null;
    const map=L.map(id).setView([28.2,83.98],zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
    return map;
  };
  const putMarkers=(map,items,iconColor) => {
    if(!map)return;const pts=[];
    items.forEach(x=>{const p=[x.lat,x.lng];pts.push(p);L.marker(p).addTo(map).bindPopup(`<strong>${escapeHtml(x.name)}</strong><br>Accuracy ±${Math.round(x.accuracy||0)} m`);});
    if(pts.length)map.fitBounds(pts,{padding:[30,30],maxZoom:14});
  };
  const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fetchJson=async(url,opts={})=>{const r=await fetch(url,{...opts,headers:{...headers,...opts.headers}});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Request failed');return r.json();};

  for(const [id,endpoint] of [['overview-map','/super-admin/locations'],['hod-map','/api/location/drivers']]){
    const map=mapWith(id);if(map)fetchJson(endpoint).then(x=>putMarkers(map,x)).catch(()=>{});
  }
  const cpMap=mapWith('checkpoint-map');
  if(cpMap){let marker;cpMap.on('click',e=>{document.getElementById('latitude').value=e.latlng.lat.toFixed(7);document.getElementById('longitude').value=e.latlng.lng.toFixed(7);if(marker)marker.setLatLng(e.latlng);else marker=L.marker(e.latlng).addTo(cpMap);});}
  const routeSel=document.getElementById('route-select'),cpForm=document.getElementById('checkpoint-form');
  if(routeSel&&cpForm)routeSel.addEventListener('change',()=>{if(routeSel.value)cpForm.action=`/hod/routes/${routeSel.value}/checkpoints`;});

  const dmap=mapWith('driver-map');
  if(dmap){(pageState.routes||[]).forEach(r=>(r.checkpoints||[]).forEach(c=>L.marker([c.lat,c.lng]).addTo(dmap).bindPopup(escapeHtml(c.name))));}
  const start=document.getElementById('start-sharing'),stop=document.getElementById('stop-sharing'),status=document.getElementById('sharing-status'),msg=document.getElementById('gps-message');
  if(start&&stop){let watch=null;
    const setUI=on=>{status.textContent=on?'Sharing location':'Not sharing';start.disabled=on;stop.disabled=!on;};
    fetchJson('/api/location/status').then(s=>{if(s.granted){status.textContent='Consent granted · not currently sharing';}}).catch(()=>{});
    start.onclick=async()=>{
      const ok=window.confirm('Location privacy notice\n\nWhile sharing, MID-WEST APP collects your precise GPS coordinates, accuracy, and timestamp. It is used to help coordinate bus pickups. Super Admin and HOD/Admin can view driver locations; students on your assigned route can view the assigned driver. You can stop sharing at any time. If you withdraw consent, saved precise location records are deleted.\n\nGrant consent and start sharing?');
      if(!ok)return;
      if(!navigator.geolocation){msg.textContent='GPS is unavailable in this browser.';return;}
      try{await fetchJson('/api/location/consent',{method:'POST',body:JSON.stringify({granted:true})});}catch(e){msg.textContent=e.message;return;}
      setUI(true);msg.textContent='Waiting for GPS…';
      watch=navigator.geolocation.watchPosition(async pos=>{const {latitude,longitude,accuracy}=pos.coords;try{await fetchJson('/api/location',{method:'POST',body:JSON.stringify({latitude,longitude,accuracy})});msg.textContent=`Updated · accuracy ±${Math.round(accuracy)} m`;if(dmap){const p=[latitude,longitude];dmap.setView(p,15);L.circleMarker(p,{radius:8}).addTo(dmap).bindPopup('Your current location');}}catch(e){msg.textContent=e.message;}},e=>{msg.textContent=e.message;setUI(false);},{enableHighAccuracy:true,maximumAge:5000,timeout:15000});
      window.midwestUploadTimer=setInterval(()=>{if(watch!==null&&navigator.geolocation)navigator.geolocation.getCurrentPosition(async p=>{try{await fetchJson('/api/location',{method:'POST',body:JSON.stringify({latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy})});}catch(e){msg.textContent=e.message;}},()=>{},{enableHighAccuracy:true,maximumAge:0});},15000);
    };
    stop.onclick=async()=>{if(watch!==null)navigator.geolocation.clearWatch(watch);watch=null;clearInterval(window.midwestUploadTimer);try{await fetchJson('/api/location/consent',{method:'POST',body:JSON.stringify({granted:false})});status.textContent='Consent withdrawn';msg.textContent='Sharing stopped and saved precise locations deleted.';}catch(e){msg.textContent=e.message;}setUI(false);};
  }
  const smap=mapWith('student-map');
  if(smap&&pageState.selectedRoute){fetchJson(`/api/location/route/${pageState.selectedRoute}`).then(data=>{
    const pts=[];data.checkpoints.forEach(c=>{pts.push([c.lat,c.lng]);L.marker([c.lat,c.lng]).addTo(smap).bindPopup(`<strong>${escapeHtml(c.name)}</strong><br>${escapeHtml(c.description||'Pickup checkpoint')}`);});
    const box=document.getElementById('student-route-info');box.innerHTML=`<strong>${escapeHtml(data.name)}</strong>${data.vehicle?` · ${escapeHtml(data.vehicle)}`:''}<br>${data.drivers.map(d=>`Driver: ${escapeHtml(d.name)}${d.location?' · latest location available':' · not sharing'}`).join('<br>')||'No driver assigned yet.'}`;
    data.drivers.forEach(d=>{if(d.location){const p=[d.location.lat,d.location.lng];pts.push(p);L.circleMarker(p,{radius:9,color:'#e7663e'}).addTo(smap).bindPopup(`Assigned driver: ${escapeHtml(d.name)}`);}});if(pts.length)smap.fitBounds(pts,{padding:[30,30],maxZoom:14});
  }).catch(e=>{document.getElementById('student-route-info').textContent=e.message;});}
})();
