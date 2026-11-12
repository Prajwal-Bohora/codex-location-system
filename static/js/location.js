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
  const fetchJson=async(url,opts={})=>{const r=await fetch(url,{cache:'no-store',...opts,headers:{...headers,...opts.headers}});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Request failed');return r.json();};
  const loadImage=url=>new Promise(resolve=>{if(!url){resolve(null);return;}const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>resolve(null);img.src=url;});
  const networkStatus=document.getElementById('driver-network-status');
  const updateNetworkStatus=()=>{if(!networkStatus)return;networkStatus.textContent=navigator.onLine?'Online':'Offline';networkStatus.classList.toggle('text-success',navigator.onLine);networkStatus.classList.toggle('text-danger',!navigator.onLine);};
  if(networkStatus){updateNetworkStatus();window.addEventListener('online',updateNetworkStatus);window.addEventListener('offline',updateNetworkStatus);}
  const announcementForm=document.getElementById('announcement-form');
  if(announcementForm)announcementForm.addEventListener('submit',()=>{
    for(const [localId,utcId] of [['event-at-local','event-at-utc'],['expires-at-local','expires-at-utc']]){
      const local=document.getElementById(localId),utc=document.getElementById(utcId);utc.value=local.value?new Date(local.value).toISOString():'';
    }
  });

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
  let draftCheckpointMarker=null;
  const selectedCheckpointLayer=cpMap?L.layerGroup().addTo(cpMap):null;
  if(cpMap){cpMap.on('click',e=>{document.getElementById('latitude').value=e.latlng.lat.toFixed(7);document.getElementById('longitude').value=e.latlng.lng.toFixed(7);if(draftCheckpointMarker)draftCheckpointMarker.setLatLng(e.latlng);else draftCheckpointMarker=L.marker(e.latlng,{icon:checkpointIcon}).addTo(cpMap);});}
  const routeSel=document.getElementById('route-select'),cpForm=document.getElementById('checkpoint-form');
  if(routeSel&&cpForm)routeSel.addEventListener('change',()=>{
    if(!routeSel.value){cpForm.removeAttribute('action');selectedCheckpointLayer?.clearLayers();return;}
    cpForm.action=`/hod/routes/${routeSel.value}/checkpoints`;
    selectedCheckpointLayer?.clearLayers();
    if(draftCheckpointMarker){cpMap.removeLayer(draftCheckpointMarker);draftCheckpointMarker=null;}
    document.getElementById('latitude').value='';document.getElementById('longitude').value='';
    const route=(pageState.routes||[]).find(item=>String(item.id)===routeSel.value);
    const points=[];
    (route?.checkpoints||[]).forEach(checkpoint=>{
      const point=[checkpoint.lat,checkpoint.lng];points.push(point);
      L.marker(point,{icon:checkpointIcon}).addTo(selectedCheckpointLayer).bindPopup(`<strong>Checkpoint:</strong> ${escapeHtml(checkpoint.name)}`);
    });
    if(points.length)cpMap.fitBounds(points,{padding:[30,30],maxZoom:15});
  });

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
  if(smap&&pageState.selectedRoute){
    const checkpointLayer=L.layerGroup().addTo(smap),driverLayer=L.layerGroup().addTo(smap);
    const box=document.getElementById('student-route-info');let firstLoad=true;let refreshTimer=null;
    const refreshDriverLocations=async()=>{
      try{
        const data=await fetchJson(`/api/location/route/${pageState.selectedRoute}`);
        const wasFirstLoad=firstLoad;
        if(firstLoad){
          data.checkpoints.forEach(c=>L.marker([c.lat,c.lng],{icon:checkpointIcon}).addTo(checkpointLayer).bindPopup(`<strong>Checkpoint:</strong> ${escapeHtml(c.name)}<br>${escapeHtml(c.description||'Pickup checkpoint')}`));
          firstLoad=false;
        }
        driverLayer.clearLayers();
        const statusRows=[];const livePoints=[];
        data.drivers.forEach(d=>{
          if(d.location){const p=[d.location.lat,d.location.lng];livePoints.push(p);L.marker(p,{icon:driverIcon}).addTo(driverLayer).bindPopup(`Assigned driver: ${escapeHtml(d.name)}<br>Updated: ${escapeHtml(new Date(d.location.time).toLocaleString())}`);statusRows.push(`<strong>${escapeHtml(d.name)}</strong> · updated ${escapeHtml(new Date(d.location.time).toLocaleString())}`);}
          else statusRows.push(`<strong>${escapeHtml(d.name)}</strong> · not currently sharing`);
        });
        box.innerHTML=`<strong>${escapeHtml(data.name)}</strong>${data.vehicle?` · ${escapeHtml(data.vehicle)}`:''}<div class="mt-2">${statusRows.join('<br>')||'No driver assigned yet.'}</div><small class="text-muted d-block mt-2">Driver locations refresh every 15 seconds. Last checked: ${escapeHtml(new Date().toLocaleTimeString())}</small>`;
        const allPoints=[...data.checkpoints.map(c=>[c.lat,c.lng]),...livePoints];
        if(wasFirstLoad&&allPoints.length)smap.fitBounds(allPoints,{padding:[30,30],maxZoom:14});
      }catch(error){box.textContent=error.message;}
    };
    refreshDriverLocations();refreshTimer=window.setInterval(refreshDriverLocations,15000);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshDriverLocations();});
    window.addEventListener('pagehide',()=>{if(refreshTimer)window.clearInterval(refreshTimer);},{once:true});
  }

  const studentCanvas=document.getElementById('student-id-card');
  const downloadCardButton=document.getElementById('download-student-card');
  if(studentCanvas&&downloadCardButton&&pageState.studentCard){
    const card=pageState.studentCard,ctx=studentCanvas.getContext('2d');
    const roundedPath=(x,y,w,h,r)=>{ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();};
    const drawCover=(img,x,y,w,h)=>{const scale=Math.max(w/img.width,h/img.height),sw=w/scale,sh=h/scale,sx=(img.width-sw)/2,sy=(img.height-sh)/2;ctx.drawImage(img,sx,sy,sw,sh,x,y,w,h);};
    const drawCard=async()=>{
      const [logo,photo]=await Promise.all([loadImage(card.logoUrl),loadImage(card.photoUrl)]);
      const w=studentCanvas.width,h=studentCanvas.height;ctx.clearRect(0,0,w,h);ctx.fillStyle='#fff';ctx.fillRect(0,0,w,h);
      ctx.save();ctx.globalAlpha=.055;if(logo){const crop=logo.width*.63;ctx.drawImage(logo,(logo.width-crop)/2,(logo.height-crop)/2,crop,crop,1040,365,500,500);}ctx.restore();
      ctx.fillStyle='#30343a';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(1190,0);ctx.lineTo(925,245);ctx.lineTo(95,245);ctx.lineTo(0,285);ctx.closePath();ctx.fill();
      ctx.fillStyle='#2799e8';ctx.beginPath();ctx.moveTo(1190,0);ctx.lineTo(w,0);ctx.lineTo(w,145);ctx.lineTo(1030,145);ctx.closePath();ctx.fill();
      if(logo){const crop=logo.width*.63;ctx.save();roundedPath(78,47,145,145,72);ctx.clip();ctx.fillStyle='#fff';ctx.fillRect(78,47,145,145);ctx.drawImage(logo,(logo.width-crop)/2,(logo.height-crop)/2,crop,crop,78,47,145,145);ctx.restore();}
      ctx.fillStyle='#fff';ctx.font='700 54px Manrope, Arial, sans-serif';ctx.fillText('MID-WESTERN UNIVERSITY',260,112,820);
      ctx.fillStyle='#dce5ee';ctx.font='500 30px "DM Sans", Arial, sans-serif';ctx.fillText('STUDENT IDENTITY CARD',264,164);
      ctx.fillStyle='#e9eef3';roundedPath(90,315,438,540,18);ctx.fill();
      if(photo){ctx.save();roundedPath(100,325,418,520,12);ctx.clip();drawCover(photo,100,325,418,520);ctx.restore();}
      else{ctx.save();roundedPath(100,325,418,520,12);ctx.fillStyle='#e9eef3';ctx.fill();ctx.fillStyle='#2467a5';ctx.font='700 140px Manrope, Arial, sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText((card.name||'S').trim().charAt(0).toUpperCase(),309,585);ctx.textAlign='left';ctx.textBaseline='alphabetic';ctx.restore();}
      const detail=(label,value,y,size=48)=>{ctx.fillStyle='#637180';ctx.font='400 30px "DM Sans", Arial, sans-serif';ctx.fillText(label,610,y);ctx.fillStyle='#141b22';ctx.font=`700 ${size}px Manrope, Arial, sans-serif`;ctx.fillText(value||'Not provided',610,y+58,875);};
      detail('NAME',card.name,365,58);detail('STUDENT ID',card.studentId,520,50);detail('PROGRAMME / DEPARTMENT',card.department,675,43);detail('YEAR LEVEL',card.yearLevel,815,44);
      ctx.fillStyle='#14856e';roundedPath(1190,825,300,70,18);ctx.fill();ctx.fillStyle='#fff';ctx.font='700 28px "DM Sans", Arial, sans-serif';ctx.textAlign='center';ctx.fillText(String(card.status||'Active').toUpperCase(),1340,871);ctx.textAlign='left';
      ctx.fillStyle='#30343a';ctx.beginPath();ctx.moveTo(0,930);ctx.lineTo(1450,930);ctx.lineTo(1380,h);ctx.lineTo(0,h);ctx.closePath();ctx.fill();ctx.fillStyle='#2799e8';ctx.beginPath();ctx.moveTo(0,930);ctx.lineTo(165,930);ctx.lineTo(95,h);ctx.lineTo(0,h);ctx.closePath();ctx.fill();
      ctx.fillStyle='#dce5ee';ctx.font='500 24px "DM Sans", Arial, sans-serif';ctx.fillText('MID-WEST APP · PRIVACY-AWARE UNIVERSITY TRANSPORT',220,978);
    };
    drawCard();
    downloadCardButton.addEventListener('click',()=>{
      studentCanvas.toBlob(blob=>{if(!blob)return;const link=document.createElement('a');link.href=URL.createObjectURL(blob);const safeId=String(card.studentId||'student').replace(/[^a-z0-9_-]+/gi,'-');link.download=`midwest-student-id-${safeId}.png`;link.click();URL.revokeObjectURL(link.href);},'image/png');
    });
  }
})();
