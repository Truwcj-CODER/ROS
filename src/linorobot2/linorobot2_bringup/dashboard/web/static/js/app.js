const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');

let mapImg    = null;
let mapInfo   = null;
let robotPose = null;
let navStatus = {navigating: false, returning_home: false, wp_idx: 0, wp_total: 0, loop: false};

// ── Initial pose state ────────────────────────────────────────────────────────
let poseMode     = false;
let initPose     = null;   // {x, y, theta} — displayed orange arrow
let poseDrag     = null;   // {px, py, ex, ey} during drag
let _justSetPose = false;  // guard: prevent click handler firing after mouseup

// ── Waypoints: persisted in localStorage ─────────────────────────────────────
let waypoints = [];

function saveWaypoints() {
  try { localStorage.setItem('robot_waypoints', JSON.stringify(waypoints)); } catch (_) {}
}
function loadWaypoints() {
  try {
    const s = localStorage.getItem('robot_waypoints');
    if (s) waypoints = JSON.parse(s);
  } catch (_) {}
}
loadWaypoints();

// ── Coordinate conversion ─────────────────────────────────────────────────────
function w2c(wx, wy) {
  if (!mapInfo) return {px: 0, py: 0};
  return {
    px: (wx - mapInfo.origin_x) / mapInfo.resolution,
    py: mapInfo.height - 1 - (wy - mapInfo.origin_y) / mapInfo.resolution
  };
}
function c2w(px, py) {
  if (!mapInfo) return {x: 0, y: 0};
  return {
    x: Math.round((mapInfo.origin_x + px * mapInfo.resolution) * 100) / 100,
    y: Math.round((mapInfo.origin_y + (mapInfo.height - 1 - py) * mapInfo.resolution) * 100) / 100
  };
}

// ── Draw ──────────────────────────────────────────────────────────────────────
function draw() {
  if (!mapImg) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(mapImg, 0, 0);

  // Connecting lines
  for (let i = 0; i < waypoints.length - 1; i++) {
    const {px, py}   = w2c(waypoints[i].x,     waypoints[i].y);
    const {px: nx, py: ny} = w2c(waypoints[i+1].x, waypoints[i+1].y);
    ctx.beginPath();
    ctx.moveTo(px, py); ctx.lineTo(nx, ny);
    ctx.strokeStyle = 'rgba(10,132,255,0.45)';
    ctx.lineWidth = 2;
    ctx.setLineDash([]);
    ctx.stroke();
  }

  // Dashed loop-back line
  if (navStatus.loop && waypoints.length > 1) {
    const {px: fx, py: fy} = w2c(waypoints[0].x, waypoints[0].y);
    const {px: lx, py: ly} = w2c(waypoints[waypoints.length-1].x, waypoints[waypoints.length-1].y);
    ctx.beginPath();
    ctx.moveTo(lx, ly); ctx.lineTo(fx, fy);
    ctx.strokeStyle = 'rgba(10,132,255,0.2)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Waypoint circles
  waypoints.forEach((wp, i) => {
    const {px, py} = w2c(wp.x, wp.y);
    const active   = navStatus.navigating     && navStatus.wp_idx === i;
    const isHome   = navStatus.returning_home && i === 0;
    const r        = (active || isHome) ? 11 : 9;

    // Glow for active
    if (active || isHome) {
      ctx.beginPath();
      ctx.arc(px, py, r + 5, 0, Math.PI * 2);
      ctx.fillStyle = active ? 'rgba(48,209,88,0.15)' : 'rgba(255,159,10,0.15)';
      ctx.fill();
    }

    ctx.beginPath();
    ctx.arc(px, py, r, 0, Math.PI * 2);
    ctx.fillStyle = isHome   ? '#FF9F0A' :
                    active   ? '#30D158' :
                    i === 0  ? '#0A84FF' :
                               '#30D158';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.8)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 10px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(i + 1, px, py);
  });

  // Robot arrow
  if (robotPose) {
    const {px, py} = w2c(robotPose.x, robotPose.y);
    ctx.save();
    ctx.translate(px, py);
    ctx.rotate(-robotPose.theta);

    // Shadow
    ctx.shadowColor = 'rgba(10,132,255,0.5)';
    ctx.shadowBlur  = 10;

    ctx.beginPath();
    ctx.moveTo(15, 0);
    ctx.lineTo(-7, -6);
    ctx.lineTo(-3, 0);
    ctx.lineTo(-7,  6);
    ctx.closePath();
    ctx.fillStyle   = '#0A84FF';
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth   = 1.5;
    ctx.fill();
    ctx.stroke();

    ctx.restore();
  }

  // Initial pose arrow (orange)
  if (initPose) {
    const {px, py} = w2c(initPose.x, initPose.y);
    ctx.save();
    ctx.translate(px, py);
    ctx.rotate(-initPose.theta);
    ctx.shadowColor = 'rgba(255,159,10,0.5)';
    ctx.shadowBlur  = 10;
    ctx.beginPath();
    ctx.moveTo(15, 0); ctx.lineTo(-7, -6); ctx.lineTo(-3, 0); ctx.lineTo(-7, 6);
    ctx.closePath();
    ctx.fillStyle   = '#FF9F0A';
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth   = 1.5;
    ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  // Pose drag preview
  if (poseMode && poseDrag) {
    const {px, py, ex, ey} = poseDrag;
    // Circle at click point
    ctx.beginPath(); ctx.arc(px, py, 9, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,159,10,0.25)'; ctx.fill();
    ctx.strokeStyle = '#FF9F0A'; ctx.lineWidth = 2; ctx.stroke();
    // Drag line + arrowhead
    const dist = Math.hypot(ex - px, ey - py);
    if (dist > 8) {
      const angle = Math.atan2(ey - py, ex - px);
      ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(ex, ey);
      ctx.strokeStyle = '#FF9F0A'; ctx.lineWidth = 2;
      ctx.setLineDash([5, 4]); ctx.stroke(); ctx.setLineDash([]);
      ctx.save();
      ctx.translate(ex, ey); ctx.rotate(angle);
      ctx.beginPath(); ctx.moveTo(8,0); ctx.lineTo(-5,-3); ctx.lineTo(-5,3);
      ctx.closePath(); ctx.fillStyle = '#FF9F0A'; ctx.fill();
      ctx.restore();
    }
  }
}

// ── Canvas click → add waypoint ───────────────────────────────────────────────
canvas.addEventListener('click', e => {
  if (_justSetPose) { _justSetPose = false; return; }
  if (poseMode)  return;
  if (!mapInfo) return;
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width  / rect.width;
  const sy = canvas.height / rect.height;
  const px = (e.clientX - rect.left) * sx;
  const py = (e.clientY - rect.top)  * sy;
  waypoints.push(c2w(px, py));
  saveWaypoints();
  renderList();
  draw();
});

// ── Waypoint list ─────────────────────────────────────────────────────────────
function renderList() {
  const el        = document.getElementById('wp-list');
  const countEl   = document.getElementById('wp-count');
  const emptyEl   = document.getElementById('wp-empty');

  if (waypoints.length === 0) {
    el.innerHTML = '';
    el.appendChild(emptyEl || Object.assign(document.createElement('div'), {
      id: 'wp-empty', className: 'wp-empty', textContent: 'Tap map to add waypoints'
    }));
    countEl.style.display = 'none';
    return;
  }

  countEl.textContent  = waypoints.length;
  countEl.style.display = 'inline-flex';

  el.innerHTML = '';
  waypoints.forEach((wp, i) => {
    const active   = navStatus.navigating     && navStatus.wp_idx === i;
    const isHome   = navStatus.returning_home && i === 0;

    const row  = document.createElement('div');
    row.className = 'wp-item' + (active ? ' active' : '') + (isHome ? ' home-active' : '');

    const num  = document.createElement('div');
    num.className = 'wp-num' + (i === 0 ? ' home' : '');
    num.textContent = i + 1;

    const info = document.createElement('div');
    info.className = 'wp-info';
    info.innerHTML  = `<span class="wp-label">${i === 0 ? 'Home' : 'Point ' + (i + 1)}</span>
                       <span class="wp-coord">${wp.x},&thinsp;${wp.y}</span>`;

    const del  = document.createElement('button');
    del.className   = 'wp-del';
    del.textContent = '\u00d7';
    del.onclick = () => { waypoints.splice(i, 1); saveWaypoints(); renderList(); draw(); };

    row.appendChild(num);
    row.appendChild(info);
    row.appendChild(del);
    el.appendChild(row);
  });
}

// ── Status update ─────────────────────────────────────────────────────────────
function updateStatus(d) {
  const badge    = document.getElementById('status-badge');
  const text     = document.getElementById('status-text');
  const progress = document.getElementById('nav-progress');
  const fill     = document.getElementById('progress-fill');
  const label    = document.getElementById('progress-label');

  badge.className = 'status-badge';

  if (d.returning_home) {
    badge.classList.add('returning');
    text.textContent = 'Returning Home';
    progress.style.display = 'none';
  } else if (d.navigating) {
    badge.classList.add('navigating');
    text.textContent = 'Navigating';
    progress.style.display = 'flex';
    const pct = d.wp_total ? (d.wp_idx / d.wp_total * 100) : 0;
    fill.style.width   = pct + '%';
    label.textContent  = `WP ${d.wp_idx + 1} of ${d.wp_total}${d.loop ? '  ·  Loop' : ''}`;
  } else {
    badge.classList.add('idle');
    text.textContent = 'Idle';
    progress.style.display = 'none';
  }
}

// ── Pose mode: mousedown / mousemove / mouseup on canvas ─────────────────────
function canvasPx(e) {
  const rect = canvas.getBoundingClientRect();
  return {
    px: (e.clientX - rect.left) * (canvas.width  / rect.width),
    py: (e.clientY - rect.top)  * (canvas.height / rect.height)
  };
}

canvas.addEventListener('mousedown', e => {
  if (!poseMode || !mapInfo) return;
  const {px, py} = canvasPx(e);
  poseDrag = {px, py, ex: px, ey: py};
  e.preventDefault();
});

canvas.addEventListener('mousemove', e => {
  if (!poseMode || !poseDrag) return;
  const {px, py} = canvasPx(e);
  poseDrag.ex = px; poseDrag.ey = py;
  draw();
});

canvas.addEventListener('mouseup', e => {
  if (!poseMode || !poseDrag) return;
  const {px, py, ex, ey} = poseDrag;
  const world = c2w(px, py);
  const dx = ex - px, dy = ey - py;
  const theta = Math.hypot(dx, dy) > 8 ? -Math.atan2(dy, dx) : 0;
  poseDrag = null;
  poseMode = false;
  _justSetPose = true;
  document.getElementById('btn-pose').classList.remove('active');
  canvas.style.cursor = 'crosshair';
  initPose = {x: world.x, y: world.y, theta};
  fetch('/api/initial-pose', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({x: world.x, y: world.y, theta})
  });
  draw();
});

// ── Button controls ───────────────────────────────────────────────────────────
document.getElementById('btn-go').onclick = () => {
  if (!waypoints.length) { alert('Add at least one waypoint first'); return; }
  const loop = document.getElementById('chk-loop').checked;
  fetch('/api/go', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({waypoints, loop})
  });
};
document.getElementById('btn-stop').onclick  = () => fetch('/api/stop', {method: 'POST'});
document.getElementById('btn-clear').onclick = () => {
  waypoints = [];
  saveWaypoints();
  renderList();
  draw();
};

document.getElementById('chk-loop').addEventListener('change', () => {
  navStatus.loop = document.getElementById('chk-loop').checked;
  draw();
});

document.getElementById('btn-pose').onclick = () => {
  poseMode = !poseMode;
  poseDrag = null;
  document.getElementById('btn-pose').classList.toggle('active', poseMode);
  canvas.style.cursor = poseMode ? 'cell' : 'crosshair';
};

// ── Map init helper ───────────────────────────────────────────────────────────
let mapInited = false;
function initCanvas(img) {
  canvas.width  = img.width;
  canvas.height = img.height;
  const maxW = document.getElementById('map-wrap').clientWidth  - 16;
  const maxH = document.getElementById('map-wrap').clientHeight - 16;
  const sc   = Math.min(maxW / img.width, maxH / img.height);   // allow scale > 1
  canvas.style.width  = Math.round(img.width  * sc) + 'px';
  canvas.style.height = Math.round(img.height * sc) + 'px';
}

// ── Load static map on first open ────────────────────────────────────────────
fetch('/api/map').then(r => r.json()).then(d => {
  if (!d.ok) {
    canvas.style.display = 'none';
    const noMap = document.getElementById('no-map');
    noMap.style.display = 'flex';
    return;
  }
  mapInfo = d.info;
  const img = new Image();
  img.onload = () => {
    mapImg = img;
    initCanvas(img);
    mapInited = true;
    renderList();
    draw();
  };
  img.src = 'data:image/png;base64,' + d.image;
});

// ── Poll live map every 2 s ───────────────────────────────────────────────────
setInterval(() => {
  fetch('/api/map-live').then(r => r.json()).then(d => {
    if (!d.ok) return;
    mapInfo = d.info;
    const img = new Image();
    img.onload = () => {
      if (!mapInited) { initCanvas(img); mapInited = true; }
      mapImg = img;
      draw();
    };
    img.src = 'data:image/png;base64,' + d.image;
  });
}, 2000);

// ── Poll robot pose every 400 ms ──────────────────────────────────────────────
setInterval(() => {
  fetch('/api/pose').then(r => r.json()).then(d => {
    robotPose = d.ok ? d : null;
    const dot = document.getElementById('conn-dot');
    dot.className = 'conn-indicator ' + (d.ok ? 'online' : 'offline');
    draw();
  });
}, 400);

// ── Poll nav status every 800 ms ─────────────────────────────────────────────
setInterval(() => {
  fetch('/api/status').then(r => r.json()).then(d => {
    navStatus = {...d, loop: document.getElementById('chk-loop').checked};
    updateStatus(d);
    renderList();
    draw();
  });
}, 800);

// ── Theme toggle ──────────────────────────────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.dataset.theme = saved;
  updateThemeIcon(saved);
})();

function updateThemeIcon(theme) {
  const btn = document.getElementById('btn-theme');
  if (!btn) return;
  // moon = go to dark, sun = go to light
  btn.innerHTML = theme === 'dark'
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/>
       </svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
       </svg>`;
}

document.getElementById('btn-theme').addEventListener('click', () => {
  const current = document.documentElement.dataset.theme || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
  updateThemeIcon(next);
});

// ── Initial render (waypoints from localStorage) ──────────────────────────────
renderList();
