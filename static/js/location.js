(() => {
  const pageState = window.MIDWEST || {routes:[], selectedRoute:null};
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
  const headers = {'Content-Type':'application/json','X-CSRFToken':csrf};
  const checkpointIcon = L.divIcon({className:'map-marker-wrap',html:'<span class="map-marker checkpoint-marker">C</span>',iconSize:[32,38],iconAnchor:[16,34],popupAnchor:[0,-30]});
  const driverIcon = L.divIcon({className:'map-marker-wrap',html:'<span class="map-marker driver-marker">D</span>',iconSize:[32,38],iconAnchor:[16,19],popupAnchor:[0,-15]});
  const mapWith = (id, zoom=12) => {
    const el=document.getElementById(id); if(!el || !window.L) return null;
    const map=L.map(id).setView([28.2,83.98],zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
    return map;
  };
  const putMarkers=(map,items,markerIndex) => {
    if(!map)return;const pts=[];
    items.forEach(x=>{const p=[x.lat,x.lng];pts.push(p);const marker=L.marker(p,{icon:driverIcon}).addTo(map).bindPopup(`<strong>${escapeHtml(x.name)}</strong><br>${escapeHtml(x.role||'User')} location · accuracy ±${Math.round(x.accuracy||0)} m`);if(markerIndex&&x.id!==undefined)markerIndex.set(Number(x.id),marker);});
    if(pts.length)map.fitBounds(pts,{padding:[30,30],maxZoom:14});
  };
  const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fetchJson=async(url,opts={})=>{const r=await fetch(url,{...opts,headers:{...headers,...opts.headers}});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Request failed');return r.json();};

  const overviewMarkers=new Map();
  let overviewMap=null;
  for(const [id,endpoint] of [['overview-map','/super-admin/locations'],['hod-map','/api/location/drivers']]){
    const map=mapWith(id);if(id==='overview-map')overviewMap=map;if(map)fetchJson(endpoint).then(x=>putMarkers(map,x,id==='overview-map'?overviewMarkers:null)).catch(()=>{});
  }
  const statCards=document.querySelectorAll('.row.g-3.mb-4 .stat-card');
  if(statCards.length&&overviewMap){
    const modalNode=document.createElement('div');
    modalNode.className='modal fade';modalNode.tabIndex=-1;modalNode.innerHTML='<div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content"><div class="modal-header"><div><div class="eyebrow mb-1">SUPER ADMIN</div><h2 class="modal-title fs-5" id="summary-modal-title"></h2></div><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div><div class="modal-body" id="summary-modal-body"></div></div></div>';
    document.body.appendChild(modalNode);
    const modal=bootstrap.Modal.getOrCreateInstance(modalNode);
    const title=modalNode.querySelector('#summary-modal-title'),body=modalNode.querySelector('#summary-modal-body');
    const roleByLabel={'Total users':'all','Students':'student','Teachers':'teacher','Drivers':'driver','HOD/Admin':'admin'};
    const focusUser=(id,lat,lng,name)=>{
      const marker=overviewMarkers.get(Number(id));
      const target=marker||L.marker([lat,lng],{icon:driverIcon}).addTo(overviewMap);
      if(!marker)target.bindPopup(`<strong>${escapeHtml(name)}</strong><br>Consented location`);
      modal.hide();document.getElementById('overview-map').scrollIntoView({behavior:'smooth',block:'center'});
      window.setTimeout(()=>{overviewMap.invalidateSize();overviewMap.flyTo([lat,lng],16,{duration:0.8});target.openPopup();},250);
    };
    const openSummary=async(label)=>{
      title.textContent=label;body.innerHTML='<p class="text-muted mb-0">Loading…</p>';modal.show();
      try{
        const sharing=label==='Sharing consent';
        const rows=await fetchJson(sharing?'/super-admin/locations':`/super-admin/users?role=${encodeURIComponent(roleByLabel[label]||'all')}`);
        if(!rows.length){body.innerHTML='<p class="text-muted mb-0">No users to show.</p>';return;}
        if(sharing){
          body.innerHTML='<p class="text-muted">Select a user to focus the map on their latest consented location.</p><div class="summary-user-list"></div>';
          const list=body.querySelector('.summary-user-list');
          rows.forEach(u=>{const button=document.createElement('button');button.type='button';button.className='summary-user location-focus';button.innerHTML=`<span><strong>${escapeHtml(u.name)}</strong><small>${escapeHtml((u.role||'').replaceAll('_',' '))} · updated ${escapeHtml(new Date(u.time).toLocaleString())}</small></span><span aria-hidden="true">↗</span>`;button.addEventListener('click',()=>focusUser(u.id,u.lat,u.lng,u.name));list.appendChild(button);});
        }else{
          body.innerHTML='<div class="summary-user-list"></div>';const list=body.firstElementChild;
          rows.forEach(u=>{const row=document.createElement('div');row.className='summary-user';row.innerHTML=`<span><strong>${escapeHtml(u.name)}</strong><small>${escapeHtml(u.phone)} · ${escapeHtml(u.role.replaceAll('_',' '))}</small></span><span class="badge ${u.active?'text-bg-success':'text-bg-secondary'}">${u.active?'Active':'Inactive'}</span>`;list.appendChild(row);});
        }
      }catch(error){body.innerHTML=`<p class="text-danger mb-0">${escapeHtml(error.message)}</p>`;}
    };
    statCards.forEach(card=>{const label=card.querySelector('span')?.textContent.trim();if(!label)return;card.tabIndex=0;card.setAttribute('role','button');card.setAttribute('aria-label',`Open ${label} list`);card.addEventListener('click',()=>openSummary(label));card.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openSummary(label);}});});
  }
  const cpMap=mapWith('checkpoint-map');
  if(cpMap){let marker;cpMap.on('click',e=>{document.getElementById('latitude').value=e.latlng.lat.toFixed(7);document.getElementById('longitude').value=e.latlng.lng.toFixed(7);if(marker)marker.setLatLng(e.latlng);else marker=L.marker(e.latlng,{icon:checkpointIcon}).addTo(cpMap);});}
  const routeSel=document.getElementById('route-select'),cpForm=document.getElementById('checkpoint-form');
  if(routeSel&&cpForm)routeSel.addEventListener('change',()=>{if(routeSel.value)cpForm.action=`/hod/routes/${routeSel.value}/checkpoints`;});

  const dmap=mapWith('driver-map');
  if(dmap){(pageState.routes||[]).forEach(r=>(r.checkpoints||[]).forEach(c=>L.marker([c.lat,c.lng],{icon:checkpointIcon}).addTo(dmap).bindPopup(`<strong>Checkpoint:</strong> ${escapeHtml(c.name)}`)));}
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
      let ownMarker=null;
      watch=navigator.geolocation.watchPosition(async pos=>{const {latitude,longitude,accuracy}=pos.coords;try{await fetchJson('/api/location',{method:'POST',body:JSON.stringify({latitude,longitude,accuracy})});msg.textContent=`Updated · accuracy ±${Math.round(accuracy)} m`;if(dmap){const p=[latitude,longitude];dmap.setView(p,15);if(ownMarker)ownMarker.setLatLng(p);else ownMarker=L.marker(p,{icon:driverIcon}).addTo(dmap);ownMarker.bindPopup('Your current location');}}catch(e){msg.textContent=e.message;}},e=>{msg.textContent=e.message;setUI(false);},{enableHighAccuracy:true,maximumAge:5000,timeout:15000});
      window.midwestUploadTimer=setInterval(()=>{if(watch!==null&&navigator.geolocation)navigator.geolocation.getCurrentPosition(async p=>{try{await fetchJson('/api/location',{method:'POST',body:JSON.stringify({latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy})});}catch(e){msg.textContent=e.message;}},()=>{},{enableHighAccuracy:true,maximumAge:0});},15000);
    };
    stop.onclick=async()=>{if(watch!==null)navigator.geolocation.clearWatch(watch);watch=null;clearInterval(window.midwestUploadTimer);try{await fetchJson('/api/location/consent',{method:'POST',body:JSON.stringify({granted:false})});status.textContent='Consent withdrawn';msg.textContent='Sharing stopped and saved precise locations deleted.';}catch(e){msg.textContent=e.message;}setUI(false);};
  }
  const smap=mapWith('student-map');
  if(smap&&pageState.selectedRoute){fetchJson(`/api/location/route/${pageState.selectedRoute}`).then(data=>{
    const pts=[];data.checkpoints.forEach(c=>{pts.push([c.lat,c.lng]);L.marker([c.lat,c.lng],{icon:checkpointIcon}).addTo(smap).bindPopup(`<strong>Checkpoint:</strong> ${escapeHtml(c.name)}<br>${escapeHtml(c.description||'Pickup checkpoint')}`);});
    const box=document.getElementById('student-route-info');box.innerHTML=`<strong>${escapeHtml(data.name)}</strong>${data.vehicle?` · ${escapeHtml(data.vehicle)}`:''}<br>${data.drivers.map(d=>`Driver: ${escapeHtml(d.name)}${d.location?' · latest location available':' · not sharing'}`).join('<br>')||'No driver assigned yet.'}`;
    data.drivers.forEach(d=>{if(d.location){const p=[d.location.lat,d.location.lng];pts.push(p);L.marker(p,{icon:driverIcon}).addTo(smap).bindPopup(`Assigned driver: ${escapeHtml(d.name)}`);}});if(pts.length)smap.fitBounds(pts,{padding:[30,30],maxZoom:14});
  }).catch(e=>{document.getElementById('student-route-info').textContent=e.message;});}
})();
