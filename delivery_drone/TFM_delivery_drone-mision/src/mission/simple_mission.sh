#!/bin/bash
echo "==================================="
echo "🚁 MISIÓN DE VUELO AUTÓNOMO"
echo "==================================="
echo ""

check_position() {
    echo "📍 Posición actual:"
    ros2 topic echo /fmu/out/vehicle_local_position_v1 --once 2>/dev/null | grep -E "x:|y:|z:" | head -3
    echo ""
}

wait_countdown() {
    local seconds=$1
    local message=$2
    echo -n "$message "
    for i in $(seq $seconds -1 1); do
        echo -n "$i... "
        sleep 1
    done
    echo "¡YA!"
    echo ""
}

force_takeoff() {
    echo "⚠️  Despegue automático fallido. Forzando armado y despegue..."
    ros2 topic pub --once /fmu/in/vehicle_command px4_msgs/msg/VehicleCommand "{command: 400, param1: 1.0, target_system: 1, target_component: 1, source_system: 1, source_component: 1, from_external: true}" > /dev/null
    sleep 2
    ros2 topic pub --once /fmu/in/vehicle_command px4_msgs/msg/VehicleCommand "{command: 22, param7: 2.5, target_system: 1, target_component: 1, source_system: 1, source_component: 1, from_external: true}" > /dev/null
    echo "✅ Comandos de armado y despegue enviados."
}

echo "📋 PLAN DE VUELO:"
echo "  1. Despegar a 2.5 metros"
echo "  2. Esperar 5 segundos"
echo "  3. Moverse 5 metros adelante (X positivo)"
echo "  4. Esperar 5 segundos"
echo "  5. Regresar al origen"
echo "  6. Aterrizar"
echo ""

read -p "¿Comenzar misión? (s/n): " confirm
if [[ "$confirm" != "s" ]]; then
    echo "Misión cancelada"
    exit 0
fi

echo ""
echo "🚀 INICIANDO MISIÓN"
echo ""

# 1. Despegue
echo "1️⃣ Despegando a 2.5 metros..."
ros2 topic pub --once /fmu/in/trajectory_setpoint px4_msgs/msg/TrajectorySetpoint "{position: [0.0, 0.0, -2.5], yaw: 0.0}" > /dev/null
wait_countdown 5 "  Ascendiendo..."

current_z=$(ros2 topic echo /fmu/out/vehicle_local_position_v1 --once 2>/dev/null | grep "z:" | head -1 | awk '{print $2}')
if [[ -z "$current_z" ]]; then
    echo "❌ No se pudo leer la posición. Forzando despegue..."
    force_takeoff
    wait_countdown 5 "  Esperando después del forzado..."
elif (( $(echo "$current_z > -0.2" | bc -l) )); then
    echo "⚠️  Altura actual ($current_z) menor de 20 cm. Forzando despegue..."
    force_takeoff
    wait_countdown 5 "  Esperando después del forzado..."
else
    echo "✅ Despegue detectado (altura = $current_z)"
fi

check_position

# 2. Moverse adelante
echo "2️⃣ Moviendo 5 metros adelante..."
ros2 topic pub --once /fmu/in/trajectory_setpoint px4_msgs/msg/TrajectorySetpoint "{position: [5.0, 0.0, -2.5], yaw: 0.0}" > /dev/null
wait_countdown 5 "  Avanzando..."
check_position

# 3. Regresar
echo "3️⃣ Regresando al origen..."
ros2 topic pub --once /fmu/in/trajectory_setpoint px4_msgs/msg/TrajectorySetpoint "{position: [0.0, 0.0, -2.5], yaw: 0.0}" > /dev/null
wait_countdown 5 "  Regresando..."
check_position

# 4. Aterrizar
echo "4️⃣ Aterrizando..."
ros2 topic pub --once /fmu/in/trajectory_setpoint px4_msgs/msg/TrajectorySetpoint "{position: [0.0, 0.0, 0.0], yaw: 0.0}" > /dev/null
wait_countdown 5 "  Descendiendo..."

sleep 2
check_position

echo ""
echo "==================================="
echo "✅ MISIÓN COMPLETADA"
echo "==================================="
