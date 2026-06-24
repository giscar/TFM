#!/bin/bash
# Script para iniciar automáticamente el sistema de simulación de dron
# Versión: con supresión de errores RTPS_READER_HISTORY

# --- Suprimir logs molestos de Fast-RTPS ---
export FASTRTPS_DEFAULT_PROFILES_FILE=/dev/null
export RTPS_LOG_LEVEL=3

# --- Configuración de tmux (directorio alternativo) ---
export TMPDIR=~/tmux-sockets
export TMUX_TMPDIR="$TMPDIR"
mkdir -p "$TMPDIR"
if [ ! -w "$TMPDIR" ]; then
    echo "ERROR: $TMPDIR no es escribible. Saliendo."
    exit 1
fi

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚁 SISTEMA DE SIMULACIÓN DE DRON${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

# Verificar contenedor
if ! docker ps -a | grep -q drone_container; then
    echo -e "${YELLOW}⚠️ Creando contenedor drone_container...${NC}"
    docker run -itd --name drone_container --restart always --network host drone_ros2_jazzy
fi

if ! docker ps | grep -q drone_container; then
    echo -e "${YELLOW}⚠️ Iniciando contenedor...${NC}"
    docker start drone_container
fi

echo -e "${GREEN}✅ Contenedor Docker listo${NC}"
echo ""

# Limpieza de sesiones y procesos previos
echo -e "${CYAN}Configurando sesión tmux...${NC}"
echo -e "${YELLOW}🧹 Limpiando sesiones y procesos anteriores...${NC}"
tmux kill-server 2>/dev/null
sudo pkill -f MicroXRCEAgent 2>/dev/null
sudo pkill -f px4 2>/dev/null
sudo pkill -f gz 2>/dev/null
sudo pkill -f rosbridge 2>/dev/null
sudo pkill -f tf_publisher 2>/dev/null
sleep 2
echo -e "${GREEN}✅ Limpieza completada${NC}"

# Crear ventanas tmux
echo -e "${CYAN}Creando ventanas tmux...${NC}"

# Ventana 0: DDS Agent (con buffers ampliados)
tmux new-session -d -s drone_sim -n "DDS Agent"
tmux send-keys -t drone_sim:0 "cd ~/drone_project/Micro-XRCE-DDS-Agent/build && ./MicroXRCEAgent udp4 -p 8888" C-m
sleep 1

# Ventana 1: PX4
tmux new-window -t drone_sim -n "PX4"
tmux send-keys -t drone_sim:1 "cd ~/drone_project/px4/PX4-Autopilot && HEADLESS=1 make px4_sitl gz_x500" C-m
sleep 2

# Ventana 2: ROS2 Control
tmux new-window -t drone_sim -n "ROS2"
tmux send-keys -t drone_sim:2 "docker exec -it drone_container bash -c 'cd /ros2_ws && source install/setup.bash && echo \"✅ ROS 2 listo\" && exec bash'" C-m
sleep 1

# Ventana 3: Monitor
tmux new-window -t drone_sim -n "Monitor"
tmux send-keys -t drone_sim:3 "docker exec -it drone_container bash -c 'cd /ros2_ws && source install/setup.bash && echo \"📊 Monitoreando posición z...\" && ros2 topic echo /fmu/out/vehicle_local_position_v1 | grep -E \"x:|y:|z:\"'" C-m
sleep 1

# Ventana 4: Rosbridge Server (puerto 9090)
echo -e "${PURPLE}📡 Creando Rosbridge (puerto 9090)...${NC}"
tmux new-window -t drone_sim -n "Rosbridge"
tmux send-keys -t drone_sim:Rosbridge "docker exec -it drone_container bash -c 'source /opt/ros/jazzy/setup.bash && source /ros2_ws/install/setup.bash && ros2 launch rosbridge_server rosbridge_websocket_launch.xml'" C-m
sleep 2

# Ventana 5: TF Publisher
echo -e "${CYAN}🧭 Creando TF Publisher (transformaciones para 3D)...${NC}"
tmux new-window -t drone_sim -n "TF"
tmux send-keys -t drone_sim:TF "docker exec -it drone_container bash -c 'cd /ros2_ws && source install/setup.bash && python3 /ros2_ws/src/tf_publisher.py'" C-m
sleep 1

# Verificación
WINDOW_COUNT=$(tmux list-windows -t drone_sim | wc -l)
echo -e "${GREEN}✅ $WINDOW_COUNT ventanas creadas${NC}"
echo ""
echo -e "${GREEN}📊 DISTRIBUCIÓN DE VENTANAS:${NC}"
echo "  0: DDS Agent    - Comunicación PX4 ↔ ROS 2 (puerto 8888)"
echo "  1: PX4          - Simulación del dron (Gazebo)"
echo "  2: ROS2         - Nodo de control (offboard_control) y misión"
echo "  3: Monitor      - Monitoreo local (posición z)"
echo "  4: Rosbridge    - Servidor WebSocket (puerto 9090) para Foxglove"
echo "  5: TF           - Publica transformaciones map → base_link para 3D"
echo ""
echo -e "${GREEN}📌 Para visualizar en Foxglove Desktop:${NC}"
echo "   1. Abre Foxglove Desktop"
echo "   2. Conexión → Rosbridge → ws://130.61.118.51:9090"
echo "   3. En panel 3D: carga el URDF (ej. x500.urdf) y configura fixed frame = map"
echo "   4. Activa la transformación map → base_link en la lista de Transforms"
echo ""
echo -e "${YELLOW}Comandos tmux:${NC}"
echo "  - Navegar: Ctrl+b n (siguiente) / Ctrl+b p (anterior)"
echo "  - Ir a ventana: Ctrl+b <número> (ej: Ctrl+b 5 para TF)"
echo "  - Lista: Ctrl+b w"
echo "  - Salir sin cerrar: Ctrl+b d"
echo ""

tmux attach -t drone_sim
