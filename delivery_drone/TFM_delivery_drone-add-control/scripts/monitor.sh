#!/bin/bash
# Script de monitoreo avanzado

while true; do
    clear
    echo "======================================"
    echo "📊 MONITOR DE DRON - $(date)"
    echo "======================================"
    
    # Verificar procesos
    echo -n "DDS Agent: "
    pgrep -f MicroXRCEAgent > /dev/null && echo "✅ Activo" || echo "❌ Inactivo"
    
    echo -n "PX4: "
    pgrep -f px4 > /dev/null && echo "✅ Activo" || echo "❌ Inactivo"
    
    echo -n "Contenedor ROS 2: "
    docker ps | grep -q drone_container && echo "✅ Activo" || echo "❌ Inactivo"
    
    echo ""
    echo "📈 Posición actual:"
    docker exec drone_container bash -c "source /ros2_ws/install/setup.bash && \
        ros2 topic echo /fmu/out/vehicle_local_position_v1 --once 2>/dev/null" | \
        grep -E "x:|y:|z:|vx:|vy:|vz:" | head -6
    
    echo ""
    echo "🔧 Estado:"
    docker exec drone_container bash -c "source /ros2_ws/install/setup.bash && \
        ros2 topic echo /fmu/out/vehicle_status_v2 --once 2>/dev/null" | \
        grep -E "arming_state|nav_state" | head -2
    
    sleep 2
done
