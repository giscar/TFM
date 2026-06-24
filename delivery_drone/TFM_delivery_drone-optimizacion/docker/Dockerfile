# Usamos la imagen oficial de ROS 2 Jazzy
FROM osrf/ros:jazzy-desktop

# Instalamos herramientas básicas de desarrollo
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configuramos el entrypoint para que cargue el entorno automáticamente
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

WORKDIR /ros2_ws
