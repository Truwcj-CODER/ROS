#!/usr/bin/env python3
"""
Frontier-based autonomous exploration.

Reads /map (OccupancyGrid from SLAM), finds unexplored frontier cells,
and navigates to them via Nav2 NavigateToPose action until the map is complete.

Usage:
  python3 auto_explore.py

Requires: Gazebo + slam.launch.py (SLAM + Nav2) running first.
"""

import math
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy

from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from tf2_ros import Buffer, TransformListener


# ── Tunable parameters ────────────────────────────────────────────────────────
MIN_FRONTIER_SIZE   = 20     # minimum cells in a cluster to be considered
GOAL_TIMEOUT        = 30.0   # seconds to wait for each nav goal
MIN_FRONTIER_DIST   = 1.0    # metres — skip frontiers closer than this
BLACKLIST_RADIUS    = 0.4    # metres — don't re-send goal within this radius
BLACKLIST_SIZE      = 20     # how many recent goals to remember
# ─────────────────────────────────────────────────────────────────────────────


class AutoExplore(Node):
    def __init__(self):
        super().__init__('auto_explore')

        # TF for robot pose
        self.tf_buffer   = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Nav2 action client
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Map subscriber (latched/transient)
        map_qos = QoSProfile(depth=1,
                             durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=QoSReliabilityPolicy.RELIABLE)
        self._map_sub = self.create_subscription(
            OccupancyGrid, 'map', self._map_cb, map_qos)

        self._current_map  = None
        self._navigating   = False
        self._done         = False
        self._visited      = []   # blacklist of recent goal positions
        self._home         = None  # recorded on first valid TF
        self._returning    = False

        # Timer: attempt exploration every 3 s when not navigating
        self.create_timer(3.0, self._explore_tick)
        self.get_logger().info('Auto-explore started — waiting for map and Nav2...')

    # ── Map callback ─────────────────────────────────────────────────────────
    def _map_cb(self, msg: OccupancyGrid):
        self._current_map = msg

    # ── Periodic exploration tick ─────────────────────────────────────────────
    def _explore_tick(self):
        if self._navigating or self._current_map is None:
            return

        robot_pos = self._get_robot_pos()
        if robot_pos is None:
            return

        # Record home position on first valid TF
        if self._home is None:
            self._home = robot_pos
            self.get_logger().info(
                f'Home position recorded: ({robot_pos[0]:.2f}, {robot_pos[1]:.2f})')

        if self._done:
            return

        frontier = self._find_best_frontier(self._current_map, robot_pos)

        if frontier is None:
            self.get_logger().info(
                'No frontiers found — exploration complete! Returning home...')
            self._done = True
            self._returning = True
            self._send_goal(self._home[0], self._home[1])
            return

        self.get_logger().info(
            f'Navigating to frontier ({frontier[0]:.2f}, {frontier[1]:.2f})')
        self._send_goal(frontier[0], frontier[1])

    # ── Robot position via TF ─────────────────────────────────────────────────
    def _get_robot_pos(self):
        try:
            tf = self.tf_buffer.lookup_transform(
                'map', 'base_footprint', rclpy.time.Time())
            t = tf.transform.translation
            return (t.x, t.y)
        except Exception:
            return None

    # ── Frontier detection ────────────────────────────────────────────────────
    def _find_best_frontier(self, map_msg: OccupancyGrid, robot_pos):
        info = map_msg.info
        w, h = info.width, info.height
        res  = info.resolution
        ox   = info.origin.position.x
        oy   = info.origin.position.y

        data = np.array(map_msg.data, dtype=np.int16).reshape(h, w)

        # Frontier: FREE cell (0) with at least one UNKNOWN (-1 → 255 as uint8 → stored as -1) neighbour
        free    = (data == 0)
        unknown = (data == -1)

        # Dilate unknown by 1 cell
        unknown_adj = np.zeros_like(unknown)
        unknown_adj[1:,  :] |= unknown[:-1, :]
        unknown_adj[:-1, :] |= unknown[1:,  :]
        unknown_adj[:,  1:] |= unknown[:, :-1]
        unknown_adj[:, :-1] |= unknown[:,  1:]

        frontier_mask = free & unknown_adj

        # Label connected components (simple flood-fill clusters)
        clusters = self._cluster_frontier(frontier_mask)
        if not clusters:
            return None

        # Filter by minimum size
        clusters = [c for c in clusters if len(c) >= MIN_FRONTIER_SIZE]
        if not clusters:
            return None

        # Convert clusters to world coords, filter by distance + blacklist
        rx = int((robot_pos[0] - ox) / res)
        ry = int((robot_pos[1] - oy) / res)

        candidates = []
        for cluster in clusters:
            cy = sum(r for r, c in cluster) / len(cluster)
            cx = sum(c for r, c in cluster) / len(cluster)
            wx = cx * res + ox
            wy = cy * res + oy
            dist_m = math.hypot(wx - robot_pos[0], wy - robot_pos[1])

            # Skip frontiers that are too close to the robot
            if dist_m < MIN_FRONTIER_DIST:
                continue

            # Skip frontiers near recently visited goals
            if any(math.hypot(wx - vx, wy - vy) < BLACKLIST_RADIUS
                   for vx, vy in self._visited):
                continue

            candidates.append((dist_m, len(cluster), wx, wy))

        if not candidates:
            # Relax distance constraint as fallback (map may be nearly complete)
            for cluster in clusters:
                cy = sum(r for r, c in cluster) / len(cluster)
                cx = sum(c for r, c in cluster) / len(cluster)
                wx = cx * res + ox
                wy = cy * res + oy
                dist_m = math.hypot(wx - robot_pos[0], wy - robot_pos[1])
                if any(math.hypot(wx - vx, wy - vy) < BLACKLIST_RADIUS
                       for vx, vy in self._visited):
                    continue
                candidates.append((dist_m, len(cluster), wx, wy))

        if not candidates:
            return None

        # Among candidates: prefer farthest to drive outward into unexplored space
        candidates.sort(key=lambda c: -c[0])
        _, _, best_x, best_y = candidates[0]
        return (best_x, best_y)

    def _cluster_frontier(self, mask):
        """Simple BFS clustering of frontier cells."""
        visited = np.zeros_like(mask, dtype=bool)
        clusters = []
        rows, cols = np.where(mask)
        for r, c in zip(rows.tolist(), cols.tolist()):
            if visited[r, c]:
                continue
            cluster = []
            queue = [(r, c)]
            visited[r, c] = True
            while queue:
                cr, cc = queue.pop()
                cluster.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if (0 <= nr < mask.shape[0] and 0 <= nc < mask.shape[1]
                            and mask[nr, nc] and not visited[nr, nc]):
                        visited[nr, nc] = True
                        queue.append((nr, nc))
            clusters.append(cluster)
        return clusters

    # ── Send Nav2 goal ────────────────────────────────────────────────────────
    def _send_goal(self, x: float, y: float):
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('Nav2 action server not ready')
            return

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.w = 1.0

        self._navigating = True
        self._visited.append((x, y))
        if len(self._visited) > BLACKLIST_SIZE:
            self._visited.pop(0)
        send_future = self._nav_client.send_goal_async(goal)
        send_future.add_done_callback(self._goal_response_cb)

    def _goal_response_cb(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn('Goal rejected by Nav2')
            self._navigating = False
            return
        handle.get_result_async().add_done_callback(self._goal_result_cb)

    def _goal_result_cb(self, future):
        self._navigating = False
        status = future.result().status
        if self._returning:
            if status == 4:
                self.get_logger().info('Returned home. All done.')
            else:
                self.get_logger().warn('Could not return home (status %d).' % status)
            return
        if status == 4:  # SUCCEEDED
            self.get_logger().info('Frontier reached.')
        else:
            self.get_logger().warn(f'Goal finished with status {status} — trying next frontier')


def main():
    rclpy.init()
    node = AutoExplore()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Exploration stopped.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
