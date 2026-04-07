import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/trucnv/Documents/robot_dev/linorobot2_ws/install/linorobot2_gazebo'
