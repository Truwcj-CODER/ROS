#!/usr/bin/env python3
"""
Waypoint patrol — loops through a fixed list of poses via Nav2 NavigateToPose.

Usage:
  python3 patrol.py

Requires: slam.launch.py (sim:=true) running first.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from tf2_ros import Buffer, TransformListener

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped


# ── Patrol waypoints (world coords, yaw=0) ────────────────────────────────────
WAYPOINTS = [
    ( 2.0,  2.0),   # NE corner
    ( 2.0, -2.0),   # SE corner
    (-2.0, -2.0),   # SW corner
    (-2.0,  2.0),   # NW corner
]
# ─────────────────────────────────────────────────────────────────────────────


class Patrol(Node):
    def __init__(self):
        super().__init__('patrol')
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.tf_buffer   = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self._wp_index   = 0
        self._navigating = False
        self._map_ready  = False

        self.create_timer(2.0, self._patrol_tick)
        self.get_logger().info(
            f'Patrol started — {len(WAYPOINTS)} waypoints, looping forever.')

    def _patrol_tick(self):
        if self._navigating:
            return

        # Wait until slam_toolbox publishes the map→base_footprint TF
        if not self._map_ready:
            try:
                self.tf_buffer.lookup_transform(
                    'map', 'base_footprint', rclpy.time.Time())
                self._map_ready = True
                self.get_logger().info('Map ready — starting patrol!')
            except Exception:
                self.get_logger().info(
                    'Waiting for map frame...', throttle_duration_sec=3.0)
                return

        wp = WAYPOINTS[self._wp_index]
        self.get_logger().info(
            f'[{self._wp_index + 1}/{len(WAYPOINTS)}] Heading to ({wp[0]}, {wp[1]})')
        self._send_goal(wp[0], wp[1])

    def _send_goal(self, x: float, y: float):
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('Nav2 action server not ready — retrying...')
            return

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.w = 1.0

        self._navigating = True
        future = self._nav_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_cb)

    def _goal_response_cb(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn('Goal rejected — skipping waypoint')
            self._advance()
            return
        handle.get_result_async().add_done_callback(self._goal_result_cb)

    def _goal_result_cb(self, future):
        status = future.result().status
        wp = WAYPOINTS[self._wp_index]
        if status == 4:  # SUCCEEDED
            self.get_logger().info(f'Reached ({wp[0]}, {wp[1]})')
        else:
            self.get_logger().warn(
                f'Goal to ({wp[0]}, {wp[1]}) ended with status {status}')
        self._advance()

    def _advance(self):
        self._wp_index = (self._wp_index + 1) % len(WAYPOINTS)
        self._navigating = False


def main():
    rclpy.init()
    node = Patrol()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Patrol stopped.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
