# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hardware Setup

- **Robot base:** 2WD differential drive
- **Microcontroller:** Raspberry Pi Pico → `/dev/ttyACM0` @ 921600 baud (micro-ROS)
- **Lidar:** RPLIDAR A2M8 → `/dev/ttyUSB0` @ 115200 baud
- **Compute:** Jetson Xavier NX (JetPack 5.x, Ubuntu 20.04) on robot; Ubuntu 22.04 ROS2 Humble on dev machine

Firmware for the Pico lives in a separate repo: https://github.com/linorobot/linorobot2_hardware

## Environment Variables

These must be exported before any `ros2 launch` command (add to `~/.bashrc`):

```bash
export LINOROBOT2_BASE=2wd                  # required: 2wd | 4wd | mecanum
export LINOROBOT2_LASER_SENSOR=a2           # optional: a1|a2|a3|s1|s2|s3|c1|ydlidar|ld06|ld19|stl27l|xv11|ldlidar
export LINOROBOT2_DEPTH_SENSOR=             # optional: realsense|zed|zed2|oakd|oakdlite|oakdpro
```

`sensors.launch.py` reads these at runtime — changing them does not require a rebuild.

## Build

Build order matters: `micro_ros_msgs` and `drive_base_msgs` must be built first.

```bash
source /opt/ros/humble/setup.bash
cd ~/Documents/linorobot2_ws

# First build (or after pulling micro_ros changes)
colcon build --packages-select micro_ros_msgs drive_base_msgs
colcon build --symlink-install --packages-skip micro_ros_msgs drive_base_msgs

source install/setup.bash
```

For subsequent builds after source changes: `colcon build --symlink-install` is sufficient.

## Run Commands

**Terminal 1 — Robot bringup (always first):**
```bash
ros2 launch linorobot2_bringup bringup.launch.py
```
Wait for micro-ROS to print `session established` before proceeding.

**Terminal 2 — SLAM mapping:**
```bash
ros2 launch linorobot2_navigation slam.launch.py rviz:=true
```

**Terminal 3 — Teleoperate to build map:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Save map:**
```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map
# saves ~/my_map.pgm + ~/my_map.yaml
```

**Navigation + obstacle avoidance (after map is saved):**
```bash
ros2 launch linorobot2_navigation navigation.launch.py map:=$HOME/my_map.yaml
```

**Simulation (no hardware needed):**
```bash
ros2 launch linorobot2_gazebo gazebo.launch.py
ros2 launch linorobot2_navigation slam.launch.py sim:=true rviz:=true
ros2 launch linorobot2_navigation navigation.launch.py map:=<path>.yaml sim:=true
```

**Override serial port or use UDP transport:**
```bash
ros2 launch linorobot2_bringup bringup.launch.py \
  base_serial_port:=/dev/ttyUSB1 \
  micro_ros_baudrate:=921600

# or UDP
ros2 launch linorobot2_bringup bringup.launch.py \
  micro_ros_transport:=udp4 \
  micro_ros_port:=8888
```

## Docker

The simple `Dockerfile` at workspace root uses `ros:humble-ros-base` (multi-arch: works on x86 and Jetson ARM64 without changes).

```bash
docker compose build          # build image (run on each machine separately)
docker compose up -d          # start container
docker exec -it linorobot2_ws bash
docker compose down
```

If deploying to a different user's machine, update the volume path in `docker-compose.yml`:
```yaml
volumes:
  - /home/<username>/Documents/linorobot2_ws:/root/linorobot2_ws
```

## Architecture

### Launch Hierarchy

```
bringup.launch.py
├── EKF node (robot_localization) — fuses odom/unfiltered + imu/data → /odom at 50 Hz
├── Madgwick filter (opt, madgwick:=true)
├── default_robot.launch.py
│   ├── micro_ros_agent (serial /dev/ttyACM0 or UDP)
│   ├── description.launch.py (robot_state_publisher, joint_state_publisher)
│   └── sensors.launch.py
│       ├── lasers.launch.py (driven by LINOROBOT2_LASER_SENSOR)
│       └── depth.launch.py  (driven by LINOROBOT2_DEPTH_SENSOR)
└── joy_teleop.launch.py (opt, joy:=true)
```

### TF Tree

```
map → odom → base_footprint → base_link → laser   (publishes /scan)
                                         → imu_link
                                         → depth_camera_link
```

- `laser` frame offset from `base_link`: `xyz="0.12 0 0.33"` (12 cm forward, 33 cm up)
- `odom` is published by EKF, not directly by micro-ROS

### Topics Published by Pico Firmware

| Topic | Type | Description |
|---|---|---|
| `odom/unfiltered` | nav_msgs/Odometry | Raw wheel odometry |
| `/imu/data` | sensor_msgs/Imu | Filtered IMU (for EKF) |
| `/imu/data_raw` | sensor_msgs/Imu | Raw IMU |
| `/imu/mag` | sensor_msgs/MagneticField | Magnetometer |

### Key Config Files

| File | Purpose |
|---|---|
| `linorobot2_base/config/ekf.yaml` | EKF sensor fusion (50 Hz, 2D mode) |
| `linorobot2_navigation/config/navigation.yaml` | Nav2: AMCL, costmaps, RegulatedPurePursuit controller |
| `linorobot2_navigation/config/slam.yaml` | slam_toolbox: Ceres solver, 0.05m resolution |
| `linorobot2_bringup/config/fake_laser.yaml` | depthimage_to_laserscan params |
| `linorobot2_description/urdf/robots/2wd.urdf.xacro` | Robot URDF (wheel geometry, joints) |

### Navigation Stack

- **SLAM:** slam_toolbox (online async, CeresSolver)
- **Localization:** AMCL (likelihood_field laser model, 500–2000 particles)
- **Controller:** RegulatedPurePursuitController + RotationShimController (0.4 m/s, lookahead 0.3–0.9 m)
- **Planner:** NavfnPlanner (Dijkstra, 0.5 m tolerance)
- **Costmaps:** local 3×3 m rolling window (voxel_layer + inflation 0.7 m), global static+obstacle+inflation
