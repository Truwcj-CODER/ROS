#!/usr/bin/env python3
"""
Web dashboard for robot waypoint navigation.

Usage:
  pip3 install flask
  python3 dashboard.py                      # uses ~/demo_map.yaml by default
  python3 dashboard.py --map /path/to.yaml  # custom map
  python3 dashboard.py --port 5000          # custom port

Open http://localhost:5000 in browser.
Requires: slam.launch.py (sim:=true) running first.
"""

import sys, os, math, threading, base64, io, argparse
import numpy as np
import yaml
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from tf2_ros import Buffer, TransformListener
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped

try:
    from PIL import Image
except ImportError:
    print('Error: Pillow not installed. Run: pip3 install Pillow')
    sys.exit(1)

try:
    from flask import Flask, jsonify, request
except ImportError:
    print('Error: Flask not installed. Run: pip3 install flask')
    sys.exit(1)


# ── Map loader ────────────────────────────────────────────────────────────────

def load_map(yaml_path):
    """Load nav2 map yaml+pgm. Returns (base64_png, info_dict) or (None, None)."""
    try:
        yaml_path = os.path.expanduser(yaml_path)
        with open(yaml_path) as f:
            meta = yaml.safe_load(f)
        pgm = meta.get('image', '')
        if not os.path.isabs(pgm):
            pgm = os.path.join(os.path.dirname(yaml_path), pgm)
        img = Image.open(pgm).convert('RGB')
        w, h = img.size
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        b64 = base64.b64encode(buf.getvalue()).decode()
        origin = meta.get('origin', [0.0, 0.0, 0.0])
        return b64, {
            'origin_x':  float(origin[0]),
            'origin_y':  float(origin[1]),
            'resolution': float(meta.get('resolution', 0.05)),
            'width': w, 'height': h,
        }
    except Exception as e:
        print(f'[dashboard] map load error: {e}')
        return None, None


# ── ROS2 nav node ─────────────────────────────────────────────────────────────

class NavNode(Node):
    def __init__(self):
        super().__init__('dashboard_nav')
        self._nav    = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.tf_buf  = Buffer()
        self._tfl    = TransformListener(self.tf_buf, self)
        self._lock      = threading.Lock()
        self._map_msg   = None
        self._map_dirty = False
        # Static map fallback (transient local — receives last published map on subscribe)
        map_qos = QoSProfile(depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, 'map', self._map_cb, map_qos)
        # Global costmap — real-time obstacles from live /scan (volatile, updates ~1Hz)
        costmap_qos = QoSProfile(depth=1,
            durability=QoSDurabilityPolicy.VOLATILE,
            reliability=QoSReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, '/global_costmap/costmap',
                                 self._map_cb, costmap_qos)
        self._reset()

    def _reset(self):
        self._waypoints      = []
        self._loop           = False
        self._wp_idx         = 0
        self._navigating     = False
        self._returning_home = False
        self._goal_handle    = None

    def _map_cb(self, msg):
        with self._lock:
            self._map_msg   = msg
            self._map_dirty = True

    def get_live_map(self):
        with self._lock:
            msg = self._map_msg
        if msg is None:
            return None, None
        w = msg.info.width
        h = msg.info.height
        # Nav2 publishes OccupancyGrid in 0-100 scale: 0=free, 100=occupied, 255=unknown
        data = np.array(msg.data, dtype=np.int8).reshape(h, w).astype(np.uint8)
        rgb = np.full((h, w, 3), 128, dtype=np.uint8)   # default = gray (unknown)
        rgb[data == 0]                  = [220, 220, 220]  # free
        rgb[(data > 0) & (data < 100)]  = [220, 220, 220]  # inflation → treat as free
        rgb[data == 100]                = [30,  30,  30 ]  # occupied  → black
        rgb[data == 255]                = [128, 128, 128]  # no info   → gray
        rgb = rgb[::-1]                                   # flip Y (map Y=up)
        img = Image.fromarray(rgb, 'RGB')
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        b64  = base64.b64encode(buf.getvalue()).decode()
        info = dict(
            origin_x   = msg.info.origin.position.x,
            origin_y   = msg.info.origin.position.y,
            resolution = msg.info.resolution,
            width=w, height=h,
        )
        return b64, info

    # ── public (called from Flask thread) ────────────────────────────────────

    def start(self, waypoints, loop):
        with self._lock:
            if not waypoints:
                return
            self._waypoints  = list(waypoints)
            self._loop       = loop
            self._wp_idx     = 0
            self._navigating = True
            self._goal_handle = None
        self._send_current()

    def cancel(self):
        with self._lock:
            if self._returning_home:
                # Second Stop press → truly stop
                self._returning_home = False
                gh = self._goal_handle
                self._goal_handle = None
                if gh:
                    gh.cancel_goal_async()
                return
            was_navigating = self._navigating
            self._navigating = False
            gh = self._goal_handle
            self._goal_handle = None
            home_wp = self._waypoints[0] if (self._waypoints and was_navigating) else None
        if gh:
            gh.cancel_goal_async()
        if home_wp:
            threading.Timer(0.5, self._go_home, args=[home_wp]).start()

    def status(self):
        with self._lock:
            return dict(
                navigating     = self._navigating,
                returning_home = self._returning_home,
                wp_idx         = self._wp_idx,
                wp_total       = len(self._waypoints),
                loop           = self._loop,
            )

    def get_pose(self):
        try:
            tf  = self.tf_buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            t   = tf.transform.translation
            r   = tf.transform.rotation
            yaw = math.atan2(2*(r.w*r.z + r.x*r.y), 1 - 2*(r.y*r.y + r.z*r.z))
            return dict(x=t.x, y=t.y, theta=yaw, ok=True)
        except Exception:
            return dict(ok=False)

    # ── internal (called from rclpy thread) ──────────────────────────────────

    def _send_current(self):
        with self._lock:
            if not self._navigating or not self._waypoints:
                return
            wp = self._waypoints[self._wp_idx]

        if not self._nav.wait_for_server(timeout_sec=3.0):
            self.get_logger().warn('Nav2 not ready')
            return

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp    = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(wp['x'])
        goal.pose.pose.position.y = float(wp['y'])
        goal.pose.pose.orientation.w = 1.0

        self.get_logger().info(f'→ waypoint {self._wp_idx+1} ({wp["x"]}, {wp["y"]})')
        fut = self._nav.send_goal_async(goal)
        fut.add_done_callback(self._on_goal_resp)

    def _on_goal_resp(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn('Goal rejected')
            self._advance()
            return
        with self._lock:
            self._goal_handle = handle
        handle.get_result_async().add_done_callback(self._on_goal_result)

    def _on_goal_result(self, future):
        status = future.result().status
        with self._lock:
            if not self._navigating:
                return
            idx = self._wp_idx
        msg = 'reached' if status == 4 else f'status={status}'
        self.get_logger().info(f'Waypoint {idx+1} {msg}')
        self._advance()

    def _advance(self):
        with self._lock:
            if not self._navigating:
                return
            self._wp_idx += 1
            if self._wp_idx >= len(self._waypoints):
                if self._loop:
                    self._wp_idx = 0
                else:
                    self._navigating = False
                    self.get_logger().info('All waypoints done.')
                    return
        self._send_current()

    def _go_home(self, wp):
        if not self._nav.wait_for_server(timeout_sec=3.0):
            return
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id    = 'map'
        goal.pose.header.stamp       = self.get_clock().now().to_msg()
        goal.pose.pose.position.x    = wp['x']
        goal.pose.pose.position.y    = wp['y']
        goal.pose.pose.orientation.w = 1.0
        with self._lock:
            self._returning_home = True
        self.get_logger().info(f'Returning to home ({wp["x"]}, {wp["y"]})')
        fut = self._nav.send_goal_async(goal)
        fut.add_done_callback(self._on_home_resp)

    def _on_home_resp(self, future):
        handle = future.result()
        if not handle.accepted:
            with self._lock:
                self._returning_home = False
            return
        with self._lock:
            self._goal_handle = handle
        handle.get_result_async().add_done_callback(self._on_home_result)

    def _on_home_result(self, future):
        with self._lock:
            self._returning_home = False
            self._goal_handle    = None
        self.get_logger().info('Home reached.')


# ── HTML / JS frontend ────────────────────────────────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Robot Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;display:flex;height:100vh;background:#12151e;color:#e0e0e0}
#sidebar{width:270px;min-width:270px;padding:16px;background:#1a1f2e;display:flex;flex-direction:column;gap:10px;overflow-y:auto}
h1{font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#58a6ff;padding-bottom:8px;border-bottom:1px solid #2d3248}
#map-wrap{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#0d1117}
canvas{cursor:crosshair}
.btn{width:100%;padding:9px;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;transition:opacity .15s}
.btn:hover{opacity:.85}
#btn-go{background:#238636;color:#fff}
#btn-stop{background:#b91c1c;color:#fff}
#btn-clear{background:#30363d;color:#ccc}
.section-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:#8b949e;margin-bottom:4px}
#status-box{background:#0d1117;border-radius:6px;padding:8px 10px;font-size:12px;color:#8b949e}
#wp-list{display:flex;flex-direction:column;gap:4px;max-height:240px;overflow-y:auto}
.wp-row{display:flex;align-items:center;gap:6px;background:#21262d;border-radius:5px;padding:5px 8px;font-size:12px}
.wp-num{background:#388bfd;color:#fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0}
.wp-coords{flex:1;color:#ccc}
.wp-del{background:none;border:none;color:#f85149;cursor:pointer;font-size:16px;padding:0 2px;line-height:1;width:auto}
label{display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer}
input[type=checkbox]{width:16px;height:16px;cursor:pointer;accent-color:#388bfd}
#hint{font-size:11px;color:#484f58;line-height:1.5;margin-top:auto}
#no-map{color:#484f58;font-size:13px;text-align:center}
</style>
</head>
<body>
<div id="sidebar">
  <h1>🤖 Robot Dashboard</h1>

  <div>
    <div class="section-title">Status</div>
    <div id="status-box">Loading…</div>
  </div>

  <div>
    <div class="section-title">Waypoints <span id="wp-count" style="color:#58a6ff"></span></div>
    <div id="wp-list"></div>
  </div>

  <label><input type="checkbox" id="chk-loop"> Loop patrol</label>

  <button class="btn" id="btn-go">▶ Go</button>
  <button class="btn" id="btn-stop">■ Stop</button>
  <button class="btn" id="btn-clear">✕ Clear waypoints</button>

  <div id="hint">
    • Click on map to add waypoint<br>
    • × to remove a waypoint<br>
    • Robot shown as blue arrow
  </div>
</div>

<div id="map-wrap">
  <canvas id="c"></canvas>
  <div id="no-map" style="display:none">No map loaded.<br>Check --map argument.</div>
</div>

<script>
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
let mapImg = null, mapInfo = null;
let waypoints = [];   // [{x, y}] world coords
let robotPose = null;
let navStatus = {navigating:false};

// ── Load map ──────────────────────────────────────────────────────────────────
fetch('/api/map').then(r=>r.json()).then(d=>{
  if(!d.ok){
    document.getElementById('no-map').style.display='block';
    canvas.style.display='none';
    return;
  }
  mapInfo = d.info;
  const img = new Image();
  img.onload = ()=>{
    mapImg = img;
    // Scale canvas to fit window
    const maxW = document.getElementById('map-wrap').clientWidth  - 20;
    const maxH = document.getElementById('map-wrap').clientHeight - 20;
    const scale = Math.min(maxW/img.width, maxH/img.height, 1);
    canvas.width  = img.width;
    canvas.height = img.height;
    canvas.style.width  = Math.round(img.width  * scale) + 'px';
    canvas.style.height = Math.round(img.height * scale) + 'px';
    draw();
  };
  img.src = 'data:image/png;base64,' + d.image;
});

// ── Coordinate conversion ─────────────────────────────────────────────────────
// PGM row 0 = top of image = high Y (north).
// Canvas pixel (px, py): px,py in image pixels.
// world_x = origin_x + px * res
// world_y = origin_y + (height - 1 - py) * res   ← Y flipped
function w2c(wx, wy){
  if(!mapInfo) return {px:0,py:0};
  return {
    px: (wx - mapInfo.origin_x) / mapInfo.resolution,
    py: mapInfo.height - 1 - (wy - mapInfo.origin_y) / mapInfo.resolution
  };
}
function c2w(px, py){
  if(!mapInfo) return {x:0,y:0};
  return {
    x: Math.round((mapInfo.origin_x + px * mapInfo.resolution)*100)/100,
    y: Math.round((mapInfo.origin_y + (mapInfo.height-1-py)*mapInfo.resolution)*100)/100
  };
}

// ── Draw ──────────────────────────────────────────────────────────────────────
function draw(){
  if(!mapImg) return;
  ctx.drawImage(mapImg, 0, 0);

  // Waypoint markers
  waypoints.forEach((wp, i)=>{
    const {px,py} = w2c(wp.x, wp.y);
    // Line to next waypoint
    if(i < waypoints.length-1){
      const {px:nx,py:ny} = w2c(waypoints[i+1].x, waypoints[i+1].y);
      ctx.beginPath();
      ctx.moveTo(px,py); ctx.lineTo(nx,ny);
      ctx.strokeStyle='rgba(88,166,255,0.5)';
      ctx.lineWidth=2; ctx.stroke();
    }
    // Circle
    const active   = navStatus.navigating     && navStatus.wp_idx === i;
    const isHome   = navStatus.returning_home && i === 0;
    ctx.beginPath();
    ctx.arc(px,py,(active||isHome)?10:8,0,Math.PI*2);
    ctx.fillStyle = isHome   ? 'rgba(255,100,0,0.9)'  :
                    active   ? 'rgba(255,200,0,0.9)'  :
                    i === 0  ? 'rgba(88,166,255,0.85)' :
                               'rgba(35,134,54,0.85)';
    ctx.fill();
    ctx.strokeStyle='white'; ctx.lineWidth=2; ctx.stroke();
    ctx.fillStyle='white';
    ctx.font='bold 10px sans-serif';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(i+1, px, py);
  });

  // Loop line
  if(navStatus.loop && waypoints.length > 1){
    const {px:fx,py:fy} = w2c(waypoints[0].x, waypoints[0].y);
    const {px:lx,py:ly} = w2c(waypoints[waypoints.length-1].x, waypoints[waypoints.length-1].y);
    ctx.beginPath();
    ctx.moveTo(lx,ly); ctx.lineTo(fx,fy);
    ctx.strokeStyle='rgba(88,166,255,0.25)';
    ctx.lineWidth=1.5; ctx.setLineDash([5,5]); ctx.stroke();
    ctx.setLineDash([]);
  }

  // Robot arrow
  if(robotPose){
    const {px,py} = w2c(robotPose.x, robotPose.y);
    const th = robotPose.theta;
    ctx.save();
    ctx.translate(px,py);
    ctx.rotate(-th);  // negate: canvas Y is downward
    ctx.beginPath();
    ctx.moveTo(14,0); ctx.lineTo(-7,-6); ctx.lineTo(-4,0); ctx.lineTo(-7,6);
    ctx.closePath();
    ctx.fillStyle='#58a6ff'; ctx.strokeStyle='white';
    ctx.lineWidth=1.5; ctx.fill(); ctx.stroke();
    ctx.restore();
  }
}

// ── Canvas click → add waypoint ───────────────────────────────────────────────
canvas.addEventListener('click', e=>{
  if(!mapInfo) return;
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width  / rect.width;
  const sy = canvas.height / rect.height;
  const px = (e.clientX - rect.left)*sx;
  const py = (e.clientY - rect.top )*sy;
  waypoints.push(c2w(px,py));
  renderList(); draw();
});

// ── Waypoint list ─────────────────────────────────────────────────────────────
function renderList(){
  document.getElementById('wp-count').textContent = waypoints.length ? `(${waypoints.length})` : '';
  const el = document.getElementById('wp-list');
  el.innerHTML = '';
  waypoints.forEach((wp,i)=>{
    const row = document.createElement('div');
    row.className = 'wp-row';
    row.innerHTML = `<div class="wp-num">${i+1}</div>
      <div class="wp-coords">(${wp.x}, ${wp.y})</div>`;
    const del = document.createElement('button');
    del.className='wp-del'; del.textContent='×';
    del.onclick=()=>{ waypoints.splice(i,1); renderList(); draw(); };
    row.appendChild(del);
    el.appendChild(row);
  });
}

// ── Controls ──────────────────────────────────────────────────────────────────
document.getElementById('btn-go').onclick = ()=>{
  if(!waypoints.length){ alert('Add at least one waypoint first'); return; }
  const loop = document.getElementById('chk-loop').checked;
  fetch('/api/go',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({waypoints, loop})});
};
document.getElementById('btn-stop').onclick = ()=>{ fetch('/api/stop',{method:'POST'}); };
document.getElementById('btn-clear').onclick = ()=>{ waypoints=[]; renderList(); draw(); };

document.getElementById('chk-loop').addEventListener('change', ()=>{
  navStatus.loop = document.getElementById('chk-loop').checked;
  draw();
});

// ── Poll live map every 2 s ───────────────────────────────────────────────────
let mapInited = false;
setInterval(()=>{
  fetch('/api/map-live').then(r=>r.json()).then(d=>{
    if(!d.ok) return;
    mapInfo = d.info;
    const img = new Image();
    img.onload = ()=>{
      if(!mapInited){
        canvas.width  = img.width;
        canvas.height = img.height;
        const maxW = document.getElementById('map-wrap').clientWidth  - 20;
        const maxH = document.getElementById('map-wrap').clientHeight - 20;
        const sc   = Math.min(maxW/img.width, maxH/img.height, 1);
        canvas.style.width  = Math.round(img.width *sc)+'px';
        canvas.style.height = Math.round(img.height*sc)+'px';
        mapInited = true;
      }
      mapImg = img;
      draw();
    };
    img.src = 'data:image/png;base64,'+d.image;
  });
}, 2000);

// ── Polling ───────────────────────────────────────────────────────────────────
setInterval(()=>{
  fetch('/api/pose').then(r=>r.json()).then(d=>{ robotPose=d.ok?d:null; draw(); });
}, 400);

setInterval(()=>{
  fetch('/api/status').then(r=>r.json()).then(d=>{
    navStatus = {...d, loop: document.getElementById('chk-loop').checked};
    const el = document.getElementById('status-box');
    el.textContent = d.returning_home
      ? '⟵ Returning to base (WP 1)…  [Stop again to cancel]'
      : d.navigating
        ? `Navigating → waypoint ${d.wp_idx+1} / ${d.wp_total}${d.loop?' (loop)':''}`
        : 'Idle';
    draw();
  });
}, 800);
</script>
</body>
</html>
"""

# ── Flask app ─────────────────────────────────────────────────────────────────

def make_app(node, map_b64, map_info):
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app = Flask(__name__)

    @app.route('/')
    def index():
        return _HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}

    @app.route('/api/map')
    def api_map():
        if map_b64 is None:
            return jsonify(ok=False)
        return jsonify(ok=True, image=map_b64, info=map_info)

    @app.route('/api/map-live')
    def api_map_live():
        b64, info = node.get_live_map()
        if b64 is None:
            return jsonify(ok=False)
        return jsonify(ok=True, image=b64, info=info)

    @app.route('/api/pose')
    def api_pose():
        return jsonify(node.get_pose())

    @app.route('/api/status')
    def api_status():
        return jsonify(node.status())

    @app.route('/api/go', methods=['POST'])
    def api_go():
        data = request.get_json(force=True)
        node.start(data.get('waypoints', []), bool(data.get('loop', False)))
        return jsonify(ok=True)

    @app.route('/api/stop', methods=['POST'])
    def api_stop():
        node.cancel()
        return jsonify(ok=True)

    return app


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Robot web dashboard')
    parser.add_argument('--map',  default='~/demo_map.yaml', help='Path to map YAML')
    parser.add_argument('--port', type=int, default=5000,    help='Web server port')
    args = parser.parse_args()

    map_b64, map_info = load_map(args.map)
    if map_b64 is None:
        print(f'[dashboard] Warning: could not load map from {args.map}')

    rclpy.init()
    node = NavNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    ros_thread = threading.Thread(target=executor.spin, daemon=True)
    ros_thread.start()

    app = make_app(node, map_b64, map_info)
    print(f'[dashboard] http://localhost:{args.port}')
    app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
