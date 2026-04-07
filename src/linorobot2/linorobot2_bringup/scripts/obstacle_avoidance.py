#!/usr/bin/env python3
"""
Reactive obstacle avoidance demo.
Reads /scan (LaserScan), drives forward when path is clear,
turns in place when an obstacle is detected within safe_distance.

Usage:
  python3 obstacle_avoidance.py

Requires bringup.launch.py to be running first.
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


FORWARD_SPEED  = 0.15   # m/s   — linear speed when path is clear
TURN_SPEED     = 0.5    # rad/s — rotation speed when obstacle detected
SAFE_DISTANCE  = 0.5    # m     — stop-and-turn threshold
FRONT_ANGLE    = 30.0   # deg   — half-width of the front sector to check


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.sub = self.create_subscription(LaserScan, 'scan', self._scan_cb, 10)
        self.get_logger().info(
            f'Obstacle avoidance started — '
            f'safe_distance={SAFE_DISTANCE}m, front_angle=±{FRONT_ANGLE}°'
        )

    def _scan_cb(self, msg: LaserScan):
        # Number of readings covering FRONT_ANGLE degrees on each side
        angle_increment = msg.angle_increment          # radians per index
        half_front_rad  = math.radians(FRONT_ANGLE)
        half_n          = max(1, int(half_front_rad / angle_increment))

        n = len(msg.ranges)
        # Indices wrapping around index 0 (front of robot)
        indices = [(i % n) for i in range(-half_n, half_n + 1)]

        front_ranges = [
            msg.ranges[i]
            for i in indices
            if msg.range_min < msg.ranges[i] < msg.range_max
        ]

        cmd = Twist()
        if front_ranges and min(front_ranges) < SAFE_DISTANCE:
            # Obstacle ahead — turn in place (left)
            cmd.angular.z = TURN_SPEED
            self.get_logger().info(
                f'Obstacle at {min(front_ranges):.2f}m — turning', throttle_duration_sec=1.0
            )
        else:
            # Path clear — go forward
            cmd.linear.x = FORWARD_SPEED

        self.pub.publish(cmd)


def main():
    rclpy.init()
    node = ObstacleAvoidance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Send stop command before exiting
        stop = Twist()
        node.pub.publish(stop)
        node.get_logger().info('Stopped.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
