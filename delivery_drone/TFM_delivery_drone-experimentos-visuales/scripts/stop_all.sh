#!/bin/bash
# Script para detener todo el sistema

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}🛑 Deteniendo sistema de simulación...${NC}"

# Detener sesiones tmux
if tmux has-session -t drone_sim 2>/dev/null; then
    tmux kill-session -t drone_sim
    echo -e "${GREEN}✅ Sesión tmux terminada${NC}"
fi

# Buscar y matar procesos
pkill -f MicroXRCEAgent 2>/dev/null && echo -e "${GREEN}✅ DDS Agent detenido${NC}"
pkill -f px4 2>/dev/null && echo -e "${GREEN}✅ PX4 detenido${NC}"
pkill -f gz 2>/dev/null && echo -e "${GREEN}✅ Gazebo detenido${NC}"

# Detener contenedor (opcional)
read -p "¿Detener contenedor Docker? (s/n): " stop_docker
if [[ "$stop_docker" == "s" ]]; then
    docker stop drone_container
    echo -e "${GREEN}✅ Contenedor detenido${NC}"
fi

echo -e "${GREEN}✅ Sistema detenido${NC}"
