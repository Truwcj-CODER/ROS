FROM ros:humble-ros-base

RUN apt-get update && apt-get install -y \
    wget \
    git \
    sudo \
    nano \
    udev \
    python3-pip

WORKDIR /root/linorobot2_ws

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "alias killros='pkill -9 -f \"ros|sllidar|micro_ros|launch\"'" >> /root/.bashrc

CMD ["/bin/bash"]