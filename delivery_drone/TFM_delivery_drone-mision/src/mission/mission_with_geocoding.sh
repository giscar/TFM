#!/bin/bash
# Misión con geocodificación y control OFFBOARD continuo (versión robusta)

if [ -z "$1" ]; then
    echo "Uso: $0 \"dirección\""
    exit 1
fi

ADDRESS="$1"

echo "========================================="
echo "🚁 MISIÓN CON GEOCODIFICACIÓN"
echo "========================================="
echo "Dirección: $ADDRESS"
echo ""

# Coordenadas de origen (Malta, Valletta Ferry Terminal)
REF_LAT="35.9000"
REF_LON="14.5200"
echo "📌 Origen (referencia): lat=$REF_LAT, lon=$REF_LON"

# Función para esperar con cuenta regresiva (ahora también mantiene setpoint)
wait_with_setpoint() {
    local seconds=$1
    local message=$2
    local x=$3
    local y=$4
    local z=$5
    echo -n "$message "
    # Lanzar publicador continuo del setpoint en segundo plano
    ros2 topic pub --rate 20 /fmu/in/trajectory_setpoint px4_msgs/msg/TrajectorySetpoint "{position: [$x, $y, $z], yaw: 0.0}" > /dev/null 2>&1 &
    local pub_pid=$!
    # Mostrar cuenta regresiva
    for i in $(seq $seconds -1 1); do
        echo -n "$i... "
        sleep 1
    done
    echo "¡YA!"
    # Detener el publicador
    kill $pub_pid 2>/dev/null
    wait $pub_pid 2>/dev/null
    echo ""
}

# --- Lanzar publicador continuo de modo OFFBOARD (20 Hz) en segundo plano ---
echo "🔄 Iniciando publicador de modo OFFBOARD..."
ros2 topic pub --rate 20 /fmu/in/offboard_control_mode px4_msgs/msg/OffboardControlMode "{position: true}" > /dev/null 2>&1 &
OFFBOARD_PID=$!
sleep 2
echo "✅ Publicador de modo OFFBOARD corriendo (PID $OFFBOARD_PID)"

# --- Geocodificar dirección ---
echo "🌍 Geocodificando dirección..."
TEMP_PY=$(mktemp)
cat > $TEMP_PY << 'PYEOF'
import sys
sys.path.append('/ros2_ws/src/geo')
from mapbox_geocoder import MapboxGeocoder
from coordinates import latlon_to_local
import os

def main():
    if len(sys.argv) < 4:
        print("ERROR: Faltan argumentos")
        sys.exit(1)
    address = sys.argv[1]
    ref_lat = float(sys.argv[2])
    ref_lon = float(sys.argv[3])
    token = os.environ.get("MAPBOX_TOKEN")
    if not token:
        print("ERROR: MAPBOX_TOKEN no definida")
        sys.exit(1)
    geocoder = MapboxGeocoder(token)
    coords = geocoder.geocode(address)
    if not coords:
        print("ERROR: No se pudo geocodificar la dirección")
        sys.exit(1)
    lat, lon = coords
    print(f"Coordenadas geográficas: lat={lat:.6f}, lon={lon:.6f}")
    x, y = latlon_to_local(lat, lon, ref_lat, ref_lon)
    print(f"{x},{y}")

if __name__ == "__main__":
    main()
PYEOF

WAYPOINT=$(python3 $TEMP_PY "$ADDRESS" "$REF_LAT" "$REF_LON")
rm $TEMP_PY

if [[ $WAYPOINT == ERROR* ]]; then
    echo "❌ $WAYPOINT"
    kill $OFFBOARD_PID 2>/dev/null
    exit 1
fi

echo "$WAYPOINT" | head -1   # coordenadas geográficas
X=$(echo "$WAYPOINT" | tail -1 | cut -d',' -f1)
Y=$(echo "$WAYPOINT" | tail -1 | cut -d',' -f2)
echo "📍 Waypoint local: x=$X, y=$Y"
echo ""

# --- Secuencia de vuelo con setpoints continuos ---
echo "🚀 INICIANDO SECUENCIA DE VUELO"

# 1. Despegue (setpoint continuo durante 5 segundos)
echo "1️⃣ Despegando..."
wait_with_setpoint 5 "  Ascendiendo" 0.0 0.0 -2.5

# Verificar altura
current_z=$(ros2 topic echo /fmu/out/vehicle_local_position_v1 --once 2>/dev/null | grep "z:" | head -1 | awk '{print $2}')
if [[ -z "$current_z" || $(echo "$current_z > -0.2" | bc -l) -eq 1 ]]; then
    echo "⚠️  Despegue automático fallido. Forzando armado y despegue..."
    ros2 topic pub --once /fmu/in/vehicle_command px4_msgs/msg/VehicleCommand "{command: 400, param1: 1.0, target_system: 1, target_component: 1, source_system: 1, source_component: 1, from_external: true}" > /dev/null
    sleep 2
    ros2 topic pub --once /fmu/in/vehicle_command px4_msgs/msg/VehicleCommand "{command: 22, param7: 2.5, target_system: 1, target_component: 1, source_system: 1, source_component: 1, from_external: true}" > /dev/null
    # Esperar con setpoint continuo
    wait_with_setpoint 5 "  Esperando después del forzado" 0.0 0.0 -2.5
else
    echo "✅ Despegue detectado (altura = $current_z)"
fi

# 2. Volar al waypoint (setpoint continuo durante 10 segundos)
echo "2️⃣ Volando hacia ($X, $Y)..."
wait_with_setpoint 10 "  Avanzando" $X $Y -2.5

# 3. Regresar al origen (setpoint continuo)
echo "3️⃣ Regresando al origen..."
wait_with_setpoint 10 "  Regresando" 0.0 0.0 -2.5

# 4. Aterrizar (setpoint continuo)
echo "4️⃣ Aterrizando..."
wait_with_setpoint 5 "  Descendiendo" 0.0 0.0 0.0

# --- Detener publicador de modo OFFBOARD ---
echo "🛑 Deteniendo publicador de modo OFFBOARD..."
kill $OFFBOARD_PID 2>/dev/null
wait $OFFBOARD_PID 2>/dev/null

echo ""
echo "========================================="
echo "✅ MISIÓN COMPLETADA"
echo "========================================="
