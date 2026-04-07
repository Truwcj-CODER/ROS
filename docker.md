# Compose image :
```bash
(sudo) docker compose up -d
(sudo) docker compose down
```

# Executive image :
```bash
(sudo) docker exec -it linorobot2_ws bash
```

# Install linorobot2 :
* LƯU Ý : Chỉ cài 1 lần khi vào Docker (30/3/2026 : Đã cài)

```bash
cd /tmp
wget https://github.com/hippo5329/linorobot2/raw/jazzy/install_linorobot2.bash
bash install_linorobot2.bash 2wd a2
source ~/.bashrc
```
# Permission denied :
```bash
sudo chown -R $USER:$USER ~/linorobot2_ws
```

# Colcon build :
```bash
colcon build --packages-select micro_ros_msgs drive_base_msgs
colcon build --symlink-install --packages-skip micro_ros_msgs drive_base_msgs
```

# Kill process :
```bash
pkill -9 -f "ros|sllidar|micro_ros"
```

# ROS2 Command :
```bash
# Bring up (SBC)
ros2 launch linorobot2_bringup bringup.launch.py

# Teleop key (Host)
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
