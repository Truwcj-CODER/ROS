"""
ROS2 navigation node for the dashboard.
Handles map subscription, robot pose, and Nav2 goal sending.
"""

import math
import threading
import base64
import io

import numpy as np
from PIL import Image

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
from tf2_ros import Buffer, TransformListener
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped


# ── Map file loader ───────────────────────────────────────────────────────────

def load_map_file(yaml_path: str):
    """Load nav2 map yaml+pgm. Returns (base64_png, info_dict) or (None, None)."""
    import os, yaml
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
            'origin_x':   float(origin[0]),
            'origin_y':   float(origin[1]),
            'resolution': float(meta.get('resolution', 0.05)),
            'width': w, 'height': h,
        }
    except Exception as e:
        print(f'[ros_node] map load error: {e}')
        return None, None


# ── ROS2 node ─────────────────────────────────────────────────────────────────

class NavNode(Node):
    def __init__(self):
        super().__init__('dashboard_nav')
        self._nav           = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._init_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.tf    = Buffer()
        self._tfl  = TransformListener(self.tf, self)
        self._lock = threading.Lock()

        # Map subscriptions
        map_qos = QoSProfile(depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE)
        costmap_qos = QoSProfile(depth=1,
            durability=QoSDurabilityPolicy.VOLATILE,
            reliability=QoSReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, 'map',
                                 self._map_cb, map_qos)
        self.create_subscription(OccupancyGrid, '/global_costmap/costmap',
                                 self._map_cb, costmap_qos)

        self._map_msg = None
        self._dock    = None   # set by set_initial_pose(); used as return-home target
        self._reset()

    # ── State ─────────────────────────────────────────────────────────────────

    def _reset(self):
        self._waypoints      = []
        self._loop           = False
        self._wp_idx         = 0
        self._navigating     = False
        self._returning_home = False
        self._goal_handle    = None

    # ── Map ───────────────────────────────────────────────────────────────────

    def _map_cb(self, msg: OccupancyGrid):
        with self._lock:
            self._map_msg = msg

    def get_live_map(self):
        with self._lock:
            msg = self._map_msg
        if msg is None:
            return None, None

        w = msg.info.width
        h = msg.info.height
        # Nav2 OccupancyGrid: 0=free, 1-99=inflation, 100=occupied, 255(-1)=unknown
        data = np.array(msg.data, dtype=np.int8).reshape(h, w).astype(np.uint8)
        rgb = np.full((h, w, 3), 128, dtype=np.uint8)    # unknown = gray
        rgb[data == 0]                 = [220, 220, 220]  # free
        rgb[(data > 0) & (data < 100)] = [220, 220, 220]  # inflation → free
        rgb[data == 100]               = [30,  30,  30 ]  # occupied
        rgb[data == 255]               = [128, 128, 128]  # no info
        rgb = rgb[::-1]                                    # flip Y

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

    # ── Pose ──────────────────────────────────────────────────────────────────

    def get_pose(self):
        try:
            tf  = self.tf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            t   = tf.transform.translation
            r   = tf.transform.rotation
            yaw = math.atan2(2*(r.w*r.z + r.x*r.y), 1 - 2*(r.y*r.y + r.z*r.z))
            return dict(x=t.x, y=t.y, theta=yaw, ok=True)
        except Exception:
            return dict(ok=False)

    def set_initial_pose(self, x: float, y: float, theta: float):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.pose.pose.position.x    = float(x)
        msg.pose.pose.position.y    = float(y)
        msg.pose.pose.orientation.z = math.sin(theta / 2.0)
        msg.pose.pose.orientation.w = math.cos(theta / 2.0)
        # Standard AMCL covariance (x, y, yaw)
        msg.pose.covariance[0]  = 0.25    # x
        msg.pose.covariance[7]  = 0.25    # y
        msg.pose.covariance[35] = 0.0685  # yaw (~15 deg)
        self._init_pose_pub.publish(msg)
        self._dock = {'x': x, 'y': y, 'theta': theta}
        self.get_logger().info(f'Initial pose / dock set: ({x:.2f}, {y:.2f}, θ={math.degrees(theta):.1f}°)')

    # ── Navigation control (called from FastAPI thread) ───────────────────────

    def start(self, waypoints: list, loop: bool):
        with self._lock:
            if not waypoints:
                return
            self._waypoints      = list(waypoints)
            self._loop           = loop
            self._wp_idx         = 0
            self._navigating     = True
            self._returning_home = False
            self._goal_handle    = None
        self._send_current()

    def cancel(self):
        with self._lock:
            if self._returning_home:
                self._returning_home = False
                gh = self._goal_handle
                self._goal_handle = None
                if gh:
                    gh.cancel_goal_async()
                return
            was_nav   = self._navigating
            self._navigating = False
            gh        = self._goal_handle
            self._goal_handle = None
            home_wp   = self._dock or (self._waypoints[0] if (self._waypoints and was_nav) else None)
        if gh:
            gh.cancel_goal_async()
        if home_wp:
            import threading as _t
            _t.Timer(0.5, self._go_home, args=[home_wp]).start()

    def status(self):
        with self._lock:
            return dict(
                navigating     = self._navigating,
                returning_home = self._returning_home,
                wp_idx         = self._wp_idx,
                wp_total       = len(self._waypoints),
                loop           = self._loop,
            )

    # ── Internal navigation ───────────────────────────────────────────────────

    def _send_goal(self, x: float, y: float, theta: float = 0.0):
        if not self._nav.wait_for_server(timeout_sec=3.0):
            self.get_logger().warn('Nav2 not ready')
            return None
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id    = 'map'
        goal.pose.header.stamp       = self.get_clock().now().to_msg()
        goal.pose.pose.position.x    = float(x)
        goal.pose.pose.position.y    = float(y)
        goal.pose.pose.orientation.z = math.sin(float(theta) / 2.0)
        goal.pose.pose.orientation.w = math.cos(float(theta) / 2.0)
        return self._nav.send_goal_async(goal)

    def _send_current(self):
        with self._lock:
            if not self._navigating or not self._waypoints:
                return
            wp = self._waypoints[self._wp_idx]
        self.get_logger().info(f'→ WP {self._wp_idx+1} ({wp["x"]:.2f}, {wp["y"]:.2f})')
        fut = self._send_goal(wp['x'], wp['y'])
        if fut:
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
        self.get_logger().info(f'WP {self._wp_idx+1} {"reached" if status==4 else f"status={status}"}')
        self._advance()

    def _advance(self):
        home_wp = None
        with self._lock:
            if not self._navigating:
                return
            self._wp_idx += 1
            if self._wp_idx >= len(self._waypoints):
                if self._loop:
                    self._wp_idx = 0
                else:
                    self._navigating = False
                    home_wp = self._dock or (self._waypoints[0] if self._waypoints else None)
                    self.get_logger().info('All waypoints done — returning home.')
        if home_wp:
            import threading as _t
            _t.Timer(0.3, self._go_home, args=[home_wp]).start()
            return
        self._send_current()

    def _go_home(self, wp):
        with self._lock:
            self._returning_home = True
        self.get_logger().info(f'Returning home ({wp["x"]:.2f}, {wp["y"]:.2f})')
        fut = self._send_goal(wp['x'], wp['y'], wp.get('theta', 0.0))
        if fut:
            fut.add_done_callback(self._on_home_resp)
        else:
            with self._lock:
                self._returning_home = False

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
